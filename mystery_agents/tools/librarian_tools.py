"""Librarian エージェント向け LLM ツール関数。

低レベル API ツールをラップし、LLM が使用する文字列ベースの
インターフェースを提供する。
"""

import concurrent.futures
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

from google.adk.tools.tool_context import ToolContext

logger = logging.getLogger(__name__)

from ..schemas.document import ArchiveDocument
from .bilingual_search import KEYWORD_PAIRS, expand_keywords_bilingual
from .chronicling_america import search_chronicling_america
from .link_validator import ValidationSummary, validate_documents
from .source_registry import get_all_sources, get_source

# 並列実行の最大ワーカー数
_MAX_WORKERS = 6

# 全ソース合計のドキュメント上限
_TOTAL_DOCS_CAP = 30


def search_newspapers(
    keywords: str,
    date_start: str = "1800",
    date_end: str = "1899",
    states: Optional[str] = None,
    max_results: int = 20,
    min_results: int = 3,
    tool_context: Optional[ToolContext] = None,
) -> str:
    """Search historical newspapers in Chronicling America with automatic fallback.

    Searches the Library of Congress Chronicling America database for
    18th-19th century newspaper articles. Automatically expands keywords
    to include both English and Spanish variants.

    If fewer than min_results documents are found, automatically applies
    progressive fallback strategies: individual keyword search, geographic
    expansion (all US states), and date range expansion (+/-10 years).

    Args:
        keywords: Comma-separated list of search keywords related to historical mysteries
        date_start: Start year (default: 1800)
        date_end: End year (default: 1899)
        states: Comma-separated US states to search (default: East Coast states)
        max_results: Maximum number of results to return (default: 20)
        min_results: Minimum documents before stopping fallback (default: 3)

    Returns:
        JSON string containing search results with documents matching the query
    """
    # キーワードパース
    keyword_list = [kw.strip() for kw in keywords.split(",") if kw.strip()]

    # バイリンガル展開
    expanded = expand_keywords_bilingual(keyword_list)
    en_keywords = expanded["en"]
    es_keywords = expanded["es"]

    # 州パース
    state_list = None
    if states:
        state_list = [s.strip() for s in states.split(",") if s.strip()]

    all_docs = []
    total_hits = 0
    seen_urls: set[str] = set()
    all_keywords_used = en_keywords + es_keywords
    error = None
    levels_used: list[str] = []

    def _search_and_collect(kw_list, *, search_states=state_list, start=date_start, end=date_end):
        nonlocal total_hits, error
        if not kw_list:
            return
        try:
            results = search_chronicling_america(
                keywords=kw_list,
                date_start=start,
                date_end=end,
                states=search_states,
                rows=max_results,
            )
            total_hits += results["total_hits"]
            if results.get("error"):
                error = results["error"]
            for doc in results.get("documents", []):
                if doc.source_url not in seen_urls:
                    seen_urls.add(doc.source_url)
                    all_docs.append(doc)
        except Exception as e:
            error = str(e)

    # Level 1: バイリンガルキーワード一括検索
    levels_used.append("L1_bilingual_combined")
    for kw_list in [en_keywords, es_keywords]:
        _search_and_collect(kw_list)

    # Level 2: 個別キーワード検索（結果不足時）
    if len(all_docs) < min_results and len(en_keywords) > 1:
        logger.info(
            "Chronicling America フォールバック L2 発動: L1結果=%d件 < min=%d",
            len(all_docs), min_results,
            extra={"search_level": "L2", "l1_count": len(all_docs)},
        )
        levels_used.append("L2_individual_keywords")
        for kw in en_keywords:
            _search_and_collect([kw])
            if len(all_docs) >= min_results:
                break
        if len(all_docs) < min_results:
            for kw in es_keywords:
                _search_and_collect([kw])
                if len(all_docs) >= min_results:
                    break

    # Level 3: 地理制限解除（全州検索）
    if len(all_docs) < min_results and state_list is not None:
        logger.info(
            "Chronicling America フォールバック L3 発動: 結果=%d件, 地理制限解除",
            len(all_docs),
            extra={"search_level": "L3", "current_count": len(all_docs)},
        )
        levels_used.append("L3_all_states")
        for kw_list in [en_keywords, es_keywords]:
            _search_and_collect(kw_list, search_states=None)
            if len(all_docs) >= min_results:
                break

    # Level 4: 日付範囲拡大（±10年）
    if len(all_docs) < min_results:
        expanded_start = str(max(1700, int(date_start) - 10))
        expanded_end = str(min(1920, int(date_end) + 10))
        if expanded_start != date_start or expanded_end != date_end:
            logger.info(
                "Chronicling America フォールバック L4 発動: 日付範囲拡大 %s-%s",
                expanded_start, expanded_end,
                extra={"search_level": "L4", "current_count": len(all_docs)},
            )
            levels_used.append(f"L4_date_expanded_{expanded_start}_{expanded_end}")
            for kw_list in [en_keywords, es_keywords]:
                _search_and_collect(kw_list, search_states=None, start=expanded_start, end=expanded_end)
                if len(all_docs) >= min_results:
                    break

    # リンク品質検証（失敗時は検証スキップで全ドキュメント保持）
    try:
        validation = validate_documents(all_docs)
        all_docs = validation.verified_documents
    except Exception:
        validation = ValidationSummary(
            total_checked=0, reachable=0, unreachable=0,
            domain_mismatch=0, removed_urls=[], duration_ms=0,
            verified_documents=list(all_docs),
        )
    logger.info(
        "Chronicling America 検索完了: %d 件 (検証後), levels=%s, リンク検証=%d/%d",
        len(all_docs), levels_used, validation.reachable, validation.total_checked,
        extra={
            "api_name": "chronicling_america", "result_count": len(all_docs),
            "search_levels": levels_used,
            "links_verified": validation.reachable,
            "links_checked": validation.total_checked,
        },
    )

    docs = [doc.model_dump() for doc in all_docs]

    result = {
        "source": "chronicling_america",
        "keywords_used": all_keywords_used,
        "total_hits": total_hits,
        "documents_returned": len(docs),
        "documents": docs,
        "error": error,
        "search_levels_used": levels_used,
        "link_validation": {
            "total_checked": validation.total_checked,
            "reachable": validation.reachable,
            "unreachable": validation.unreachable,
            "removed_count": len(validation.removed_urls),
            "removed_urls": validation.removed_urls,
            "duration_ms": validation.duration_ms,
        },
    }

    # セッション状態に保存
    if tool_context is not None:
        existing = tool_context.state.get("raw_search_results", [])
        existing.append(result)
        tool_context.state["raw_search_results"] = existing

    return json.dumps(result, ensure_ascii=False, indent=2)


