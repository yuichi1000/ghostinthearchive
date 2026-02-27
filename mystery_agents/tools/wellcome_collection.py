"""Wellcome Collection Catalogue API ソース。

Wellcome Collection（ロンドン）の Catalogue API v2 を使用して
医学史・写本・民俗・迷信コレクション（数百万点）を検索する。
認証不要。レスポンスは JSON。
"""

import logging

from ..schemas.document import ArchiveDocument
from .archive_source_base import ArchiveSearchResult, ArchiveSource
from .search_utils import build_search_query
from .source_registry import register_source

logger = logging.getLogger(__name__)

# archive_source_base.py に統一された strip_html を使用
_strip_html = ArchiveSource.strip_html

BASE_URL = "https://api.wellcomecollection.org/catalogue/v2/works"

# ISO 639-3 → ISO 639-1 マッピング（言語検出用）
_LANG_MAP: dict[str, str] = {
    "eng": "en",
    "fre": "fr",
    "fra": "fr",
    "deu": "de",
    "ger": "de",
    "spa": "es",
    "nld": "nl",
    "dut": "nl",
    "por": "pt",
    "jpn": "ja",
    "ita": "it",
    "lat": "la",
    "rus": "ru",
    "ara": "ar",
    "zho": "zh",
    "chi": "zh",
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


def _detect_language(work: dict) -> str:
    """languages フィールドから ISO 639-1 コードを返す。

    Args:
        work: Wellcome API の work オブジェクト

    Returns:
        ISO 639-1 言語コード。不明な場合は "en" をデフォルトにする。
    """
    languages = work.get("languages", [])
    if languages:
        lang_id = languages[0].get("id", "")
        if lang_id in _LANG_MAP:
            return _LANG_MAP[lang_id]
    return "en"


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

        # notes フィールドから補足テキストを抽出
        notes_parts: list[str] = []
        for note in work.get("notes", []):
            note_text = _strip_html(note.get("contents", ""))
            if note_text:
                notes_parts.append(note_text)
        notes_text = " ".join(notes_parts)

        summary_text = description or title

        # description + notes を結合して raw_text に設定
        raw_text_parts = [p for p in [description, notes_text] if p]
        raw_text = " ".join(raw_text_parts)[:5000] if raw_text_parts else None

        date_label = _extract_date_label(work)
        parsed_date = ArchiveSource.parse_year(date_label) if date_label else None

        source_url = f"https://wellcomecollection.org/works/{work_id}"
        location = _extract_location(work)
        language = _detect_language(work)

        # キーワードマッチ
        combined = f"{title} {summary_text}".lower()
        matched = [kw for kw in keywords if kw.lower() in combined]

        # サムネイル URL 抽出
        thumbnail = work.get("thumbnail", {})
        thumbnail_url = thumbnail.get("url") if isinstance(thumbnail, dict) else None

        doc = ArchiveDocument(
            title=str(title)[:500],
            date=parsed_date,
            source_url=source_url,
            summary=str(summary_text)[:500],
            language=language,
            location=str(location)[:200],
            source_type="wellcome",
            raw_text=raw_text,
            thumbnail_url=thumbnail_url,
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
        date_start: str | None,
        date_end: str | None,
        max_results: int,
        language: str | None,
    ) -> ArchiveSearchResult:
        search_text = build_search_query(keywords)
        if not search_text:
            return ArchiveSearchResult(error="No keywords provided")

        params: dict[str, str | int] = {
            "query": search_text,
            "pageSize": min(max_results, 100),
            "include": "subjects,genres,contributors,production,languages,notes",
        }

        # 日付フィルタ（YYYY-MM-DD 形式）
        has_date_filter = bool(date_start or date_end)
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

        result = _parse_wellcome_response(response.json(), keywords)

        # 日付フィルタ付きで 0 件の場合、日付フィルタなしで再検索する
        # Wellcome の歴史資料は日付メタデータが不完全なことが多い
        if not result.documents and has_date_filter:
            logger.info(
                "Wellcome 日付フィルタフォールバック: 日付フィルタ(%s〜%s)で 0 件 → 日付なしで再検索",
                date_start,
                date_end,
            )
            params_no_date = {
                k: v
                for k, v in params.items()
                if k not in ("production.dates.from", "production.dates.to")
            }
            self._rate_limit()
            response = self._session.get(
                BASE_URL,
                params=params_no_date,
                headers=headers,
                timeout=30,
            )
            response.raise_for_status()
            result = _parse_wellcome_response(response.json(), keywords)

        return result


# レジストリに自動登録
_instance = WellcomeSource()
register_source(_instance)
