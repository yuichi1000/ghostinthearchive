"""Library of Congress Digital Collections API ソース。

LOC の loc.gov JSON API を使用して、Chronicling America 以外の
全デジタルコレクションを検索する。
"""

import json
from typing import Optional

import requests

from ..schemas.document import ArchiveDocument, SourceLanguage
from .archive_source_base import ArchiveSearchResult, ArchiveSource
from .search_utils import build_search_query
from .source_registry import register_source

BASE_URL = "https://www.loc.gov/search/"


class LOCDigitalSource(ArchiveSource):
    """Library of Congress Digital Collections ソース。"""

    source_key = "loc"
    source_name = "LOC Digital Collections"
    source_type = "loc_digital"
    min_request_delay = 3.0
    supported_languages = {"en"}
    supports_language_filter = False
    is_newspaper_source = False
    expected_domains = ["loc.gov"]
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

        params = {
            "q": search_text,
            "fa": "not:partof:chronicling america",
            "fo": "json",
            "c": min(max_results, 50),
            "sp": 1,
        }

        # 空文字日付対応: 日付フィルタを条件付きに
        if date_start and date_end:
            start_year = date_start[:4] if len(date_start) >= 4 else date_start
            end_year = date_end[:4] if len(date_end) >= 4 else date_end
            params["dates"] = f"{start_year}/{end_year}"

        response = self._session.get(
            BASE_URL,
            params=params,
            timeout=30,
            headers={
                "User-Agent": "GhostInTheArchive/1.0 (Historical Research Project)",
                "Accept": "application/json",
            },
        )
        response.raise_for_status()
        data = response.json()

        documents = []
        for item in data.get("results", []):
            description = ""
            if isinstance(item.get("description"), list):
                description = " ".join(str(d) for d in item["description"])
            elif isinstance(item.get("description"), str):
                description = item["description"]

            url = item.get("url", item.get("id", ""))
            if url and not url.startswith("http"):
                url = f"https://www.loc.gov{url}"
            if not url:
                continue

            location = _extract_location(item)
            date_str = item.get("date", "")
            if isinstance(date_str, list) and date_str:
                date_str = str(date_str[0])

            doc = ArchiveDocument(
                title=str(item.get("title", "Unknown Title"))[:500],
                date=self.parse_year(str(date_str)),
                source_url=url,
                summary=description[:500] if description else "No description",
                language=_detect_language(description),
                location=location,
                source_type=self.source_type,
                raw_text=description[:5000] if description else None,
                keywords_matched=[
                    kw for kw in keywords if kw.lower() in (description or "").lower()
                ],
            )
            documents.append(doc)

        pagination = data.get("pagination", {})
        total_hits = pagination.get("total", pagination.get("of", 0))

        return ArchiveSearchResult(documents=documents, total_hits=total_hits)


def _extract_location(item: dict) -> str:
    if "location" in item:
        loc = item["location"]
        if isinstance(loc, list):
            return ", ".join(str(el) for el in loc[:2])
        if isinstance(loc, str):
            return loc
    title = item.get("title", "")
    if "(" in title and ")" in title:
        return title[title.find("(") + 1 : title.find(")")]
    return "Unknown"


def _detect_language(text: str) -> SourceLanguage:
    if not text:
        return SourceLanguage.EN
    spanish_indicators = [" el ", " la ", " los ", " las ", " de ", " en ", " que ", " es "]
    text_lower = f" {text.lower()} "
    spanish_count = sum(1 for w in spanish_indicators if w in text_lower)
    return SourceLanguage.ES if spanish_count > 3 else SourceLanguage.EN


# レジストリに自動登録
_instance = LOCDigitalSource()
register_source(_instance)
