"""Internet Archive (Archive.org) Search API ソース。

Internet Archive の膨大なコレクション（書籍、雑誌、ウェブページ、
その他のデジタル化資料）を検索する。
"""

from typing import Optional

import requests

from ..schemas.document import ArchiveDocument, SourceLanguage
from .archive_source_base import ArchiveSearchResult, ArchiveSource
from .search_utils import build_search_query
from .source_registry import register_source

BASE_URL = "https://archive.org/advancedsearch.php"

_LANG_CODE_MAP = {
    "en": ["eng", "english"],
    "es": ["spa", "spanish", "español"],
    "de": ["ger", "deu", "german", "deutsch"],
    "fr": ["fre", "fra", "french", "français"],
    "nl": ["dut", "nld", "dutch", "nederlands"],
    "pt": ["por", "portuguese", "português"],
}


class InternetArchiveSource(ArchiveSource):
    """Internet Archive ソース。"""

    source_key = "internet_archive"
    source_name = "Internet Archive"
    source_type = "internet_archive"
    min_request_delay = 2.0
    supported_languages = {"en", "es", "de", "fr", "nl", "pt"}
    supports_language_filter = True
    is_newspaper_source = False
    expected_domains = ["archive.org"]
    env_var_key = None

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

        # 空文字日付対応: 日付フィルタを条件付きに
        query = f"({search_text})"
        if date_start and date_end:
            start_year = date_start[:4] if len(date_start) >= 4 else date_start
            end_year = date_end[:4] if len(date_end) >= 4 else date_end
            query += f" AND date:[{start_year}-01-01 TO {end_year}-12-31]"

        # 言語フィルタ
        if language and language in _LANG_CODE_MAP:
            lang_codes = _LANG_CODE_MAP[language]
            lang_filter = " OR ".join(f'language:"{code}"' for code in lang_codes)
            query = f"{query} AND ({lang_filter})"

        params = {
            "q": query,
            "fl[]": [
                "identifier",
                "title",
                "description",
                "date",
                "language",
                "subject",
                "creator",
            ],
            "sort[]": "date asc",
            "rows": min(max_results, 100),
            "page": 1,
            "output": "json",
        }

        response = self._session.get(
            BASE_URL,
            params=params,
            timeout=30,
            headers={"User-Agent": "GhostInTheArchive/1.0"},
        )
        response.raise_for_status()
        data = response.json()

        resp = data.get("response", {})
        documents = []

        for item in resp.get("docs", []):
            title = item.get("title", "Unknown Title")
            if isinstance(title, list):
                title = title[0] if title else "Unknown Title"

            description = item.get("description", "")
            if isinstance(description, list):
                description = " ".join(str(d) for d in description)

            identifier = item.get("identifier", "")
            url = f"https://archive.org/details/{identifier}" if identifier else ""
            if not url:
                continue

            date_str = item.get("date", "")
            if isinstance(date_str, list) and date_str:
                date_str = str(date_str[0])

            item_language = item.get("language", "")
            if isinstance(item_language, list) and item_language:
                item_language = str(item_language[0])
            lang = _detect_source_language(str(item_language))

            combined = f"{title} {description}".lower()
            matched = [kw for kw in keywords if kw.lower() in combined]

            doc = ArchiveDocument(
                title=str(title)[:500],
                date=self.parse_year(str(date_str), min_century=13),
                source_url=url,
                summary=str(description)[:500] if description else str(title)[:500],
                language=lang,
                location="Unknown",
                source_type=self.source_type,
                raw_text=str(description)[:5000] if description else None,
                keywords_matched=matched,
            )
            documents.append(doc)

        total_hits = resp.get("numFound", 0)
        return ArchiveSearchResult(documents=documents, total_hits=total_hits)


def _detect_source_language(lang_str: str) -> SourceLanguage:
    """メタデータの言語文字列から SourceLanguage を判定する。"""
    lower = lang_str.lower()
    for lang_code, identifiers in _LANG_CODE_MAP.items():
        for ident in identifiers:
            if ident in lower:
                try:
                    return SourceLanguage(lang_code)
                except ValueError:
                    break
    return SourceLanguage.EN


# レジストリに自動登録
_instance = InternetArchiveSource()
register_source(_instance)
