"""Chronicling America API ソース。

LOC の loc.gov JSON API を使用して Chronicling America 新聞コレクションを検索する。
"""

import json
import re
from typing import Optional

import requests

from ..schemas.document import ArchiveDocument, SourceLanguage
from .archive_source_base import ArchiveSearchResult, ArchiveSource
from .search_utils import build_search_query
from .source_registry import register_source

# 東海岸州リスト（新聞検索のデフォルトフィルタ）
EAST_COAST_STATES = [
    "new york",
    "massachusetts",
    "pennsylvania",
    "connecticut",
    "rhode island",
    "new jersey",
    "maryland",
    "virginia",
    "delaware",
]

BASE_URL = "https://www.loc.gov/search/"


class ChroniclingAmericaSource(ArchiveSource):
    """Chronicling America 新聞コレクションソース。"""

    source_key = "chronicling_america"
    source_name = "Chronicling America"
    source_type = "newspaper"
    min_request_delay = 3.0
    supported_languages = {"en"}
    supports_language_filter = False
    is_newspaper_source = True
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
            "fa": "partof:chronicling america",
            "fo": "json",
            "c": min(max_results, 50),
            "sp": 1,
        }

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
        results = data.get("results", [])

        for item in results:
            description = ""
            if isinstance(item.get("description"), list):
                description = " ".join(str(d) for d in item["description"])
            elif isinstance(item.get("description"), str):
                description = item["description"]

            lang = _detect_language(description)

            location = _extract_location(item)

            date_str = item.get("date", "")
            if isinstance(date_str, list) and date_str:
                date_str = str(date_str[0])

            url = item.get("url", item.get("id", ""))
            if url and not url.startswith("http"):
                url = f"https://www.loc.gov{url}"
            if not url:
                continue

            doc = ArchiveDocument(
                title=str(item.get("title", "Unknown Title"))[:500],
                date=_parse_newspaper_date(str(date_str)),
                source_url=url,
                summary=_extract_summary(
                    description or str(item.get("title", "")), keywords
                ),
                language=lang,
                location=location[:200],
                source_type=self.source_type,
                raw_text=description[:5000] if description else None,
                keywords_matched=_find_matched_keywords(
                    description or str(item.get("title", "")), keywords
                ),
            )
            documents.append(doc)

        pagination = data.get("pagination", {})
        total_hits = pagination.get("total", pagination.get("of", 0))

        return ArchiveSearchResult(documents=documents, total_hits=total_hits)


def search_chronicling_america(
    keywords: list[str],
    date_start: str = "1780",
    date_end: str = "1899",
    states: list[str] | None = None,
    page: int = 1,
    rows: int = 20,
) -> dict:
    """Chronicling America を検索する関数（search_newspapers から使用）。

    states フィルタリングなど search_newspapers 固有のロジック用に残す。
    内部的には ChroniclingAmericaSource を使用する。
    """
    result = _instance.search(
        keywords=keywords,
        date_start=date_start,
        date_end=date_end,
        max_results=min(rows, 50),
    )
    return {
        "documents": result.documents,
        "total_hits": result.total_hits,
        "page": page,
        "has_more": False,
        "error": result.error,
    }


def _detect_language(text: str) -> SourceLanguage:
    """テキストから言語を簡易判定する。"""
    if not text:
        return SourceLanguage.EN
    spanish_indicators = [
        " el ", " la ", " los ", " las ", " de ",
        " en ", " que ", " es ", " un ", " una ",
    ]
    text_lower = f" {text.lower()} "
    spanish_count = sum(1 for word in spanish_indicators if word in text_lower)
    return SourceLanguage.ES if spanish_count > 3 else SourceLanguage.EN


def _parse_newspaper_date(date_str: str) -> str | None:
    """新聞日付文字列を ISO 形式にパースする。"""
    if not date_str:
        return None
    date_str = str(date_str).strip()

    # YYYYMMDD 形式
    if len(date_str) == 8 and date_str.isdigit():
        return f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:8]}"

    # YYYY-MM-DD 形式（そのまま）
    if len(date_str) == 10 and date_str[4] == "-" and date_str[7] == "-":
        return date_str

    # 年のみ
    if len(date_str) == 4 and date_str.isdigit():
        return f"{date_str}-01-01"

    # 年を抽出
    year_match = re.search(r"\b(1[7-9]\d{2})\b", date_str)
    if year_match:
        return f"{year_match.group(1)}-01-01"

    return date_str[:10] if len(date_str) > 10 else date_str


def _extract_location(item: dict) -> str:
    """アイテムから場所情報を抽出する。"""
    location_parts = []
    if "location" in item:
        loc = item["location"]
        if isinstance(loc, list):
            location_parts.extend(str(el) for el in loc[:2])
        elif isinstance(loc, str):
            location_parts.append(loc)

    if not location_parts:
        title = item.get("title", "")
        if "(" in title and ")" in title:
            loc_match = title[title.find("(") + 1 : title.find(")")]
            if loc_match:
                location_parts.append(loc_match)

    return ", ".join(location_parts) if location_parts else "Unknown"


def _extract_summary(text: str, keywords: list[str]) -> str:
    """キーワード周辺のコンテキストからサマリーを抽出する。"""
    if not text:
        return "No content available"

    text_lower = text.lower()
    for keyword in keywords:
        idx = text_lower.find(keyword.lower())
        if idx != -1:
            start = max(0, idx - 100)
            end = min(len(text), idx + 200)
            snippet = text[start:end].strip()
            snippet = " ".join(snippet.split())
            return f"...{snippet}..."

    snippet = " ".join(text[:300].split())
    return f"{snippet}..." if len(text) > 300 else snippet


def _find_matched_keywords(text: str, keywords: list[str]) -> list[str]:
    """テキスト中に出現するキーワードを検出する。"""
    if not text:
        return []
    text_lower = text.lower()
    return [kw for kw in keywords if kw.lower() in text_lower]


# レジストリに自動登録
_instance = ChroniclingAmericaSource()
register_source(_instance)
