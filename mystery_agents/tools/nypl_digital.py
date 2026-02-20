"""NYPL Digital Collections API tool.

Searches the New York Public Library's digitized collections
including manuscripts, maps, photographs, and rare materials.
"""

import json
import logging
import os
import time
from typing import Any, Dict, List, Optional

import requests

from shared.http_retry import create_retry_session

logger = logging.getLogger(__name__)

from ..schemas.document import ArchiveDocument, SourceLanguage, SourceType
from .search_utils import build_search_query

BASE_URL = "https://api.repo.nypl.org/api/v2/items/search"
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


def search_nypl(
    keywords: List[str],
    date_start: str = "1800",
    date_end: str = "1899",
    max_results: int = 20,
) -> Dict[str, Any]:
    """Search NYPL Digital Collections.

    Args:
        keywords: List of search keywords
        date_start: Start year
        date_end: End year
        max_results: Maximum results to return

    Returns:
        Dict with documents, total_hits, error keys.
    """
    api_token = os.environ.get("NYPL_API_TOKEN", "")
    if not api_token:
        return {"documents": [], "total_hits": 0, "error": "NYPL_API_TOKEN not set"}

    search_text = build_search_query(keywords)
    if not search_text:
        return {"documents": [], "total_hits": 0, "error": "No keywords provided"}

    # Include date range in query for filtering
    start_year = date_start[:4] if len(date_start) >= 4 else date_start
    end_year = date_end[:4] if len(date_end) >= 4 else date_end
    search_text_with_date = f"{search_text} {start_year}-{end_year}"

    params = {
        "q": search_text_with_date,
        "per_page": min(max_results, 100),
        "page": 1,
        "publicDomainOnly": "true",
    }

    _rate_limit()
    start = time.monotonic()

    try:
        response = _session.get(
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
                date=_parse_year(str(date_str)),
                source_url=url,
                summary=str(title)[:500],
                language=SourceLanguage.EN,
                location="New York",
                source_type=SourceType.NYPL,
                raw_text=None,
                keywords_matched=[kw for kw in keywords if kw.lower() in str(title).lower()],
            )
            documents.append(doc)

        total_hits = int(nypl_response.get("numResults", 0))

        latency_ms = round((time.monotonic() - start) * 1000)
        logger.info(
            "NYPL 検索完了: %d 件 (%dms)", len(documents), latency_ms,
            extra={"api_name": "nypl", "result_count": len(documents),
                   "total_hits": total_hits, "latency_ms": latency_ms},
        )

        return {"documents": documents, "total_hits": total_hits, "error": None}

    except (requests.RequestException, json.JSONDecodeError, ValueError) as e:
        latency_ms = round((time.monotonic() - start) * 1000)
        logger.warning(
            "NYPL API エラー: %s (%dms)", e, latency_ms,
            extra={"api_name": "nypl", "latency_ms": latency_ms, "error": str(e)},
        )
        return {"documents": [], "total_hits": 0, "error": f"NYPL API error: {e}"}


def _parse_year(date_str: str) -> Optional[str]:
    if not date_str:
        return None
    import re
    year_match = re.search(r"\b(1[5-9]\d{2}|20\d{2})\b", date_str)
    if year_match:
        return f"{year_match.group(1)}-01-01"
    return date_str[:10] if len(date_str) > 10 else date_str
