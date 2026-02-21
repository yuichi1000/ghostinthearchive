"""NYPL Digital Collections API ソース。

ニューヨーク公共図書館のデジタル化コレクション（写本、地図、写真、
希少資料）を検索する。
"""

import os
from typing import Optional

import requests

from ..schemas.document import ArchiveDocument, SourceLanguage
from .archive_source_base import ArchiveSearchResult, ArchiveSource
from .search_utils import build_search_query
from .source_registry import register_source

BASE_URL = "https://api.repo.nypl.org/api/v2/items/search"


class NYPLSource(ArchiveSource):
    """NYPL Digital Collections ソース。"""

    source_key = "nypl"
    source_name = "NYPL Digital Collections"
    source_type = "nypl"
    min_request_delay = 1.0
    supported_languages = {"en"}
    supports_language_filter = False
    is_newspaper_source = False
    expected_domains = ["digitalcollections.nypl.org", "nypl.org"]
    env_var_key = "NYPL_API_TOKEN"

    def _search_impl(
        self,
        keywords: list[str],
        date_start: str,
        date_end: str,
        max_results: int,
        language: str | None,
    ) -> ArchiveSearchResult:
        api_token = os.environ.get("NYPL_API_TOKEN", "")

        search_text = build_search_query(keywords)
        if not search_text:
            return ArchiveSearchResult(error="No keywords provided")

        # 空文字日付対応: 日付範囲をクエリに含めるのを条件付きに
        if date_start and date_end:
            start_year = date_start[:4] if len(date_start) >= 4 else date_start
            end_year = date_end[:4] if len(date_end) >= 4 else date_end
            search_text_with_date = f"{search_text} {start_year}-{end_year}"
        else:
            search_text_with_date = search_text

        params = {
            "q": search_text_with_date,
            "per_page": min(max_results, 100),
            "page": 1,
            "publicDomainOnly": "true",
        }

        response = self._session.get(
            BASE_URL,
            params=params,
            timeout=30,
            headers={
                "Authorization": f'Token token="{api_token}"',
                "User-Agent": "GhostInTheArchive/1.0",
            },
        )
        response.raise_for_status()
        data = response.json()

        documents = []
        nypl_response = data.get("nyplAPI", {}).get("response", {})
        results = nypl_response.get("result", [])
        if not isinstance(results, list):
            results = [results] if results else []

        for item in results:
            title = item.get("title", "Unknown Title")
            if isinstance(title, list):
                title = title[0] if title else "Unknown Title"

            uuid = item.get("uuid", "")
            url = f"https://digitalcollections.nypl.org/items/{uuid}" if uuid else ""
            if not url:
                continue

            date_str = item.get("dateDigitized", "")

            doc = ArchiveDocument(
                title=str(title)[:500],
                date=self.parse_year(str(date_str)),
                source_url=url,
                summary=str(title)[:500],
                language=SourceLanguage.EN,
                location="New York",
                source_type=self.source_type,
                raw_text=None,
                keywords_matched=[
                    kw for kw in keywords if kw.lower() in str(title).lower()
                ],
            )
            documents.append(doc)

        total_hits = int(nypl_response.get("numResults", 0))
        return ArchiveSearchResult(documents=documents, total_hits=total_hits)


# レジストリに自動登録
_instance = NYPLSource()
register_source(_instance)
