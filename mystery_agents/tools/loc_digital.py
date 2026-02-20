"""Library of Congress Digital Collections API tool.

Uses the loc.gov JSON API to search across all LOC digital collections
(not just Chronicling America newspapers).
"""

import json
import logging
import time
from typing import Any, Dict, List, Optional

import requests

from shared.http_retry import create_retry_session

logger = logging.getLogger(__name__)

from ..schemas.document import ArchiveDocument, SourceLanguage, SourceType
from .search_utils import build_search_query

BASE_URL = "https://www.loc.gov/search/"
_session = create_retry_session()
MIN_REQUEST_DELAY = 3.0
_last_request_time = 0.0


def _rate_limit() -> None:
    global _last_request_time
    now = time.time()
    elapsed = now - _last_request_time
    if elapsed < MIN_REQUEST_DELAY:
        time.sleep(MIN_REQUEST_DELAY - elapsed)
    _last_request_time = time.time()


def search_loc_digital(
    keywords: List[str],
    date_start: str = "1800",
    date_end: str = "1899",
    max_results: int = 20,
) -> Dict[str, Any]:
    """Search LOC Digital Collections (excluding Chronicling America).

    Args:
        keywords: List of search keywords
        date_start: Start year
        date_end: End year
        max_results: Maximum results to return

    Returns:
        Dict with documents, total_hits, error keys.
    """
    search_text = build_search_query(keywords)
    if not search_text:
        return {"documents": [], "total_hits": 0, "error": "No keywords provided"}

    start_year = date_start[:4] if len(date_start) >= 4 else date_start
    end_year = date_end[:4] if len(date_end) >= 4 else date_end

    params = {
        "q": search_text,
        "fa": "not:partof:chronicling america",  # Exclude Chronicling America (searched separately)
        "fo": "json",
        "c": min(max_results, 50),
        "sp": 1,
        "dates": f"{start_year}/{end_year}",
    }

    _rate_limit()
    start = time.monotonic()

    try:
        response = _session.get(
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
                date=_parse_year(str(date_str)),
                source_url=url,
                summary=description[:500] if description else "No description",
                language=_detect_language(description),
                location=location,
                source_type=SourceType.LOC_DIGITAL,
                raw_text=description[:5000] if description else None,
                keywords_matched=[kw for kw in keywords if kw.lower() in (description or "").lower()],
            )
            documents.append(doc)

        pagination = data.get("pagination", {})
        total_hits = pagination.get("total", pagination.get("of", 0))

        latency_ms = round((time.monotonic() - start) * 1000)
        logger.info(
            "LOC 検索完了: %d 件 (%dms)", len(documents), latency_ms,
            extra={"api_name": "loc", "result_count": len(documents),
                   "total_hits": total_hits, "latency_ms": latency_ms},
        )

        return {"documents": documents, "total_hits": total_hits, "error": None}

    except (requests.RequestException, json.JSONDecodeError) as e:
        latency_ms = round((time.monotonic() - start) * 1000)
        logger.warning(
            "LOC API エラー: %s (%dms)", e, latency_ms,
            extra={"api_name": "loc", "latency_ms": latency_ms, "error": str(e)},
        )
        return {"documents": [], "total_hits": 0, "error": f"LOC API error: {e}"}


def _extract_location(item: Dict) -> str:
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


def _parse_year(date_str: str) -> Optional[str]:
    if not date_str:
        return None
    import re
    year_match = re.search(r"\b(1[5-9]\d{2}|20\d{2})\b", date_str)
    if year_match:
        return f"{year_match.group(1)}-01-01"
    return date_str[:10] if len(date_str) > 10 else date_str


def _detect_language(text: str) -> SourceLanguage:
    if not text:
        return SourceLanguage.EN
    spanish_indicators = [" el ", " la ", " los ", " las ", " de ", " en ", " que ", " es "]
    text_lower = f" {text.lower()} "
    spanish_count = sum(1 for w in spanish_indicators if w in text_lower)
    return SourceLanguage.ES if spanish_count > 3 else SourceLanguage.EN
