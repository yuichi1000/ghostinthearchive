"""Digital Public Library of America (DPLA) API tool.

Searches the DPLA aggregated collections from libraries, archives,
and museums across the United States.
"""

import json
import os
import time
from typing import Any, Dict, List, Optional

import requests

from shared.http_retry import create_retry_session

from ..schemas.document import ArchiveDocument, SourceLanguage, SourceType
from .search_utils import build_search_query

BASE_URL = "https://api.dp.la/v2/items"
_session = create_retry_session()
MIN_REQUEST_DELAY = 1.0
_last_request_time = 0.0


def _rate_limit() -> None:
    global _last_request_time
    now = time.time()
    elapsed = now - _last_request_time
    if elapsed < MIN_REQUEST_DELAY:
        time.sleep(MIN_REQUEST_DELAY - elapsed)
    _last_request_time = time.time()


# DPLA sourceResource.language.name で使われる言語名マッピング
_DPLA_LANG_NAMES = {
    "en": ["English"],
    "es": ["Spanish", "Español"],
    "de": ["German", "Deutsch"],
    "fr": ["French", "Français"],
    "nl": ["Dutch", "Nederlands"],
    "pt": ["Portuguese", "Português"],
}


def search_dpla(
    keywords: List[str],
    date_start: str = "1800",
    date_end: str = "1899",
    max_results: int = 20,
    language: Optional[str] = None,
) -> Dict[str, Any]:
    """Search DPLA for historical documents.

    Args:
        keywords: List of search keywords
        date_start: Start year
        date_end: End year
        max_results: Maximum results to return
        language: Optional ISO 639-1 language code to filter by sourceResource.language.name

    Returns:
        Dict with documents, total_hits, error keys.
    """
    api_key = os.environ.get("DPLA_API_KEY", "")
    if not api_key:
        return {"documents": [], "total_hits": 0, "error": "DPLA_API_KEY not set"}

    search_text = build_search_query(keywords)
    if not search_text:
        return {"documents": [], "total_hits": 0, "error": "No keywords provided"}

    start_year = date_start[:4] if len(date_start) >= 4 else date_start
    end_year = date_end[:4] if len(date_end) >= 4 else date_end

    params = {
        "q": search_text,
        "api_key": api_key,
        "page_size": min(max_results, 100),
        "sourceResource.date.after": start_year,
        "sourceResource.date.before": end_year,
    }

    # 言語フィルタ: sourceResource.language.name で絞り込み
    if language and language in _DPLA_LANG_NAMES:
        params["sourceResource.language.name"] = _DPLA_LANG_NAMES[language][0]

    _rate_limit()

    try:
        response = _session.get(
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
                date_str = d.get("displayDate", d.get("begin", "")) if isinstance(d, dict) else str(d)

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
                lang_name = lang_val.get("name", "") if isinstance(lang_val, dict) else str(lang_val)
                lang = _detect_dpla_language(lang_name)

            url = item.get("isShownAt", item.get("@id", ""))
            if not url:
                continue

            doc = ArchiveDocument(
                title=str(title)[:500],
                date=_parse_year(str(date_str)),
                source_url=url,
                summary=str(description)[:500] if description else "No description",
                language=lang,
                location=str(location)[:200],
                source_type=SourceType.DPLA,
                raw_text=str(description)[:5000] if description else None,
                keywords_matched=[kw for kw in keywords if kw.lower() in str(description).lower() or kw.lower() in str(title).lower()],
            )
            documents.append(doc)

        total_hits = data.get("count", 0)
        return {"documents": documents, "total_hits": total_hits, "error": None}

    except (requests.RequestException, json.JSONDecodeError) as e:
        return {"documents": [], "total_hits": 0, "error": f"DPLA API error: {e}"}


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


def _parse_year(date_str: str) -> Optional[str]:
    if not date_str:
        return None
    import re
    year_match = re.search(r"\b(1[5-9]\d{2}|20\d{2})\b", date_str)
    if year_match:
        return f"{year_match.group(1)}-01-01"
    return date_str[:10] if len(date_str) > 10 else date_str
