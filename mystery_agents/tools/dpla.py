"""Digital Public Library of America (DPLA) API ソース。

DPLA の集約コレクション（全米の図書館・アーカイブ・博物館）を検索する。
"""

import os

import requests

from ..schemas.document import ArchiveDocument, SourceLanguage
from .archive_source_base import ArchiveSearchResult, ArchiveSource
from .search_utils import build_search_query
from .source_registry import register_source

BASE_URL = "https://api.dp.la/v2/items"

# DPLA sourceResource.language.name で使われる言語名マッピング
_DPLA_LANG_NAMES = {
    "en": ["English"],
    "es": ["Spanish", "Español"],
    "de": ["German", "Deutsch"],
    "fr": ["French", "Français"],
    "nl": ["Dutch", "Nederlands"],
    "pt": ["Portuguese", "Português"],
}


class DPLASource(ArchiveSource):
    """Digital Public Library of America ソース。"""

    source_key = "dpla"
    source_name = "DPLA"
    source_type = "dpla"
    min_request_delay = 1.0
    supported_languages = {"en", "es"}
    supports_language_filter = True
    is_newspaper_source = False
    expected_domains = []  # パートナー機関ドメインが多様
    env_var_key = "DPLA_API_KEY"

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

        api_key = os.environ.get("DPLA_API_KEY", "")
        params = {
            "api_key": api_key,
            "q": search_text,
            "page_size": min(max_results, 100),
        }

        # 空文字日付対応: 日付フィルタを条件付きに
        if date_start and date_end:
            start_year = date_start[:4] if len(date_start) >= 4 else date_start
            end_year = date_end[:4] if len(date_end) >= 4 else date_end
            params["sourceResource.date.after"] = start_year
            params["sourceResource.date.before"] = end_year

        # 言語フィルタ
        if language and language in _DPLA_LANG_NAMES:
            params["sourceResource.language.name"] = _DPLA_LANG_NAMES[language][0]

        response = self._session.get(
            BASE_URL,
            params=params,
            timeout=30,
            headers={"User-Agent": "GhostInTheArchive/1.0"},
        )
        response.raise_for_status()
        data = response.json()

        documents = []
        for item in data.get("docs", []):
            sr = item.get("sourceResource", {})

            title = sr.get("title", "Unknown Title")
            if isinstance(title, list):
                title = title[0] if title else "Unknown Title"

            description = sr.get("description", "")
            if isinstance(description, list):
                description = " ".join(str(d) for d in description)

            date_str = ""
            date_info = sr.get("date", {})
            if isinstance(date_info, dict):
                date_str = date_info.get("displayDate", date_info.get("begin", ""))
            elif isinstance(date_info, list) and date_info:
                d = date_info[0]
                date_str = (
                    d.get("displayDate", d.get("begin", ""))
                    if isinstance(d, dict)
                    else str(d)
                )

            spatial = sr.get("spatial", [])
            location = "Unknown"
            if spatial:
                s = spatial[0] if isinstance(spatial, list) else spatial
                if isinstance(s, dict):
                    location = s.get("name", s.get("city", "Unknown"))
                elif isinstance(s, str):
                    location = s

            lang_field = sr.get("language", [])
            lang = SourceLanguage.EN
            if lang_field:
                lang_val = lang_field[0] if isinstance(lang_field, list) else lang_field
                lang_name = (
                    lang_val.get("name", "") if isinstance(lang_val, dict) else str(lang_val)
                )
                lang = _detect_dpla_language(lang_name)

            url = item.get("isShownAt", item.get("@id", ""))
            if not url:
                continue

            # サムネイル / フル画像URL抽出
            obj = item.get("object", "")
            thumbnail_url = obj if isinstance(obj, str) and obj else None
            shown_by = item.get("isShownBy", "")
            full_image = shown_by if isinstance(shown_by, str) and shown_by else None

            doc = ArchiveDocument(
                title=str(title)[:500],
                date=self.parse_year(str(date_str)),
                source_url=url,
                summary=str(description)[:500] if description else "No description",
                language=lang,
                location=str(location)[:200],
                source_type=self.source_type,
                raw_text=str(description)[:5000] if description else None,
                thumbnail_url=thumbnail_url,
                image_url=full_image,
                keywords_matched=[
                    kw
                    for kw in keywords
                    if kw.lower() in str(description).lower()
                    or kw.lower() in str(title).lower()
                ],
            )
            documents.append(doc)

        total_hits = data.get("count", 0)
        return ArchiveSearchResult(documents=documents, total_hits=total_hits)


def _detect_dpla_language(lang_name: str) -> SourceLanguage:
    """DPLA の言語名から SourceLanguage を判定する。"""
    lower = lang_name.lower()
    for lang_code, names in _DPLA_LANG_NAMES.items():
        for name in names:
            if name.lower() in lower:
                try:
                    return SourceLanguage(lang_code)
                except ValueError:
                    break
    return SourceLanguage.EN


# レジストリに自動登録
_instance = DPLASource()
register_source(_instance)
