"""Mystery Report schemas for Scholar Agent output."""

from datetime import datetime
from enum import Enum
from typing import List, Literal, Optional

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
        ..., description="Type of source: newspaper"
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


class SourceCoverage(BaseModel):
    """ソースカバレッジ評価 — Polymath が行う調査範囲の自己評価。"""

    apis_searched: List[str] = Field(
        default_factory=list,
        description="検索した API/アーカイブのリスト",
    )
    apis_with_results: List[str] = Field(
        default_factory=list,
        description="結果を返した API/アーカイブのリスト",
    )
    apis_without_results: List[str] = Field(
        default_factory=list,
        description="結果を返さなかった API/アーカイブのリスト",
    )
    known_undigitized_sources: List[str] = Field(
        default_factory=list,
        description="この時代・地域に存在するがデジタル化されていない既知のソース",
    )
    coverage_assessment: Optional[str] = Field(
        None,
        description="デジタル化範囲と調査限界に関する総合評価",
    )


class AgentLogEntry(BaseModel):
    """パイプライン実行中の単一エージェントのログエントリ。"""

    agent_name: str = Field(..., description="エージェント名 (librarian, scholar, etc.)")
    status: Literal["running", "completed", "error"] = Field(..., description="実行ステータス")
    start_time: str = Field(..., description="開始タイムスタンプ (ISO format)")
    end_time: Optional[str] = Field(None, description="終了タイムスタンプ (ISO format)")
    duration_seconds: Optional[float] = Field(None, description="所要時間（秒）")
    output_summary: Optional[str] = Field(None, description="出力の要約（最大200文字）")


class MysteryReport(BaseModel):
    """Complete mystery report output from the Scholar Agent.

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
        max_length=5,
        description="Other supporting documents that relate to this mystery (max 5)",
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
    source_coverage: Optional[SourceCoverage] = Field(
        None,
        description="ソースカバレッジ評価（検索範囲と限界の自己評価）",
    )
    confidence_rationale: Optional[str] = Field(
        None,
        description="confidence_level 判定の根拠（なぜその水準か）",
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

    narrative_content: Optional[str] = Field(
        None,
        description="Storyteller が生成した物語的ブログ原稿（マークダウン形式）",
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