def save_search_results(
    theme: str,
    results_json: str,
    filename: Optional[str] = None,
) -> str:
    """Save search results to the data directory.

    Saves the collected search results to a JSON file in the data/ directory
    for later processing by the Scholar Agent.

    Args:
        theme: The original search theme (e.g., "Spanish ship disappearance in Boston Harbor")
        results_json: JSON string containing all search results
        filename: Optional custom filename (default: auto-generated from timestamp)

    Returns:
        Path to the saved file
    """
    data_dir = Path(__file__).parent.parent / "data"
    data_dir.mkdir(exist_ok=True)

    if filename is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_theme = "".join(c if c.isalnum() or c in " _-" else "_" for c in theme[:30])
        safe_theme = safe_theme.replace(" ", "_")
        filename = f"search_{safe_theme}_{timestamp}.json"

    filepath = data_dir / filename

    try:
        results_data = json.loads(results_json)
    except json.JSONDecodeError:
        results_data = {"raw": results_json}

    output = {
        "theme": theme,
        "search_timestamp": datetime.now().isoformat(),
        "results": results_data,
    }

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    return json.dumps(
        {
            "status": "success",
            "message": "Results saved successfully",
            "filepath": str(filepath),
            "theme": theme,
        },
        ensure_ascii=False,
    )


