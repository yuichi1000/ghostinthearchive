"""Europeana REST API tool.

Searches Europeana's aggregated collections from cultural heritage
institutions across Europe.
"""

import json
import os
import time
from typing import Any, Dict, List, Optional

import requests

from ..schemas.document import ArchiveDocument, SourceLanguage, SourceType

BASE_URL = "https://api.europeana.eu/record/v2/search.json"
MIN_REQUEST_DELAY = 1.0
_last_request_time = 0.0

# Europeana LANGUAGE クエリフィルタ用の ISO 639-1/3 マッピング
_EUROPEANA_LANG_CODES = {
    "en": "en",
    "de": "de",
    "fr": "fr",
    "nl": "nl",
    "pt": "pt",
    "es": "es",
}


def _rate_limit() -> None:
    global _last_request_time
    now = time.time()
    elapsed = now - _last_request_time
    if elapsed < MIN_REQUEST_DELAY:
        time.sleep(MIN_REQUEST_DELAY - elapsed)
    _last_request_time = time.time()


def search_europeana(
    keywords: List[str],
    date_start: str = "1800",
    date_end: str = "1899",
    max_results: int = 20,
    language: Optional[str] = None,
) -> Dict[str, Any]:
    """Search Europeana for historical materials.

    Args:
        keywords: List of search keywords
        date_start: Start year
        date_end: End year
        max_results: Maximum results to return
        language: Optional ISO 639-1 language code to filter results

    Returns:
        Dict with documents, total_hits, error keys.
    """
    api_key = os.environ.get("EUROPEANA_API_KEY", "")
    if not api_key:
        return {"documents": [], "total_hits": 0, "error": "EUROPEANA_API_KEY not set"}

    search_text = " OR ".join(kw for kw in keywords if kw.strip())
    if not search_text:
        return {"documents": [], "total_hits": 0, "error": "No keywords provided"}

    start_year = date_start[:4] if len(date_start) >= 4 else date_start
    end_year = date_end[:4] if len(date_end) >= 4 else date_end

    params = {
        "query": search_text,
        "wskey": api_key,
        "rows": min(max_results, 100),
        "start": 1,
        "profile": "standard",
    }

    # 日付範囲フィルタ
    qf_filters = [f"when:[{start_year} TO {end_year}]"]

    # 言語フィルタ
    if language and language in _EUROPEANA_LANG_CODES:
        qf_filters.append(f"LANGUAGE:{_EUROPEANA_LANG_CODES[language]}")

    if qf_filters:
        params["qf"] = qf_filters

    _rate_limit()

    try:
        response = requests.get(
            BASE_URL,
            params=params,
            timeout=30,
            headers={"User-Agent": "GhostInTheArchive/1.0"},
        )
        response.raise_for_status()
        data = response.json()

        documents = []
        for item in data.get("items", []):
            title = _extract_first(item.get("title", ["Unknown Title"]))
            description = _extract_first(item.get("dcDescription", [""]))

            url = item.get("guid", item.get("edmIsShownAt", [""])[0] if item.get("edmIsShownAt") else "")
            if not url:
                continue

            # 日付の取得
            date_str = ""
            year = item.get("year", [])
            if year:
                date_str = str(year[0]) if isinstance(year, list) else str(year)

            # 言語判定
            item_lang = item.get("dcLanguage", [])
            if isinstance(item_lang, list) and item_lang:
                item_lang = str(item_lang[0])
            else:
                item_lang = str(item_lang) if item_lang else ""
            lang = _detect_europeana_language(item_lang)

            # 場所の取得
            location = "Europe"
            spatial = item.get("edmPlaceLabel", item.get("dcCoverage", []))
            if spatial:
                loc_val = spatial[0] if isinstance(spatial, list) else spatial
                if isinstance(loc_val, dict):
                    location = loc_val.get("def", [location])[0] if "def" in loc_val else location
                elif isinstance(loc_val, str):
                    location = loc_val

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

        total_hits = data.get("totalResults", 0)
        return {"documents": documents, "total_hits": total_hits, "error": None}

    except (requests.RequestException, json.JSONDecodeError) as e:
        return {"documents": [], "total_hits": 0, "error": f"Europeana API error: {e}"}


def _extract_first(value: Any) -> str:
    """リストまたは文字列から最初の値を取得する。"""
    if isinstance(value, list):
        return str(value[0]) if value else ""
    return str(value) if value else ""


def _detect_europeana_language(lang_str: str) -> SourceLanguage:
    """Europeana の言語コードから SourceLanguage を判定する。"""
    lower = lang_str.lower().strip()
    for code in _EUROPEANA_LANG_CODES:
        if lower == code or lower.startswith(code):
            try:
                return SourceLanguage(code)
            except ValueError:
                break
    return SourceLanguage.EN


def _parse_year(date_str: str) -> Optional[str]:
    if not date_str:
        return None
    import re
    year_match = re.search(r"\b(1[3-9]\d{2}|20\d{2})\b", date_str)
    if year_match:
        return f"{year_match.group(1)}-01-01"
    return date_str[:10] if len(date_str) > 10 else date_str
