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


_LANG_CODE_MAP = {
    "en": ["eng", "english"],
    "es": ["spa", "spanish", "español"],
    "de": ["ger", "deu", "german", "deutsch"],
    "fr": ["fre", "fra", "french", "français"],
    "nl": ["dut", "nld", "dutch", "nederlands"],
    "pt": ["por", "portuguese", "português"],
}


def search_internet_archive(
    keywords: List[str],
    date_start: str = "1800",
    date_end: str = "1899",
    max_results: int = 20,
    language: Optional[str] = None,
) -> Dict[str, Any]:
    """Search Internet Archive for historical materials.

    Args:
        keywords: List of search keywords
        date_start: Start year
        date_end: End year
        max_results: Maximum results to return
        language: Optional ISO 639-1 language code (en, de, fr, etc.) to filter results

    Returns:
        Dict with documents, total_hits, error keys.
    """
    search_text = " OR ".join(kw for kw in keywords if kw.strip())
    if not search_text:
        return {"documents": [], "total_hits": 0, "error": "No keywords provided"}

    start_year = date_start[:4] if len(date_start) >= 4 else date_start
    end_year = date_end[:4] if len(date_end) >= 4 else date_end

    query = f"({search_text}) AND date:[{start_year}-01-01 TO {end_year}-12-31]"

    # 言語フィルタ: ocr_detected_lang または language メタデータで絞り込み
    if language and language in _LANG_CODE_MAP:
        lang_codes = _LANG_CODE_MAP[language]
        lang_filter = " OR ".join(f'language:"{code}"' for code in lang_codes)
        query = f"{query} AND ({lang_filter})"

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

            item_language = item.get("language", "")
            if isinstance(item_language, list) and item_language:
                item_language = str(item_language[0])
            lang = _detect_source_language(str(item_language))

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


def _detect_source_language(lang_str: str) -> SourceLanguage:
    """メタデータの言語文字列から SourceLanguage を判定する。"""
    lower = lang_str.lower()
    for lang_code, identifiers in _LANG_CODE_MAP.items():
        for ident in identifiers:
            if ident in lower:
                try:
                    return SourceLanguage(lang_code)
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
