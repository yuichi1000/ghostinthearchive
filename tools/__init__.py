"""Tools for the Librarian Agent."""

# Low-level API tools
from .bilingual_search import KEYWORD_PAIRS, expand_keywords_bilingual
from .chronicling_america import search_chronicling_america
from .nara_catalog import get_spanish_record_groups, search_nara_catalog

# LLM-facing tool functions
from .librarian_tools import (
    get_available_keywords,
    save_search_results,
    search_nara_records,
    search_newspapers,
)

__all__ = [
    # Low-level
    "KEYWORD_PAIRS",
    "expand_keywords_bilingual",
    "search_chronicling_america",
    "search_nara_catalog",
    "get_spanish_record_groups",
    # LLM tools
    "search_newspapers",
    "search_nara_records",
    "save_search_results",
    "get_available_keywords",
]
