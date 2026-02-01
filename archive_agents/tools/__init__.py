"""Tools for Ghost in the Archive agents."""

# Low-level API tools
from .bilingual_search import KEYWORD_PAIRS, expand_keywords_bilingual
from .chronicling_america import search_chronicling_america

# Low-level archive API tools
from .dpla import search_dpla
from .internet_archive import search_internet_archive
from .loc_digital import search_loc_digital
from .nypl_digital import search_nypl
# Librarian Agent LLM-facing tools
from .librarian_tools import (
    get_available_keywords,
    save_search_results,
    search_archives,
    search_newspapers,
)

# Designer Agent LLM-facing tools
from .designer_tools import generate_image

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
    # Low-level archive APIs
    "search_loc_digital",
    "search_dpla",
    "search_nypl",
    "search_internet_archive",
    # Librarian LLM tools
    "search_newspapers",
    "search_archives",
    "save_search_results",
    "get_available_keywords",
    # Designer LLM tools
    "generate_image",
    # Historian LLM tools
    "load_search_results",
    "load_multiple_search_results",
    "build_analysis_context",
    "list_available_results",
    "save_mystery_report",
]
