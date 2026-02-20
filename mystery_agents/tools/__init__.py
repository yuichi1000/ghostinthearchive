"""Tools for Ghost in the Archive agents."""

# Low-level API tools
from .bilingual_search import KEYWORD_PAIRS, expand_keywords_bilingual
from .chronicling_america import search_chronicling_america

# Low-level archive API tools
from .dpla import search_dpla
from .internet_archive import search_internet_archive
from .loc_digital import search_loc_digital
from .nypl_digital import search_nypl
from .ddb import search_ddb
from .europeana import search_europeana

# Librarian Agent LLM-facing tools
from .librarian_tools import (
    get_available_keywords,
    save_search_results,
    search_archives,
    search_newspapers,
)

# Illustrator Agent LLM-facing tools
from .illustrator_tools import generate_image, resize_image_variants, validate_image

# Scholar Agent LLM-facing tools
from .scholar_tools import (
    build_analysis_context,
    list_available_results,
    load_multiple_search_results,
    load_search_results,
    save_mystery_report,
    save_structured_report,
)

# Debate tools
from .debate_tools import append_to_whiteboard

# ThemeAnalyzer Agent LLM-facing tools
from .theme_analyzer_tools import save_language_selection

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
    "search_ddb",
    "search_europeana",
    # Librarian LLM tools
    "search_newspapers",
    "search_archives",
    "save_search_results",
    "get_available_keywords",
    # Illustrator LLM tools
    "generate_image",
    "resize_image_variants",
    "validate_image",
    # Scholar LLM tools
    "load_search_results",
    "load_multiple_search_results",
    "build_analysis_context",
    "list_available_results",
    "save_mystery_report",
    "save_structured_report",
    # Debate tools
    "append_to_whiteboard",
    # ThemeAnalyzer LLM tools
    "save_language_selection",
]
