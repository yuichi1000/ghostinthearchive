"""NARA Catalog API tool for searching National Archives records.

Note: The NARA Catalog API v2 requires an API key. Set NARA_API_KEY
environment variable to enable this functionality.
Request an API key from: Catalog_API@nara.gov
"""

import json
import os
import time
from typing import Any, Dict, List, Optional

import requests

from schemas.document import ArchiveDocument, SourceLanguage, SourceType

# Key Record Groups for Spanish/diplomatic records
SPANISH_RECORD_GROUPS: Dict[str, str] = {
    "RG 59": "General Records of the Department of State",
    "RG 45": "Naval Records Collection of the Office of Naval Records and Library",
    "RG 76": "Records of Boundary and Claims Commissions and Arbitrations",
    "RG 84": "Records of the Foreign Service Posts of the Department of State",
    "RG 36": "Records of the U.S. Customs Service",
    "RG 41": "Records of the Bureau of Marine Inspection and Navigation",
    "RG 26": "Records of the U.S. Coast Guard",
}

# NARA API v2 base URL
BASE_URL = "https://catalog.archives.gov/api/v2/"

# Rate limiting
MIN_REQUEST_DELAY = 1.0
_last_request_time = 0.0


def _rate_limit() -> None:
    """Ensure minimum delay between API requests."""
    global _last_request_time
    now = time.time()
    elapsed = now - _last_request_time
    if elapsed < MIN_REQUEST_DELAY:
        time.sleep(MIN_REQUEST_DELAY - elapsed)
    _last_request_time = time.time()


def _get_api_key() -> Optional[str]:
    """Get NARA API key from environment variable."""
    return os.environ.get("NARA_API_KEY")


def search_nara_catalog(
    keywords: List[str],
    record_groups: Optional[List[str]] = None,
    result_types: Optional[List[str]] = None,
    rows: int = 25,
    offset: int = 0,
) -> Dict[str, Any]:
    """Search NARA Catalog for historical records.

    Searches the National Archives catalog for records matching keywords,
    with optional filtering by Record Groups relevant to Spanish/diplomatic history.

    Note: Requires NARA_API_KEY environment variable to be set.
    Request an API key from: Catalog_API@nara.gov

    Args:
        keywords: List of search keywords (supports English and Spanish)
        record_groups: List of Record Group IDs to filter (e.g., ["RG 59", "RG 45"])
        result_types: Types of results to return (default: ["item", "fileUnit"])
        rows: Number of results per page (default: 25, max: 100)
        offset: Starting offset for pagination (default: 0)

    Returns:
        Dictionary containing:
        - documents: List of ArchiveDocument objects
        - total_hits: Total number of matching records
        - offset: Current offset
        - has_more: Boolean indicating if more results exist
        - error: Error message if search failed (None on success)

    Note:
        NARA API has a monthly limit of 10,000 requests per API key.
    """
    api_key = _get_api_key()

    if not api_key:
        # Return a helpful message instead of failing silently
        return {
            "documents": [],
            "total_hits": 0,
            "offset": offset,
            "has_more": False,
            "error": (
                "NARA API key not configured. "
                "Set NARA_API_KEY environment variable. "
                "Request a key from: Catalog_API@nara.gov"
            ),
        }

    if result_types is None:
        result_types = ["item", "fileUnit", "series"]

    rows = min(rows, 100)

    # Build search query
    search_text = " ".join(f'"{kw}"' for kw in keywords if kw.strip())
    if not search_text:
        return {
            "documents": [],
            "total_hits": 0,
            "offset": offset,
            "has_more": False,
            "error": "No keywords provided",
        }

    _rate_limit()

    try:
        # Use v2 API endpoint
        response = requests.get(
            f"{BASE_URL}records/search",
            params={
                "q": search_text,
                "rows": rows,
                "offset": offset,
            },
            timeout=30,
            headers={
                "User-Agent": "GhostInTheArchive/1.0 (Historical Research Project)",
                "Accept": "application/json",
                "x-api-key": api_key,
            },
        )

        # Check for HTML response (API might be unavailable)
        content_type = response.headers.get("content-type", "")
        if "text/html" in content_type:
            return {
                "documents": [],
                "total_hits": 0,
                "offset": offset,
                "has_more": False,
                "error": "NARA API returned HTML instead of JSON. The API may be temporarily unavailable.",
            }

        response.raise_for_status()
        data = response.json()

        documents = []
        results = data.get("results", [])

        if isinstance(results, dict):
            results = [results]
        elif results is None:
            results = []

        for item in results:
            # Extract fields from the response
            title = item.get("title", "Untitled Record")
            description = item.get("scopeContent", "") or item.get("description", "")
            nara_id = item.get("naId", "")

            # Detect language
            combined_text = f"{title} {description}"
            language = _detect_language(combined_text)

            # Extract date
            date_str = item.get("productionDate", "") or item.get("coverageDates", "")

            # Extract record group
            record_group = item.get("recordGroupNumber", "")
            if record_group:
                record_group = f"RG {record_group}"

            doc = ArchiveDocument(
                title=str(title)[:500],
                date=_normalize_date(date_str),
                source_url=f"https://catalog.archives.gov/id/{nara_id}" if nara_id else "",
                summary=str(description)[:500] if description else "No description available",
                language=language,
                location=item.get("creator", "National Archives"),
                source_type=SourceType.NARA_CATALOG,
                record_group=record_group if record_group else None,
                keywords_matched=_find_matched_keywords(combined_text, keywords),
            )
            documents.append(doc)

        total_hits = data.get("total", len(results))

        return {
            "documents": documents,
            "total_hits": total_hits,
            "offset": offset,
            "has_more": (offset + rows) < total_hits,
            "error": None,
        }

    except requests.Timeout:
        return {
            "documents": [],
            "total_hits": 0,
            "offset": offset,
            "has_more": False,
            "error": "Request timed out after 30 seconds",
        }
    except requests.RequestException as e:
        return {
            "documents": [],
            "total_hits": 0,
            "offset": offset,
            "has_more": False,
            "error": f"NARA API request failed: {str(e)}",
        }
    except (json.JSONDecodeError, KeyError, TypeError) as e:
        return {
            "documents": [],
            "total_hits": 0,
            "offset": offset,
            "has_more": False,
            "error": f"Failed to parse NARA response: {str(e)}",
        }


