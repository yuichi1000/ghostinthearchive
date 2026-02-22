"""Europeana Search API ソース。

Europeana の集約コレクション（6,000+ の欧州文化遺産機関）を検索する。
wskey クエリパラメータ認証を使用。
"""

import os
import re
from typing import Any, Optional

import requests

from ..schemas.document import ArchiveDocument, SourceLanguage
from .archive_source_base import ArchiveSearchResult, ArchiveSource
from .search_utils import build_search_query
from .source_registry import register_source

BASE_URL = "https://api.europeana.eu/record/v2/search.json"

# Europeana の language フィールドから SourceLanguage へのマッピング
_LANG_MAP: dict[str, SourceLanguage] = {
    "en": SourceLanguage.EN,
    "es": SourceLanguage.ES,
    "de": SourceLanguage.DE,
    "fr": SourceLanguage.FR,
    "nl": SourceLanguage.NL,
    "pt": SourceLanguage.PT,
}


class EuropeanaSource(ArchiveSource):
    """Europeana ソース。"""

    source_key = "europeana"
    source_name = "Europeana"
    source_type = "europeana"
    min_request_delay = 1.0
    supported_languages = {"de", "es", "fr", "nl", "pt"}
    supports_language_filter = True
    is_newspaper_source = False
    expected_domains = ["europeana.eu"]
    env_var_key = "EUROPEANA_API_KEY"

    def _search_impl(
        self,
        keywords: list[str],
        date_start: str | None,
        date_end: str | None,
        max_results: int,
        language: str | None,
    ) -> ArchiveSearchResult:
        api_key = os.environ.get("EUROPEANA_API_KEY", "")

        search_text = build_search_query(keywords)
        if not search_text:
            return ArchiveSearchResult(error="No keywords provided")

        params: dict[str, Any] = {
            "wskey": api_key,
            "query": search_text,
            "rows": min(max_results, 100),
            "start": 1,
            "profile": "standard",
        }

        # 空文字日付対応: フィルタを条件付きに
        qf_list: list[str] = []
        if date_start and date_end:
            qf_list.append(f"YEAR:[{date_start} TO {date_end}]")
        if language:
            qf_list.append(f"LANGUAGE:{language}")
        if qf_list:
            params["qf"] = qf_list

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
        data = response.json()

        documents = []
        items = data.get("items", [])

        for item in items:
            # タイトル抽出
            title = item.get("title", ["Unknown Title"])
            if isinstance(title, list):
                title = title[0] if title else "Unknown Title"

            # 説明文抽出
            description = ""
            dc_description = item.get("dcDescription", [])
            if isinstance(dc_description, list) and dc_description:
                description = str(dc_description[0])
            elif isinstance(dc_description, str):
                description = dc_description

            # URL 抽出（guid を優先、edmIsShownAt にフォールバック）
            url = item.get("guid", "")
            if not url:
                shown_at = item.get("edmIsShownAt", [])
                if isinstance(shown_at, list) and shown_at:
                    url = str(shown_at[0])
                elif isinstance(shown_at, str):
                    url = shown_at
            if not url:
                continue

            # 日付抽出
            date_str = ""
            year = item.get("year", [])
            if isinstance(year, list) and year:
                date_str = str(year[0])
            elif isinstance(year, str):
                date_str = year

            # 言語検出
            lang = _detect_language(item)

            # 場所抽出
            location = _extract_location(item)

            # キーワードマッチ
            combined = f"{title} {description}".lower()
            matched = [kw for kw in keywords if kw.lower() in combined]

            doc = ArchiveDocument(
                title=str(title)[:500],
                date=self.parse_year(str(date_str), min_century=13),
                source_url=url,
                summary=str(description)[:500] if description else str(title)[:500],
                language=lang,
                location=str(location)[:200],
                source_type=self.source_type,
                raw_text=str(description)[:5000] if description else None,
                keywords_matched=matched,
            )
            documents.append(doc)

        total_hits = data.get("totalResults", len(documents))
        return ArchiveSearchResult(documents=documents, total_hits=total_hits)


def _detect_language(item: dict) -> SourceLanguage:
    """アイテムの language フィールドから SourceLanguage を検出する。"""
    languages = item.get("language", [])
    if isinstance(languages, list):
        for lang in languages:
            if lang and lang.lower() in _LANG_MAP:
                return _LANG_MAP[lang.lower()]
    elif isinstance(languages, str) and languages.lower() in _LANG_MAP:
        return _LANG_MAP[languages.lower()]
    return SourceLanguage.EN


def _extract_location(item: dict) -> str:
    """アイテムから場所情報を抽出する。"""
    place_labels = item.get("edmPlaceLabelLangAware", {})
    if isinstance(place_labels, dict):
        for key in ("en", "def"):
            if key in place_labels and place_labels[key]:
                labels = place_labels[key]
                if isinstance(labels, list) and labels:
                    return str(labels[0])[:200]

    country = item.get("country", [])
    if isinstance(country, list) and country:
        return str(country[0])[:200]
    elif isinstance(country, str) and country:
        return country[:200]

    return "Europe"


# レジストリに自動登録
_instance = EuropeanaSource()
register_source(_instance)
