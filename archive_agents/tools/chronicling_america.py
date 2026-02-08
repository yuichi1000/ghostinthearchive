"""Chronicling America API tool for searching historical newspapers.

Uses the loc.gov JSON API to search the Chronicling America collection.
"""

import json
import time
from typing import Any, Dict, List, Optional

import requests

from ..schemas.document import ArchiveDocument, SourceLanguage, SourceType

# East Coast states for filtering (lowercase for API)
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

# loc.gov search API base URL
BASE_URL = "https://www.loc.gov/search/"

# Rate limiting: minimum delay between requests (seconds)
MIN_REQUEST_DELAY = 3.0  # Conservative to respect rate limits
_last_request_time = 0.0


def _rate_limit() -> None:
    """Ensure minimum delay between API requests."""
    global _last_request_time
    now = time.time()
    elapsed = now - _last_request_time
    if elapsed < MIN_REQUEST_DELAY:
        time.sleep(MIN_REQUEST_DELAY - elapsed)
    _last_request_time = time.time()


def search_chronicling_america(
    keywords: List[str],
    date_start: str = "1780",
    date_end: str = "1899",
    states: Optional[List[str]] = None,
    page: int = 1,
    rows: int = 20,
) -> Dict[str, Any]:
    """Search Chronicling America for historical newspaper articles.

    Searches the Library of Congress Chronicling America database for
    18th-19th century newspaper articles matching the given keywords.
    Uses the loc.gov search API.

    Args:
        keywords: List of search keywords (supports English and Spanish)
        date_start: Start year (default: 1780)
        date_end: End year (default: 1899)
        states: List of US states to filter (default: East Coast states)
        page: Page number for pagination (default: 1)
        rows: Number of results per page (default: 20, max: 50)

    Returns:
        Dictionary containing:
        - documents: List of ArchiveDocument objects
        - total_hits: Total number of matching records
        - page: Current page number
        - has_more: Boolean indicating if more pages exist
        - error: Error message if search failed (None on success)
    """
    if states is None:
        states = EAST_COAST_STATES

    # Limit rows to reasonable maximum
    rows = min(rows, 50)

    # Build search query - join keywords with OR for broader results
    search_text = " OR ".join(kw for kw in keywords if kw.strip())

    if not search_text:
        return {
            "documents": [],
            "total_hits": 0,
            "page": page,
            "has_more": False,
            "error": "No keywords provided",
        }

    # Build URL parameters for loc.gov search API
    params = {
        "q": search_text,
        "fa": "partof:chronicling america",  # Filter to Chronicling America collection
        "fo": "json",
        "c": rows,  # Count per page
        "sp": page,  # Page number
    }

    # Add date range filter if specified
    # Note: loc.gov uses different date parameter format
    if date_start and date_end:
        # Normalize years
        start_year = date_start[:4] if len(date_start) >= 4 else date_start
        end_year = date_end[:4] if len(date_end) >= 4 else date_end
        params["dates"] = f"{start_year}/{end_year}"

    _rate_limit()

    try:
        response = requests.get(
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
            # Extract description/text content
            description = ""
            if isinstance(item.get("description"), list):
                description = " ".join(str(d) for d in item["description"])
            elif isinstance(item.get("description"), str):
                description = item["description"]

            # Determine language from content heuristics
            language = _detect_language(description)

            # Extract location info from item
            location_parts = []
            # Try to get location from various fields
            if "location" in item:
                loc = item["location"]
                if isinstance(loc, list):
                    location_parts.extend(str(l) for l in loc[:2])
                elif isinstance(loc, str):
                    location_parts.append(loc)

            # Also check for state in other fields
            if not location_parts:
                title = item.get("title", "")
                # Try to extract location from title (often in parentheses)
                if "(" in title and ")" in title:
                    loc_match = title[title.find("(") + 1 : title.find(")")]
                    if loc_match:
                        location_parts.append(loc_match)

            location = ", ".join(location_parts) if location_parts else "Unknown"

            # Extract date
            date_str = item.get("date", "")
            if isinstance(date_str, list) and date_str:
                date_str = str(date_str[0])

            # Get URL
            url = item.get("url", item.get("id", ""))
            if url and not url.startswith("http"):
                url = f"https://www.loc.gov{url}"
            if not url:
                continue

            doc = ArchiveDocument(
                title=str(item.get("title", "Unknown Title"))[:500],
                date=_parse_date(str(date_str)),
                source_url=url,
                summary=_extract_summary(
                    description or str(item.get("title", "")), keywords
                ),
                language=language,
                location=location[:200],
                source_type=SourceType.NEWSPAPER,
                raw_text=description[:5000] if description else None,
                keywords_matched=_find_matched_keywords(
                    description or str(item.get("title", "")), keywords
                ),
            )
            documents.append(doc)

        # Get pagination info
        pagination = data.get("pagination", {})
        total_hits = pagination.get("total", pagination.get("of", 0))
        current_page = pagination.get("current", page)

        return {
            "documents": documents,
            "total_hits": total_hits,
            "page": current_page,
            "has_more": pagination.get("next") is not None,
            "error": None,
        }

    except requests.Timeout:
        return {
            "documents": [],
            "total_hits": 0,
            "page": page,
            "has_more": False,
            "error": "Request timed out after 30 seconds",
        }
    except requests.RequestException as e:
        return {
            "documents": [],
            "total_hits": 0,
            "page": page,
            "has_more": False,
            "error": f"API request failed: {str(e)}",
        }
    except json.JSONDecodeError as e:
        return {
            "documents": [],
            "total_hits": 0,
            "page": page,
            "has_more": False,
            "error": f"Failed to parse API response: {str(e)}",
        }


def _detect_language(text: str) -> SourceLanguage:
    """Detect language from text using simple heuristics."""
    if not text:
        return SourceLanguage.EN

    spanish_indicators = [
        " el ",
        " la ",
        " los ",
        " las ",
        " de ",
        " en ",
        " que ",
        " es ",
        " un ",
        " una ",
    ]
    text_lower = f" {text.lower()} "
    spanish_count = sum(1 for word in spanish_indicators if word in text_lower)
    return SourceLanguage.ES if spanish_count > 3 else SourceLanguage.EN


def _parse_date(date_str: str) -> Optional[str]:
    """Parse date string to ISO format."""
    if not date_str:
        return None

    date_str = str(date_str).strip()

    # Handle YYYYMMDD format
    if len(date_str) == 8 and date_str.isdigit():
        return f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:8]}"

    # Handle YYYY-MM-DD format (already correct)
    if len(date_str) == 10 and date_str[4] == "-" and date_str[7] == "-":
        return date_str

    # Handle year only
    if len(date_str) == 4 and date_str.isdigit():
        return f"{date_str}-01-01"

    # Handle various date formats like "May 5, 1840"
    # Just extract year if possible
    import re

    year_match = re.search(r"\b(1[7-9]\d{2})\b", date_str)
    if year_match:
        return f"{year_match.group(1)}-01-01"

    return date_str[:10] if len(date_str) > 10 else date_str


def _extract_summary(text: str, keywords: List[str]) -> str:
    """Extract a summary by finding context around keywords."""
    if not text:
        return "No content available"

    text_lower = text.lower()
    for keyword in keywords:
        idx = text_lower.find(keyword.lower())
        if idx != -1:
            start = max(0, idx - 100)
            end = min(len(text), idx + 200)
            snippet = text[start:end].strip()
            # Clean up whitespace
            snippet = " ".join(snippet.split())
            return f"...{snippet}..."

    # No keyword found, return beginning of text
    snippet = " ".join(text[:300].split())
    return f"{snippet}..." if len(text) > 300 else snippet


def _find_matched_keywords(text: str, keywords: List[str]) -> List[str]:
    """Find which keywords appear in the text."""
    if not text:
        return []
    text_lower = text.lower()
    return [kw for kw in keywords if kw.lower() in text_lower]
