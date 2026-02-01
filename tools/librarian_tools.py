"""LLM-facing tool functions for the Librarian Agent.

These functions wrap the low-level API tools and provide a simple
string-based interface for the LLM to use.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Optional

from .bilingual_search import KEYWORD_PAIRS, expand_keywords_bilingual
from .chronicling_america import search_chronicling_america
from .dpla import search_dpla
from .internet_archive import search_internet_archive
from .loc_digital import search_loc_digital
from .nypl_digital import search_nypl


def search_newspapers(
    keywords: str,
    date_start: str = "1800",
    date_end: str = "1899",
    states: Optional[str] = None,
    max_results: int = 20,
) -> str:
    """Search historical newspapers in Chronicling America.

    Searches the Library of Congress Chronicling America database for
    18th-19th century newspaper articles. Automatically expands keywords
    to include both English and Spanish variants.

    Args:
        keywords: Comma-separated list of search keywords related to historical mysteries
        date_start: Start year (default: 1800)
        date_end: End year (default: 1899)
        states: Comma-separated US states to search (default: East Coast states)
        max_results: Maximum number of results to return (default: 20)

    Returns:
        JSON string containing search results with documents matching the query
    """
    # Parse keywords
    keyword_list = [kw.strip() for kw in keywords.split(",") if kw.strip()]

    # Expand keywords to bilingual
    expanded = expand_keywords_bilingual(keyword_list)
    all_keywords = expanded["en"] + expanded["es"]

    # Parse states if provided
    state_list = None
    if states:
        state_list = [s.strip() for s in states.split(",") if s.strip()]

    # Perform search
    results = search_chronicling_america(
        keywords=all_keywords,
        date_start=date_start,
        date_end=date_end,
        states=state_list,
        rows=max_results,
    )

    # Convert to JSON-serializable format
    if results["documents"]:
        docs = [doc.model_dump() for doc in results["documents"]]
    else:
        docs = []

    return json.dumps(
        {
            "source": "chronicling_america",
            "keywords_used": all_keywords,
            "total_hits": results["total_hits"],
            "documents_returned": len(docs),
            "documents": docs,
            "error": results.get("error"),
        },
        ensure_ascii=False,
        indent=2,
    )


def save_search_results(
    theme: str,
    results_json: str,
    filename: Optional[str] = None,
) -> str:
    """Save search results to the data directory.

    Saves the collected search results to a JSON file in the data/ directory
    for later processing by the Historian Agent.

    Args:
        theme: The original search theme (e.g., "Spanish ship disappearance in Boston Harbor")
        results_json: JSON string containing all search results
        filename: Optional custom filename (default: auto-generated from timestamp)

    Returns:
        Path to the saved file
    """
    # Find project root (where data/ directory should be)
    data_dir = Path(__file__).parent.parent / "data"
    data_dir.mkdir(exist_ok=True)

    if filename is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        # Create safe filename from theme
        safe_theme = "".join(c if c.isalnum() or c in " _-" else "_" for c in theme[:30])
        safe_theme = safe_theme.replace(" ", "_")
        filename = f"search_{safe_theme}_{timestamp}.json"

    filepath = data_dir / filename

    # Parse and re-structure the results
    try:
        results_data = json.loads(results_json)
    except json.JSONDecodeError:
        results_data = {"raw": results_json}

    output = {
        "theme": theme,
        "search_timestamp": datetime.now().isoformat(),
        "results": results_data,
    }

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    return json.dumps(
        {
            "status": "success",
            "message": "Results saved successfully",
            "filepath": str(filepath),
            "theme": theme,
        },
        ensure_ascii=False,
    )


_ARCHIVE_SOURCES = {
    "loc": ("LOC Digital Collections", search_loc_digital),
    "dpla": ("DPLA", search_dpla),
    "nypl": ("NYPL Digital Collections", search_nypl),
    "internet_archive": ("Internet Archive", search_internet_archive),
}


def search_archives(
    keywords: str,
    date_start: str = "1800",
    date_end: str = "1899",
    sources: Optional[str] = None,
    max_results: int = 10,
) -> str:
    """Search multiple public archive APIs simultaneously.

    Searches across LOC Digital Collections, DPLA, NYPL, and Internet Archive.
    Results are merged and returned as a unified JSON response.

    Unlike search_newspapers, this function does NOT perform bilingual keyword
    expansion. Pass the exact keywords you want to search for.

    Args:
        keywords: Comma-separated search keywords (used as-is, no bilingual expansion)
        date_start: Start year (default: 1800)
        date_end: End year (default: 1899)
        sources: Comma-separated source names to search (default: all).
                 Options: loc, dpla, nypl, internet_archive
        max_results: Max results per source (default: 10)

    Returns:
        JSON string with merged results from all sources.
    """
    keyword_list = [kw.strip() for kw in keywords.split(",") if kw.strip()]
    all_keywords = keyword_list

    if sources:
        source_keys = [s.strip().lower() for s in sources.split(",") if s.strip()]
    else:
        source_keys = list(_ARCHIVE_SOURCES.keys())

    all_docs = []
    source_results = {}
    errors = {}

    for key in source_keys:
        if key not in _ARCHIVE_SOURCES:
            errors[key] = f"Unknown source: {key}"
            continue

        name, search_fn = _ARCHIVE_SOURCES[key]
        try:
            result = search_fn(
                keywords=all_keywords,
                date_start=date_start,
                date_end=date_end,
                max_results=max_results,
            )
            docs = [doc.model_dump() for doc in result.get("documents", [])]
            all_docs.extend(docs)
            source_results[key] = {
                "name": name,
                "total_hits": result.get("total_hits", 0),
                "documents_returned": len(docs),
            }
            if result.get("error"):
                errors[key] = result["error"]
        except Exception as e:
            errors[key] = str(e)
            source_results[key] = {"name": name, "total_hits": 0, "documents_returned": 0}

    return json.dumps(
        {
            "keywords_used": all_keywords,
            "sources_searched": source_results,
            "total_documents": len(all_docs),
            "documents": all_docs,
            "errors": errors if errors else None,
        },
        ensure_ascii=False,
        indent=2,
    )


def get_available_keywords() -> str:
    """Get the list of available bilingual keyword pairs.

    Returns the predefined English-Spanish keyword pairs that can be
    used for searching historical mysteries.

    Returns:
        JSON string containing keyword pairs
    """
    return json.dumps(
        {
            "description": "Available bilingual keyword pairs for historical mystery searches",
            "keyword_pairs": KEYWORD_PAIRS,
            "usage": "Use these keywords to search both English and Spanish sources",
        },
        ensure_ascii=False,
        indent=2,
    )