def _search_single_source(
    source_obj,
    keyword_groups: list[list[str]],
    *,
    date_start: str,
    date_end: str,
    per_source_limit: int,
    language: str | None,
) -> tuple[str, list[ArchiveDocument], int, str | None, bool]:
    """単一ソースを検索して結果を返す（並列実行用）。

    各キーワードグループで検索し、結果なし＆複数キーワード時は
    個別キーワードでフォールバック検索を実行する。

    Returns:
        (source_key, documents, total_hits, error, fallback_used)
    """
    key = source_obj.source_key
    docs: list[ArchiveDocument] = []
    seen_urls: set[str] = set()
    total_hits = 0
    error: str | None = None
    fallback_used = False

    def _do_search(kw_list: list[str]) -> tuple[list[ArchiveDocument], int, str | None]:
        """キーワードリストで1回検索する。"""
        if not kw_list:
            return [], 0, None
        try:
            lang_arg = language if (language and source_obj.supports_language_filter) else None
            result = source_obj.search(
                keywords=kw_list,
                date_start=date_start,
                date_end=date_end,
                max_results=per_source_limit,
                language=lang_arg,
            )
            return result.documents, result.total_hits, result.error
        except Exception as e:
            return [], 0, str(e)

    # 各キーワードグループで検索してマージ
    for kw_list in keyword_groups:
        found_docs, hits, err = _do_search(kw_list)
        total_hits += hits
        if err:
            error = err
        for doc in found_docs:
            if doc.source_url not in seen_urls:
                seen_urls.add(doc.source_url)
                docs.append(doc)

    # フォールバック: 結果なし & 複数キーワードの場合、個別に検索
    first_group = keyword_groups[0] if keyword_groups else []
    if not docs and len(first_group) > 1:
        fallback_used = True
        for kw_group in keyword_groups:
            for kw in kw_group:
                found_docs, hits, err = _do_search([kw])
                total_hits += hits
                if err:
                    error = err
                for doc in found_docs:
                    if doc.source_url not in seen_urls:
                        seen_urls.add(doc.source_url)
                        docs.append(doc)
                if docs:
                    break
            if docs:
                break

    return key, docs, total_hits, error, fallback_used


def _rank_documents(
    docs: list[ArchiveDocument],
) -> list[ArchiveDocument]:
    """keywords_matched 数でドキュメントをランキングする。

    同点の場合は元の順序（API 応答順）を維持する。
    """
    return sorted(docs, key=lambda d: len(d.keywords_matched), reverse=True)


