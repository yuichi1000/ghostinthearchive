"""Internet Archive (Archive.org) Search API tool.

Searches the Internet Archive's vast collection of books, magazines,
web pages, and other digitized materials.
"""

import json
import time
from typing import Any, Dict, List, Optional

import requests

from ..schemas.document import ArchiveDocument, SourceLanguage, SourceType

BASE_URL = "https://archive.org/advancedsearch.php"
MIN_REQUEST_DELAY = 2.0
_last_request_time = 0.0


def _rate_limit() -> None:
    global _last_request_time
    now = time.time()
    elapsed = now - _last_request_time
    if elapsed < MIN_REQUEST_DELAY:
        time.sleep(MIN_REQUEST_DELAY - elapsed)
    _last_request_time = time.time()


def search_internet_archive(
    keywords: List[str],
    date_start: str = "1800",
    date_end: str = "1899",
    max_results: int = 20,
) -> Dict[str, Any]:
    """Search Internet Archive for historical materials.

    Args:
        keywords: List of search keywords
        date_start: Start year
        date_end: End year
        max_results: Maximum results to return

    Returns:
        Dict with documents, total_hits, error keys.
    """
    search_text = " OR ".join(kw for kw in keywords if kw.strip())
    if not search_text:
        return {"documents": [], "total_hits": 0, "error": "No keywords provided"}

    start_year = date_start[:4] if len(date_start) >= 4 else date_start
    end_year = date_end[:4] if len(date_end) >= 4 else date_end

    query = f"({search_text}) AND date:[{start_year}-01-01 TO {end_year}-12-31]"

    params = {
        "q": query,
        "fl[]": ["identifier", "title", "description", "date", "language", "subject", "creator"],
        "sort[]": "date asc",
        "rows": min(max_results, 100),
        "page": 1,
        "output": "json",
    }

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

        resp = data.get("response", {})
        documents = []

        for item in resp.get("docs", []):
            title = item.get("title", "Unknown Title")
            if isinstance(title, list):
                title = title[0] if title else "Unknown Title"

            description = item.get("description", "")
            if isinstance(description, list):
                description = " ".join(str(d) for d in description)

            identifier = item.get("identifier", "")
            url = f"https://archive.org/details/{identifier}" if identifier else ""
            if not url:
                continue

            date_str = item.get("date", "")
            if isinstance(date_str, list) and date_str:
                date_str = str(date_str[0])

            language = item.get("language", "")
            if isinstance(language, list) and language:
                language = str(language[0])
            lang = SourceLanguage.ES if "spa" in str(language).lower() or "spanish" in str(language).lower() else SourceLanguage.EN

            combined = f"{title} {description}".lower()
            matched = [kw for kw in keywords if kw.lower() in combined]

            doc = ArchiveDocument(
                title=str(title)[:500],
                date=_parse_year(str(date_str)),
                source_url=url,
                summary=str(description)[:500] if description else str(title)[:500],
                language=lang,
                location="Unknown",
                source_type=SourceType.INTERNET_ARCHIVE,
                raw_text=str(description)[:5000] if description else None,
                keywords_matched=matched,
            )
            documents.append(doc)

        total_hits = resp.get("numFound", 0)
        return {"documents": documents, "total_hits": total_hits, "error": None}

    except (requests.RequestException, json.JSONDecodeError) as e:
        return {"documents": [], "total_hits": 0, "error": f"Internet Archive API error: {e}"}


def _parse_year(date_str: str) -> Optional[str]:
    if not date_str:
        return None
    import re
    year_match = re.search(r"\b(1[3-9]\d{2}|20\d{2})\b", date_str)
    if year_match:
        return f"{year_match.group(1)}-01-01"
    return date_str[:10] if len(date_str) > 10 else date_str
