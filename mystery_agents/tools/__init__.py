"""Tools for Ghost in the Archive agents."""

# アーカイブソース基盤
from .archive_source_base import ArchiveSearchResult, ArchiveSource
from .source_registry import (
    get_all_sources,
    get_source,
    register_source,
    resolve_newspaper_sources,
    resolve_sources,
)

# Low-level API tools
from .bilingual_search import KEYWORD_PAIRS, expand_keywords_bilingual
from .chronicling_america import search_chronicling_america

# Librarian Agent LLM-facing tools
from .librarian_tools import (
    get_available_keywords,
    save_search_results,
    search_archives,
    search_newspapers,
)

# Illustrator Agent LLM-facing tools
from .illustrator_tools import generate_image, validate_image
from .image_processing import resize_image_variants

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

# Search metadata tool
from .search_metadata import get_search_metadata

# Word count tool
from .word_count import count_words

__all__ = [
    # アーカイブソース基盤
    "ArchiveSource",
    "ArchiveSearchResult",
    "register_source",
    "get_source",
    "get_all_sources",
    "resolve_sources",
    "resolve_newspaper_sources",
    # Low-level
    "KEYWORD_PAIRS",
    "expand_keywords_bilingual",
    "search_chronicling_america",
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
    # Search metadata tool
    "get_search_metadata",
    # Word count tool
    "count_words",
]
