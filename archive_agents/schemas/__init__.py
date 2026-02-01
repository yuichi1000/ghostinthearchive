"""Schemas for inter-agent communication."""

from .document import ArchiveDocument, SearchResults, SourceLanguage, SourceType
from .mystery_report import (
    AnalysisResults,
    ConfidenceLevel,
    DiscrepancyType,
    Evidence,
    HistoricalContext,
    MysteryReport,
)

__all__ = [
    # Document schemas (Librarian output)
    "ArchiveDocument",
    "SearchResults",
    "SourceLanguage",
    "SourceType",
    # Mystery Report schemas (Historian output)
    "AnalysisResults",
    "ConfidenceLevel",
    "DiscrepancyType",
    "Evidence",
    "HistoricalContext",
    "MysteryReport",
]
