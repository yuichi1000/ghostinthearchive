"""Europeana Search API tool.

Searches the Europeana aggregated collections from 6,000+ European cultural
heritage institutions (museums, libraries, archives). Uses wskey query
parameter authentication.
"""

import json
import os
import re
import time
from typing import Any, Dict, List, Optional

import requests

from shared.http_retry import create_retry_session

from ..schemas.document import ArchiveDocument, SourceLanguage, SourceType
from .search_utils import build_search_query

BASE_URL = "https://api.europeana.eu/record/v2/search.json"
_session = create_retry_session()
MIN_REQUEST_DELAY = 1.0
_last_request_time = 0.0

# Europeana の language フィールドから SourceLanguage へのマッピング
_LANG_MAP: dict[str, SourceLanguage] = {
    "en": SourceLanguage.EN,
    "es": SourceLanguage.ES,
    "de": SourceLanguage.DE,
    "fr": SourceLanguage.FR,
    "nl": SourceLanguage.NL,
    "pt": SourceLanguage.PT,
}


def _rate_limit() -> None:
    global _last_request_time
    now = time.time()
    elapsed = now - _last_request_time
    if elapsed < MIN_REQUEST_DELAY:
        time.sleep(MIN_REQUEST_DELAY - elapsed)
    _last_request_time = time.time()


def _detect_language(item: dict) -> SourceLanguage:
    """アイテムの language フィールドから SourceLanguage を検出する。"""
    languages = item.get("language", [])
    if isinstance(languages, list):
        for lang in languages:
            if lang and lang.lower() in _LANG_MAP:
                return _LANG_MAP[lang.lower()]
    elif isinstance(languages, str) and languages.lower() in _LANG_MAP:
        return _LANG_MAP[languages.lower()]
    # デフォルトは英語
    return SourceLanguage.EN


def _extract_location(item: dict) -> str:
    """アイテムから場所情報を抽出する。"""
    # edmPlaceLabelLangAware を優先
    place_labels = item.get("edmPlaceLabelLangAware", {})
    if isinstance(place_labels, dict):
        # 英語ラベルを優先、なければ最初の値を使用
        for key in ("en", "def"):
            if key in place_labels and place_labels[key]:
                labels = place_labels[key]
                if isinstance(labels, list) and labels:
                    return str(labels[0])[:200]

    # country フィールドにフォールバック
    country = item.get("country", [])
    if isinstance(country, list) and country:
        return str(country[0])[:200]
    elif isinstance(country, str) and country:
        return country[:200]

    return "Europe"


def _parse_year(date_str: str) -> Optional[str]:
    """年文字列を ISO 日付形式に変換する。"""
    if not date_str:
        return None
    year_match = re.search(r"\b(1[3-9]\d{2}|20\d{2})\b", date_str)
    if year_match:
        return f"{year_match.group(1)}-01-01"
    return date_str[:10] if len(date_str) > 10 else date_str


def search_europeana(
    keywords: List[str],
    date_start: str = "1800",
    date_end: str = "1899",
    max_results: int = 20,
    language: Optional[str] = None,
) -> Dict[str, Any]:
    """Search Europeana for European cultural heritage materials.

    Args:
        keywords: List of search keywords
        date_start: Start year
        date_end: End year
        max_results: Maximum results to return
        language: Optional ISO 639-1 language code for filtering

    Returns:
        Dict with documents, total_hits, error keys.
    """
    api_key = os.environ.get("EUROPEANA_API_KEY", "")
    if not api_key:
        return {"documents": [], "total_hits": 0, "error": "EUROPEANA_API_KEY not set"}

    search_text = build_search_query(keywords)
    if not search_text:
        return {"documents": [], "total_hits": 0, "error": "No keywords provided"}

    params: dict[str, Any] = {
        "wskey": api_key,
        "query": search_text,
        "rows": min(max_results, 100),
        "start": 1,
        "profile": "standard",
    }

    # 日付フィルタ
    qf_list: list[str] = [f"YEAR:[{date_start} TO {date_end}]"]

    # 言語フィルタ
    if language:
        qf_list.append(f"LANGUAGE:{language}")

    params["qf"] = qf_list

    headers = {
        "Accept": "application/json",
        "User-Agent": "GhostInTheArchive/1.0",
    }

    _rate_limit()

    try:
        response = _session.get(
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
                date=_parse_year(str(date_str)),
                source_url=url,
                summary=str(description)[:500] if description else str(title)[:500],
                language=lang,
                location=str(location)[:200],
                source_type=SourceType.EUROPEANA,
                raw_text=str(description)[:5000] if description else None,
                keywords_matched=matched,
            )
            documents.append(doc)

        total_hits = data.get("totalResults", len(documents))
        return {"documents": documents, "total_hits": total_hits, "error": None}

    except (requests.RequestException, json.JSONDecodeError) as e:
        return {"documents": [], "total_hits": 0, "error": f"Europeana API error: {e}"}
