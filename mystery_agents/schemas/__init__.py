"""Schemas for inter-agent communication."""

from .document import ArchiveDocument, SearchResults, SourceLanguage, SourceType
from .mystery_id import (
    CLASSIFICATION_DESCRIPTIONS,
    CLASSIFICATION_DESCRIPTIONS_EN,
    REGION_CODES,
    ClassificationCode,
    parse_mystery_id,
    validate_mystery_id,
)
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
    # Mystery ID schemas (Publisher input)
    "ClassificationCode",
    "CLASSIFICATION_DESCRIPTIONS",
    "CLASSIFICATION_DESCRIPTIONS_EN",
    "REGION_CODES",
    "validate_mystery_id",
    "parse_mystery_id",
    # Mystery Report schemas (Scholar output)
    "AnalysisResults",
    "ConfidenceLevel",
    "DiscrepancyType",
    "Evidence",
    "HistoricalContext",
    "MysteryReport",
]