def search_archives(
    keywords: str,
    date_start: str = "1800",
    date_end: str = "1899",
    sources: Optional[str] = None,
    max_results: int = 10,
    language: Optional[str] = None,
    tool_context: Optional[ToolContext] = None,
) -> str:
    """Search multiple public archive APIs in parallel.

    Searches across LOC Digital Collections, DPLA, NYPL, Internet Archive,
    Deutsche Digitale Bibliothek, and Europeana using ThreadPoolExecutor.
    Results are ranked by keyword match count and capped at a total limit.

    When no language filter is specified, automatically expands keywords to
    include both English and Spanish variants. When a language is specified,
    keywords are passed as-is and the language filter is applied to APIs that
    support it.

    Args:
        keywords: Comma-separated search keywords
        date_start: Start year (default: 1800)
        date_end: End year (default: 1899)
        sources: Comma-separated source names to search (default: all US sources).
                 Options: loc, dpla, nypl, internet_archive, ddb, europeana
        max_results: Max results per source (default: 10)
        language: Optional ISO 639-1 language code (en, de, fr, es, nl, pt).
                  When specified, applies language filter to supported APIs
                  and skips bilingual expansion.

    Returns:
        JSON string with merged results from all sources.
    """
    keyword_list = [kw.strip() for kw in keywords.split(",") if kw.strip()]

    # 言語指定がある場合はバイリンガル展開をスキップ
    if language:
        keyword_groups = [keyword_list]
    else:
        expanded = expand_keywords_bilingual(keyword_list)
        keyword_groups = [expanded["en"], expanded["es"]]

    all_sources_map = get_all_sources()

    if sources:
        source_keys = [s.strip().lower() for s in sources.split(",") if s.strip()]
    else:
        # デフォルトは US ソース
        source_keys = ["loc", "dpla", "nypl", "internet_archive"]

    # 動的 per-source 制限: ソース数で均等割（最低3件/ソース）
    valid_source_count = sum(1 for k in source_keys if k in all_sources_map)
    if valid_source_count > 0:
        per_source_limit = min(max_results, max(3, _TOTAL_DOCS_CAP // valid_source_count))
    else:
        per_source_limit = max_results

    all_docs: list[ArchiveDocument] = []
    source_results: dict = {}
    errors: dict = {}
    seen_urls: set[str] = set()
    fallback_used = False

    # 不明ソースを先にエラー登録
    valid_sources = []
    for key in source_keys:
        source_obj = all_sources_map.get(key)
        if source_obj is None:
            errors[key] = f"Unknown source: {key}"
        else:
            valid_sources.append((key, source_obj))

    # 並列実行
    with concurrent.futures.ThreadPoolExecutor(
        max_workers=min(_MAX_WORKERS, len(valid_sources) or 1)
    ) as executor:
        futures = {
            executor.submit(
                _search_single_source,
                source_obj,
                keyword_groups,
                date_start=date_start,
                date_end=date_end,
                per_source_limit=per_source_limit,
                language=language,
            ): key
            for key, source_obj in valid_sources
        }
        for future in concurrent.futures.as_completed(futures):
            key = futures[future]
            source_obj = all_sources_map[key]
            try:
                src_key, src_docs, src_hits, src_err, src_fallback = future.result()
            except Exception as e:
                errors[key] = str(e)
                source_results[key] = {
                    "name": source_obj.source_name,
                    "total_hits": 0,
                    "documents_returned": 0,
                }
                continue

            if src_err:
                errors[key] = src_err
            if src_fallback:
                fallback_used = True

            # メインスレッドで URL 重複除去
            deduped_docs = []
            for doc in src_docs:
                if doc.source_url not in seen_urls:
                    seen_urls.add(doc.source_url)
                    deduped_docs.append(doc)

            all_docs.extend(deduped_docs)
            source_results[key] = {
                "name": source_obj.source_name,
                "total_hits": src_hits,
                "documents_returned": len(deduped_docs),
            }

    all_keywords_used = []
    for kw_group in keyword_groups:
        all_keywords_used.extend(kw_group)

    # ランキング（keywords_matched 数でスコアリング）→ 上限適用
    all_docs = _rank_documents(all_docs)
    all_docs = all_docs[:_TOTAL_DOCS_CAP]

    # リンク品質検証（ランキング後の上位ドキュメントのみ）
    try:
        validation = validate_documents(all_docs)
        all_docs = validation.verified_documents
    except Exception:
        validation = ValidationSummary(
            total_checked=0, reachable=0, unreachable=0,
            domain_mismatch=0, removed_urls=[], duration_ms=0,
            verified_documents=list(all_docs),
        )
    logger.info(
        "アーカイブ検索完了: %d 件 (検証後), sources=%s, リンク検証=%d/%d",
        len(all_docs), list(source_results.keys()),
        validation.reachable, validation.total_checked,
        extra={
            "api_name": "archives_combined", "result_count": len(all_docs),
            "sources_searched": list(source_results.keys()),
            "fallback_used": fallback_used,
            "links_verified": validation.reachable,
            "links_checked": validation.total_checked,
        },
    )

    all_docs_dicts = [doc.model_dump() for doc in all_docs]

    # API キー未設定の警告
    warnings = []
    api_key_errors = {k: v for k, v in errors.items() if "not set" in str(v)}
    if api_key_errors:
        skipped = ", ".join(api_key_errors.keys())
        warnings.append(
            f"API keys not configured for: {skipped}. "
            f"These sources were skipped. Set the required environment variables to enable them."
        )

    result = {
        "warnings": warnings if warnings else None,
        "keywords_used": all_keywords_used,
        "sources_searched": source_results,
        "total_documents": len(all_docs_dicts),
        "documents": all_docs_dicts,
        "errors": errors if errors else None,
        "fallback_used": fallback_used,
        "link_validation": {
            "total_checked": validation.total_checked,
            "reachable": validation.reachable,
            "unreachable": validation.unreachable,
            "removed_count": len(validation.removed_urls),
            "removed_urls": validation.removed_urls,
            "duration_ms": validation.duration_ms,
        },
    }

    # セッション状態に保存
    if tool_context is not None:
        state_key = f"raw_search_results_{language}" if language else "raw_search_results"
        existing = tool_context.state.get(state_key, [])
        existing.append(result)
        tool_context.state[state_key] = existing

    return json.dumps(result, ensure_ascii=False, indent=2)


def get_available_keywords() -> str:
    """Get the list of available bilingual keyword pairs.

    Returns the predefined English-Spanish keyword pairs that can be
    used for searching historical mysteries.

    Returns:
        JSON string containing keyword pairs
    """
    return json.dumps(
        {
            "description": "Available bilingual keyword pairs for historical mystery searches",
            "keyword_pairs": KEYWORD_PAIRS,
            "usage": "Use these keywords to search both English and Spanish sources",
        },
        ensure_ascii=False,
        indent=2,
    )
