"""LLM-facing tool functions for the Librarian Agent.

These functions wrap the low-level API tools and provide a simple
string-based interface for the LLM to use.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Optional

from google.adk.tools.tool_context import ToolContext

from .bilingual_search import KEYWORD_PAIRS, expand_keywords_bilingual
from .chronicling_america import search_chronicling_america
from .ddb import search_ddb
from .dpla import search_dpla
from .internet_archive import search_internet_archive
from .loc_digital import search_loc_digital
from .nypl_digital import search_nypl


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
    expansion (all US states), and date range expansion (±10 years).

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
    # Parse keywords
    keyword_list = [kw.strip() for kw in keywords.split(",") if kw.strip()]

    # Expand keywords to bilingual
    expanded = expand_keywords_bilingual(keyword_list)
    en_keywords = expanded["en"]
    es_keywords = expanded["es"]

    # Parse states if provided
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

    # Level 1: All keywords together (bilingual)
    levels_used.append("L1_bilingual_combined")
    for kw_list in [en_keywords, es_keywords]:
        _search_and_collect(kw_list)

    # Level 2: Individual keywords (if not enough results)
    if len(all_docs) < min_results and len(en_keywords) > 1:
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

    # Level 3: Remove geographic restriction (search all states)
    if len(all_docs) < min_results and state_list is not None:
        levels_used.append("L3_all_states")
        for kw_list in [en_keywords, es_keywords]:
            _search_and_collect(kw_list, search_states=None)
            if len(all_docs) >= min_results:
                break

    # Level 4: Expand date range ±10 years
    if len(all_docs) < min_results:
        expanded_start = str(max(1700, int(date_start) - 10))
        expanded_end = str(min(1920, int(date_end) + 10))
        if expanded_start != date_start or expanded_end != date_end:
            levels_used.append(f"L4_date_expanded_{expanded_start}_{expanded_end}")
            for kw_list in [en_keywords, es_keywords]:
                _search_and_collect(kw_list, search_states=None, start=expanded_start, end=expanded_end)
                if len(all_docs) >= min_results:
                    break

    docs = [doc.model_dump() for doc in all_docs]

    result = {
        "source": "chronicling_america",
        "keywords_used": all_keywords_used,
        "total_hits": total_hits,
        "documents_returned": len(docs),
        "documents": docs,
        "error": error,
        "search_levels_used": levels_used,
    }

    # Save raw search results to session state for downstream agents
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
    # Find project root (where data/ directory should be)
    data_dir = Path(__file__).parent.parent / "data"
    data_dir.mkdir(exist_ok=True)

    if filename is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        # Create safe filename from theme
        safe_theme = "".join(c if c.isalnum() or c in " _-" else "_" for c in theme[:30])
        safe_theme = safe_theme.replace(" ", "_")
        filename = f"search_{safe_theme}_{timestamp}.json"

    filepath = data_dir / filename

    # Parse and re-structure the results
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


# 言語フィルタをサポートするソース
_LANGUAGE_FILTER_SOURCES = {"dpla", "internet_archive"}

_ARCHIVE_SOURCES = {
    "loc": ("LOC Digital Collections", search_loc_digital),
    "dpla": ("DPLA", search_dpla),
    "nypl": ("NYPL Digital Collections", search_nypl),
    "internet_archive": ("Internet Archive", search_internet_archive),
    "ddb": ("Deutsche Digitale Bibliothek", search_ddb),
}


def search_archives(
    keywords: str,
    date_start: str = "1800",
    date_end: str = "1899",
    sources: Optional[str] = None,
    max_results: int = 10,
    language: Optional[str] = None,
    tool_context: Optional[ToolContext] = None,
) -> str:
    """Search multiple public archive APIs simultaneously.

    Searches across LOC Digital Collections, DPLA, NYPL, Internet Archive,
    and Deutsche Digitale Bibliothek.
    Results are merged and returned as a unified JSON response.

    When no language filter is specified, automatically expands keywords to
    include both English and Spanish variants. When a language is specified,
    keywords are passed as-is and the language filter is applied to APIs that
    support it.

    Args:
        keywords: Comma-separated search keywords
        date_start: Start year (default: 1800)
        date_end: End year (default: 1899)
        sources: Comma-separated source names to search (default: all US sources).
                 Options: loc, dpla, nypl, internet_archive, ddb
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

    if sources:
        source_keys = [s.strip().lower() for s in sources.split(",") if s.strip()]
    else:
        # デフォルトは既存の US ソースのみ（後方互換性維持）
        source_keys = ["loc", "dpla", "nypl", "internet_archive"]

    all_docs = []
    source_results = {}
    errors = {}
    seen_urls = set()
    fallback_used = False

    def _search_source(search_fn, kw_list, source_key):
        """Search a single source with given keywords, collecting results."""
        docs = []
        hits = 0
        err = None
        if not kw_list:
            return docs, hits, err
        try:
            kwargs = {
                "keywords": kw_list,
                "date_start": date_start,
                "date_end": date_end,
                "max_results": max_results,
            }
            # 言語フィルタをサポートする API にのみ language を渡す
            if language and source_key in _LANGUAGE_FILTER_SOURCES:
                kwargs["language"] = language
            result = search_fn(**kwargs)
            hits = result.get("total_hits", 0)
            err = result.get("error")
            for doc in result.get("documents", []):
                dump = doc.model_dump()
                url = dump.get("source_url", "")
                if url not in seen_urls:
                    seen_urls.add(url)
                    docs.append(dump)
        except Exception as e:
            err = str(e)
        return docs, hits, err

    for key in source_keys:
        if key not in _ARCHIVE_SOURCES:
            errors[key] = f"Unknown source: {key}"
            continue

        name, search_fn = _ARCHIVE_SOURCES[key]
        source_hits = 0
        source_docs = []

        # 各キーワードグループで検索してマージ
        for kw_list in keyword_groups:
            docs, hits, err = _search_source(search_fn, kw_list, key)
            source_docs.extend(docs)
            source_hits += hits
            if err:
                errors[key] = err

        # フォールバック: 結果なし & 複数キーワードの場合、個別に検索
        first_group = keyword_groups[0] if keyword_groups else []
        if not source_docs and len(first_group) > 1:
            fallback_used = True
            for kw_group in keyword_groups:
                for kw in kw_group:
                    docs, hits, err = _search_source(search_fn, [kw], key)
                    source_docs.extend(docs)
                    source_hits += hits
                    if err:
                        errors[key] = err

        all_docs.extend(source_docs)
        source_results[key] = {
            "name": name,
            "total_hits": source_hits,
            "documents_returned": len(source_docs),
        }

    all_keywords_used = []
    for kw_group in keyword_groups:
        all_keywords_used.extend(kw_group)

    # Build warnings for missing API keys
    warnings = []
    api_key_errors = {k: v for k, v in errors.items() if "not set" in str(v)}
    if api_key_errors:
        skipped = ", ".join(api_key_errors.keys())
        warnings.append(
            f"⚠ API keys not configured for: {skipped}. "
            f"These sources were skipped. Set the required environment variables to enable them."
        )

    result = {
        "warnings": warnings if warnings else None,
        "keywords_used": all_keywords_used,
        "sources_searched": source_results,
        "total_documents": len(all_docs),
        "documents": all_docs,
        "errors": errors if errors else None,
        "fallback_used": fallback_used,
    }

    # Save raw search results to session state for downstream agents
    if tool_context is not None:
        # 言語指定がある場合は言語別キーに保存
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
