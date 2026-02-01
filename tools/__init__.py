"""Tools for Ghost in the Archive agents."""

# Low-level API tools
from .bilingual_search import KEYWORD_PAIRS, expand_keywords_bilingual
from .chronicling_america import search_chronicling_america

# Librarian Agent LLM-facing tools
from .librarian_tools import (
    get_available_keywords,
    save_search_results,
    search_newspapers,
)

# Historian Agent LLM-facing tools
from .historian_tools import (
    build_analysis_context,
    list_available_results,
    load_multiple_search_results,
    load_search_results,
    save_mystery_report,
)

__all__ = [
    # Low-level
    "KEYWORD_PAIRS",
    "expand_keywords_bilingual",
    "search_chronicling_america",
    # Librarian LLM tools
    "search_newspapers",
    "save_search_results",
    "get_available_keywords",
    # Historian LLM tools
    "load_search_results",
    "load_multiple_search_results",
    "build_analysis_context",
    "list_available_results",
    "save_mystery_report",
]
