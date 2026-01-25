"""Mystery Report schemas for Historian Agent output."""

from datetime import datetime
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


class DiscrepancyType(str, Enum):
    """Type of discrepancy detected between sources."""

    DATE_MISMATCH = "date_mismatch"
    PERSON_MISSING = "person_missing"
    EVENT_OUTCOME = "event_outcome"
    LOCATION_CONFLICT = "location_conflict"
    NARRATIVE_GAP = "narrative_gap"
    NAME_VARIANT = "name_variant"


class ConfidenceLevel(str, Enum):
    """Confidence level of the analysis."""

    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class Evidence(BaseModel):
    """Individual piece of evidence from a source document."""

    source_type: str = Field(
        ..., description="Type of source: newspaper or nara_catalog"
    )
    source_language: str = Field(..., description="Language of the source: en or es")
    source_title: str = Field(..., description="Title of the source document")
    source_date: Optional[str] = Field(
        None, description="Date of the source (YYYY-MM-DD)"
    )
    source_url: str = Field(..., description="URL to the original source")
    relevant_excerpt: str = Field(
        ..., description="Key excerpt from the document supporting this evidence"
    )
    location_context: Optional[str] = Field(
        None, description="Geographic context (Boston, NYC, etc.)"
    )

    model_config = {"use_enum_values": True}


class HistoricalContext(BaseModel):
    """Historical context for understanding the mystery."""

    time_period: str = Field(
        ..., description="Era or period (e.g., 'Early 19th Century', '1820s')"
    )
    geographic_scope: List[str] = Field(
        default_factory=list,
        description="Relevant locations (Boston, New York, etc.)",
    )
    relevant_events: List[str] = Field(
        default_factory=list,
        description="Related historical events of the era",
    )
    key_figures: List[str] = Field(
        default_factory=list,
        description="Important historical figures involved",
    )
    political_climate: Optional[str] = Field(
        None,
        description="Political or diplomatic backdrop (US-Spain relations, trade tensions, etc.)",
    )


class MysteryReport(BaseModel):
    """Complete mystery report output from the Historian Agent.

    This schema structures the analysis of historical discrepancies found
    between English newspaper sources and Spanish archival records.
    """

    mystery_id: str = Field(
        ..., description="Unique identifier for this mystery (e.g., 'MYSTERY-1820-BOSTON-001')"
    )
    title: str = Field(
        ..., description="Compelling title for the mystery (e.g., 'The Vanishing of the Santa Maria')"
    )
    summary: str = Field(
        ..., description="2-3 sentence summary of the mystery and its significance"
    )

    discrepancy_detected: str = Field(
        ..., description="Clear statement of the discrepancy found between sources"
    )
    discrepancy_type: DiscrepancyType = Field(
        ..., description="Category of the discrepancy"
    )

    evidence_a: Evidence = Field(
        ..., description="Primary evidence (typically English newspaper source)"
    )
    evidence_b: Evidence = Field(
        ..., description="Contrasting evidence (typically Spanish archival source)"
    )
    additional_evidence: List[Evidence] = Field(
        default_factory=list,
        description="Other supporting documents that relate to this mystery",
    )

    hypothesis: str = Field(
        ..., description="Primary hypothesis explaining the discrepancy"
    )
    alternative_hypotheses: List[str] = Field(
        default_factory=list,
        description="Other possible explanations for the discrepancy",
    )
    confidence_level: ConfidenceLevel = Field(
        ..., description="Confidence level in the primary hypothesis"
    )

    historical_context: HistoricalContext = Field(
        ..., description="Background context for understanding the mystery"
    )

    research_questions: List[str] = Field(
        default_factory=list,
        description="Open questions for further investigation",
    )
    story_hooks: List[str] = Field(
        default_factory=list,
        description="Narrative angles for the Storyteller Agent",
    )

    analysis_timestamp: str = Field(
        default_factory=lambda: datetime.now().isoformat(),
        description="When this analysis was performed",
    )

    model_config = {"use_enum_values": True}


class AnalysisResults(BaseModel):
    """Container for all mystery reports from a single analysis session."""

    theme: str = Field(..., description="Original search theme from Librarian")
    source_file: str = Field(..., description="Path to the source search results file")
    mysteries_found: List[MysteryReport] = Field(default_factory=list)
    total_documents_analyzed: int = Field(0)
    english_sources_count: int = Field(0)
    spanish_sources_count: int = Field(0)
    analysis_timestamp: str = Field(
        default_factory=lambda: datetime.now().isoformat(),
        description="When this analysis was performed",
    )
