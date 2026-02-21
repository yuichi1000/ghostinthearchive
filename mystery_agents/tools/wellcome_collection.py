"""Wellcome Collection Catalogue API ソース。

Wellcome Collection（ロンドン）の Catalogue API v2 を使用して
医学史・写本・民俗・迷信コレクション（数百万点）を検索する。
認証不要。レスポンスは JSON。
"""

import logging
import re

from ..schemas.document import ArchiveDocument, SourceLanguage
from .archive_source_base import ArchiveSearchResult, ArchiveSource
from .search_utils import build_search_query
from .source_registry import register_source

logger = logging.getLogger(__name__)

BASE_URL = "https://api.wellcomecollection.org/catalogue/v2/works"

# ISO 639-3 → SourceLanguage マッピング
_LANG_MAP: dict[str, SourceLanguage] = {
    "eng": SourceLanguage.EN,
    "fre": SourceLanguage.FR,
    "fra": SourceLanguage.FR,
    "deu": SourceLanguage.DE,
    "ger": SourceLanguage.DE,
    "spa": SourceLanguage.ES,
    "nld": SourceLanguage.NL,
    "dut": SourceLanguage.NL,
    "por": SourceLanguage.PT,
    "jpn": SourceLanguage.JA,
}

# ISO 639-1 → 639-3 マッピング（言語フィルタ用）
_LANG_1_TO_3: dict[str, str] = {
    "en": "eng",
    "fr": "fre",
    "de": "ger",
    "es": "spa",
    "nl": "dut",
    "pt": "por",
    "ja": "jpn",
}


def _strip_html(text: str | None) -> str:
    """HTML タグを除去する。

    Args:
        text: HTML を含む可能性のあるテキスト

    Returns:
        タグ除去済みのプレーンテキスト。None の場合は空文字列。
    """
    if not text:
        return ""
    return re.sub(r"<[^>]+>", "", text).strip()


def _extract_date_label(work: dict) -> str:
    """production.dates からラベルを抽出する。

    Args:
        work: Wellcome API の work オブジェクト

    Returns:
        日付ラベル文字列。見つからない場合は空文字列。
    """
    for prod in work.get("production", []):
        for date in prod.get("dates", []):
            label = date.get("label", "")
            if label:
                return label
    return ""


def _extract_location(work: dict) -> str:
    """production.places から場所を抽出する。

    Args:
        work: Wellcome API の work オブジェクト

    Returns:
        場所ラベル。見つからない場合は "United Kingdom"。
    """
    for prod in work.get("production", []):
        for place in prod.get("places", []):
            label = place.get("label", "")
            if label:
                return label
    return "United Kingdom"


def _detect_language(work: dict) -> SourceLanguage:
    """languages フィールドから SourceLanguage を検出する。

    Args:
        work: Wellcome API の work オブジェクト

    Returns:
        検出された SourceLanguage。不明な場合は EN をデフォルトにする。
    """
    languages = work.get("languages", [])
    if languages:
        lang_id = languages[0].get("id", "")
        if lang_id in _LANG_MAP:
            return _LANG_MAP[lang_id]
    return SourceLanguage.EN


def _parse_wellcome_response(
    data: dict, keywords: list[str]
) -> ArchiveSearchResult:
    """Wellcome API JSON レスポンスを ArchiveSearchResult に変換する。

    Args:
        data: API レスポンスの JSON 辞書
        keywords: マッチ検出用のキーワードリスト

    Returns:
        パース済みの ArchiveSearchResult
    """
    total_hits = data.get("totalResults", 0)
    documents = []

    for work in data.get("results", []):
        work_id = work.get("id")
        if not work_id:
            continue

        title = work.get("title", "Unknown Title")
        description = _strip_html(work.get("description"))
        summary_text = description or title

        date_label = _extract_date_label(work)
        parsed_date = ArchiveSource.parse_year(date_label) if date_label else None

        source_url = f"https://wellcomecollection.org/works/{work_id}"
        location = _extract_location(work)
        language = _detect_language(work)

        # キーワードマッチ
        combined = f"{title} {summary_text}".lower()
        matched = [kw for kw in keywords if kw.lower() in combined]

        doc = ArchiveDocument(
            title=str(title)[:500],
            date=parsed_date,
            source_url=source_url,
            summary=str(summary_text)[:500],
            language=language,
            location=str(location)[:200],
            source_type="wellcome",
            raw_text=None,  # Catalogue API は全文テキスト非提供
            keywords_matched=matched,
        )
        documents.append(doc)

    return ArchiveSearchResult(documents=documents, total_hits=total_hits)


class WellcomeSource(ArchiveSource):
    """Wellcome Collection（ロンドン）ソース。"""

    source_key = "wellcome"
    source_name = "Wellcome Collection"
    source_type = "wellcome"
    min_request_delay = 1.0
    supported_languages = {"en"}
    supports_language_filter = True
    is_newspaper_source = False
    expected_domains = ["wellcomecollection.org"]
    env_var_key = None  # 認証不要

    def _search_impl(
        self,
        keywords: list[str],
        date_start: str,
        date_end: str,
        max_results: int,
        language: str | None,
    ) -> ArchiveSearchResult:
        search_text = build_search_query(keywords)
        if not search_text:
            return ArchiveSearchResult(error="No keywords provided")

        params: dict[str, str | int] = {
            "query": search_text,
            "pageSize": min(max_results, 100),
            "include": "subjects,genres,contributors,production,languages",
        }

        # 日付フィルタ（YYYY-MM-DD 形式）
        if date_start:
            params["production.dates.from"] = f"{date_start[:4]}-01-01"
        if date_end:
            params["production.dates.to"] = f"{date_end[:4]}-12-31"

        # 言語フィルタ（ISO 639-1 → 639-3 変換）
        if language and language in _LANG_1_TO_3:
            params["languages"] = _LANG_1_TO_3[language]

        headers = {
            "Accept": "application/json",
            "User-Agent": "GhostInTheArchive/1.0",
        }

        response = self._session.get(
            BASE_URL,
            params=params,
            headers=headers,
            timeout=30,
        )
        response.raise_for_status()

        return _parse_wellcome_response(response.json(), keywords)


# レジストリに自動登録
_instance = WellcomeSource()
register_source(_instance)
