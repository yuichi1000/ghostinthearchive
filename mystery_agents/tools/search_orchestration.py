"""アーカイブ検索の内部オーケストレーション。

librarian_tools.py から分離した内部ヘルパー関数群。
単一ソース検索、ドキュメントランキング、キーワード翻訳を提供する。
"""

import logging
from collections import defaultdict
from typing import Optional

from google.adk.tools.tool_context import ToolContext
from shared.constants import LATIN_SCRIPT_LANGUAGES
from shared.keyword_translator import translate_keywords
from shared.state_keys import SELECTED_LANGUAGES

from ..schemas.document import ArchiveDocument

logger = logging.getLogger(__name__)


def _search_single_source(
    source_obj,
    keyword_groups: list[list[str]],
    *,
    date_start: str | None,
    date_end: str | None,
    per_source_limit: int,
    language: str | None,
    reference_keywords: list[str] | None = None,
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
                reference_keywords=reference_keywords,
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

    # reference_keywords_matched を算出: title/summary 内の固有名詞マッチ
    if reference_keywords:
        for doc in docs:
            combined = f"{doc.title} {doc.summary}".lower()
            doc.reference_keywords_matched = [
                kw for kw in reference_keywords if kw.lower() in combined
            ]

    return key, docs, total_hits, error, fallback_used


def _filter_irrelevant_documents(
    docs: list[ArchiveDocument],
) -> tuple[list[ArchiveDocument], int]:
    """keywords_matched が空のドキュメントを除外する。

    ソース単位の全除外防止: あるソースの全ドキュメントが除外対象の場合、
    API の検索結果を尊重してそのソースのドキュメントを全て保持する。
    これにより、形態論的差異（オランダ語等）で部分文字列マッチが
    系統的に失敗するソースのドキュメントが失われることを防ぐ。
    """
    by_source: dict[str, list[ArchiveDocument]] = defaultdict(list)
    for doc in docs:
        by_source[doc.source_type].append(doc)

    filtered: list[ArchiveDocument] = []
    total_removed = 0

    for source_type, source_docs in by_source.items():
        matched = [d for d in source_docs if d.keywords_matched]
        if matched:
            # 一部マッチ → マッチしたもののみ保持（通常フィルタ）
            filtered.extend(matched)
            removed = len(source_docs) - len(matched)
            if removed > 0:
                logger.info(
                    "キーワード無一致ドキュメント除外: %s から %d 件",
                    source_type, removed,
                )
            total_removed += removed
        else:
            # 全除外防止: API 検索結果を尊重して全保持
            filtered.extend(source_docs)
            logger.info(
                "キーワード無一致 全除外防止: %s の %d 件を保持（API 検索結果を尊重）",
                source_type, len(source_docs),
            )

    return filtered, total_removed


def _rank_documents(
    docs: list[ArchiveDocument],
) -> list[ArchiveDocument]:
    """ソースインターリーブでドキュメントをランキングする。

    各ソース（source_type）ごとに keywords_matched 数でソートした後、
    ラウンドロビンで各ソースから1件ずつ取り出して最終リストを構築する。
    これにより、メタデータ豊富な特定ソースが上位を独占するのを防ぐ。
    """
    docs, _ = _filter_irrelevant_documents(docs)

    # ソースごとにグループ化して各グループ内でランキング
    by_source: dict[str, list[ArchiveDocument]] = defaultdict(list)
    for doc in docs:
        by_source[doc.source_type].append(doc)
    for key in by_source:
        by_source[key].sort(
            key=lambda d: (len(d.reference_keywords_matched), len(d.keywords_matched)),
            reverse=True,
        )

    # ラウンドロビンインターリーブ
    result: list[ArchiveDocument] = []
    source_iters = [iter(v) for v in by_source.values()]
    while source_iters:
        next_round = []
        for it in source_iters:
            doc = next(it, None)
            if doc is not None:
                result.append(doc)
                next_round.append(it)
        source_iters = next_round
    return result


def _is_ascii_only(keyword: str) -> bool:
    """キーワードが ASCII 文字のみで構成されているか判定する。

    ASCII 文字のみで構成されるキーワードを検出する。
    ドイツ語のウムラウト（ä,ö,ü）、フランス語のアクセント（é,è）等の
    非 ASCII 文字を含む場合は False を返す。
    """
    return all(ord(c) < 128 for c in keyword)


def _log_keyword_language_mismatch(
    keywords: list[str], language: str
) -> None:
    """非英語 Librarian が英語キーワードのみで検索していないかログ出力する。

    ラテン文字言語（de, es, fr 等）は ASCII のみのキーワードでも正当な
    ネイティブ語である可能性が高いため DEBUG レベルに抑制する。
    非ラテン文字言語（ja, ko 等）では WARNING を維持する。
    """
    ascii_only = [kw for kw in keywords if _is_ascii_only(kw)]
    if len(ascii_only) == len(keywords) and keywords:
        log_level = (
            logging.DEBUG
            if language in LATIN_SCRIPT_LANGUAGES
            else logging.WARNING
        )
        logger.log(
            log_level,
            "キーワード言語不一致: language=%s だが全キーワードが ASCII のみ "
            "(ネイティブ言語キーワード未使用の可能性): %s",
            language,
            keywords,
            extra={
                "language": language,
                "keywords": keywords,
                "all_ascii": True,
            },
        )


def _get_expansion_languages(tool_context: Optional[ToolContext], current_lang: str) -> list[str]:
    """selected_languages から current_lang を除いた言語リストを返す。

    1言語のみなら空リスト（展開不要）。tool_context が None の場合も空リスト。
    """
    if tool_context is None:
        return []
    selected = tool_context.state.get(SELECTED_LANGUAGES, [])
    if not isinstance(selected, list) or len(selected) <= 1:
        return []
    return [lang for lang in selected if lang != current_lang]


def _translate_keywords_for_source(
    keyword_list: list[str],
    source_obj,
) -> list[str] | None:
    """単一言語非英語ソースに英語キーワードが渡された場合、自動翻訳する。

    対象: supported_languages が単一言語かつ非英語のソース（DDB=de, NDL=ja）
    条件: 全キーワードが ASCII のみ（英語と推定）

    Returns:
        翻訳成功 → 翻訳キーワードリスト
        対象外・翻訳失敗 → None（元キーワードで続行）
    """
    # 英語ソースまたは多言語ソースはスキップ
    supported = source_obj.supported_languages
    if len(supported) != 1:
        return None
    primary_lang = next(iter(supported))
    if primary_lang == "en":
        return None

    # ラテン文字言語ソースは ASCII キーワードが正当なネイティブ語の可能性が高い → スキップ
    if primary_lang in LATIN_SCRIPT_LANGUAGES:
        return None

    # 非 ASCII キーワードが1つでもあればネイティブ言語が既に含まれている
    if not all(_is_ascii_only(kw) for kw in keyword_list):
        return None

    # 英語キーワードをソースのネイティブ言語に翻訳
    logger.warning(
        "キーワード言語不一致を検出: ソース=%s (言語=%s) に英語キーワードのみ → 自動翻訳を試行: %s",
        source_obj.source_key,
        primary_lang,
        keyword_list,
        extra={
            "source_key": source_obj.source_key,
            "source_lang": primary_lang,
            "keywords": keyword_list,
        },
    )
    translated = translate_keywords(keyword_list, "en", [primary_lang])
    native_kws = translated.get(primary_lang)
    if not native_kws:
        return None
    return native_kws