def _detect_language(text: str) -> SourceLanguage:
    """Detect language from text using simple heuristics."""
    if not text:
        return SourceLanguage.EN

    spanish_indicators = [
        "español",
        "spanish",
        "spain",
        "españa",
        "tratado",
        "consulado",
        "cuba",
        "mexico",
        "méxico",
    ]
    text_lower = text.lower()
    for indicator in spanish_indicators:
        if indicator in text_lower:
            return SourceLanguage.ES
    return SourceLanguage.EN


def _normalize_date(date_str: Optional[str]) -> Optional[str]:
    """Normalize various date formats to ISO format."""
    if not date_str:
        return None

    date_str = str(date_str).strip()

    # Handle year-only dates
    if date_str.isdigit() and len(date_str) == 4:
        return f"{date_str}-01-01"

    # Handle date ranges like "1820 - 1825" or "1820-1825"
    if " - " in date_str:
        first_part = date_str.split(" - ")[0].strip()
        if first_part.isdigit() and len(first_part) == 4:
            return f"{first_part}-01-01"

    if "-" in date_str and len(date_str) == 9:  # "1820-1825"
        first_part = date_str.split("-")[0].strip()
        if first_part.isdigit() and len(first_part) == 4:
            return f"{first_part}-01-01"

    return date_str


def _find_matched_keywords(text: str, keywords: List[str]) -> List[str]:
    """Find which keywords appear in the text."""
    if not text:
        return []
    text_lower = text.lower()
    return [kw for kw in keywords if kw.lower() in text_lower]


def get_spanish_record_groups() -> Dict[str, str]:
    """Return the dictionary of Spanish/diplomatic-related Record Groups."""
    return SPANISH_RECORD_GROUPS.copy()
