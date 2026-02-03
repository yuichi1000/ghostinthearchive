"""Unit tests for Pydantic schemas."""

import pytest
from pydantic import ValidationError

from archive_agents.schemas.document import (
    ArchiveDocument,
    SearchResults,
    SourceLanguage,
    SourceType,
)
from archive_agents.schemas.mystery_report import (
    AnalysisResults,
    ConfidenceLevel,
    DiscrepancyType,
    Evidence,
    HistoricalContext,
    MysteryReport,
)


class TestSourceEnums:
    """Tests for source-related enums."""

    def test_source_language_values(self):
        """SourceLanguage enum should have en and es values."""
        assert SourceLanguage.EN.value == "en"
        assert SourceLanguage.ES.value == "es"

    def test_source_type_values(self):
        """SourceType enum should have all archive source types."""
        expected_types = ["newspaper", "loc_digital", "dpla", "nypl", "pares", "internet_archive"]
        actual_types = [st.value for st in SourceType]
        assert set(expected_types) == set(actual_types)


class TestDiscrepancyEnums:
    """Tests for discrepancy-related enums."""

    def test_discrepancy_type_values(self):
        """DiscrepancyType enum should have all discrepancy categories."""
        expected = [
            "date_mismatch",
            "person_missing",
            "event_outcome",
            "location_conflict",
            "narrative_gap",
            "name_variant",
        ]
        actual = [dt.value for dt in DiscrepancyType]
        assert set(expected) == set(actual)

    def test_confidence_level_values(self):
        """ConfidenceLevel enum should have high, medium, low."""
        assert ConfidenceLevel.HIGH.value == "high"
        assert ConfidenceLevel.MEDIUM.value == "medium"
        assert ConfidenceLevel.LOW.value == "low"


class TestArchiveDocument:
    """Tests for ArchiveDocument schema."""

    def test_valid_document(self, sample_archive_document_data):
        """Valid data should create an ArchiveDocument."""
        doc = ArchiveDocument(**sample_archive_document_data)
        assert doc.title == "Mystery of the Lost Ship"
        assert doc.language == "en"
        assert doc.source_type == "newspaper"

    def test_missing_required_field(self, sample_archive_document_data):
        """Missing required field should raise ValidationError."""
        del sample_archive_document_data["title"]
        with pytest.raises(ValidationError) as exc_info:
            ArchiveDocument(**sample_archive_document_data)
        assert "title" in str(exc_info.value)

    def test_invalid_language_enum(self, sample_archive_document_data):
        """Invalid language should raise ValidationError."""
        sample_archive_document_data["language"] = "invalid"
        with pytest.raises(ValidationError) as exc_info:
            ArchiveDocument(**sample_archive_document_data)
        assert "language" in str(exc_info.value)

    def test_invalid_source_type_enum(self, sample_archive_document_data):
        """Invalid source_type should raise ValidationError."""
        sample_archive_document_data["source_type"] = "invalid_source"
        with pytest.raises(ValidationError) as exc_info:
            ArchiveDocument(**sample_archive_document_data)
        assert "source_type" in str(exc_info.value)

    def test_optional_fields_default_to_none(self):
        """Optional fields should default to None or empty list."""
        minimal_data = {
            "title": "Test",
            "source_url": "https://example.com",
            "summary": "Test summary",
            "language": "en",
            "location": "Boston",
            "source_type": "newspaper",
        }
        doc = ArchiveDocument(**minimal_data)
        assert doc.date is None
        assert doc.raw_text is None
        assert doc.record_group is None
        assert doc.keywords_matched == []

    def test_use_enum_values_config(self, sample_archive_document_data):
        """use_enum_values should serialize enums as strings."""
        doc = ArchiveDocument(**sample_archive_document_data)
        data = doc.model_dump()
        assert data["language"] == "en"
        assert data["source_type"] == "newspaper"


class TestSearchResults:
    """Tests for SearchResults schema."""

    def test_valid_search_results(self, sample_search_results_data):
        """Valid data should create SearchResults."""
        results = SearchResults(**sample_search_results_data)
        assert results.theme == "Boston maritime mysteries 1840s"
        assert len(results.documents) == 1
        assert results.total_found == 1

    def test_default_values(self):
        """Default values should be applied correctly."""
        results = SearchResults(theme="Test theme")
        assert results.documents == []
        assert results.total_found == 0
        assert results.sources_searched == []
        assert results.search_timestamp is not None

    def test_search_timestamp_auto_generated(self):
        """search_timestamp should be auto-generated if not provided."""
        results = SearchResults(theme="Test")
        assert len(results.search_timestamp) > 0
        # Should be ISO format
        assert "T" in results.search_timestamp


class TestEvidence:
    """Tests for Evidence schema."""

    def test_valid_evidence(self, sample_evidence_data):
        """Valid data should create an Evidence object."""
        evidence = Evidence(**sample_evidence_data)
        assert evidence.source_type == "newspaper"
        assert evidence.source_language == "en"

    def test_missing_required_field(self, sample_evidence_data):
        """Missing required field should raise ValidationError."""
        del sample_evidence_data["relevant_excerpt"]
        with pytest.raises(ValidationError):
            Evidence(**sample_evidence_data)

    def test_optional_location_context(self, sample_evidence_data):
        """location_context should be optional."""
        del sample_evidence_data["location_context"]
        evidence = Evidence(**sample_evidence_data)
        assert evidence.location_context is None


class TestHistoricalContext:
    """Tests for HistoricalContext schema."""

    def test_valid_historical_context(self, sample_historical_context_data):
        """Valid data should create a HistoricalContext object."""
        context = HistoricalContext(**sample_historical_context_data)
        assert context.time_period == "Early 19th Century"
        assert "Boston" in context.geographic_scope

    def test_default_empty_lists(self):
        """List fields should default to empty lists."""
        context = HistoricalContext(time_period="Test Period")
        assert context.geographic_scope == []
        assert context.relevant_events == []
        assert context.key_figures == []

    def test_optional_political_climate(self):
        """political_climate should be optional."""
        context = HistoricalContext(time_period="Test Period")
        assert context.political_climate is None


class TestMysteryReport:
    """Tests for MysteryReport schema."""

    def test_valid_mystery_report(self, sample_mystery_report_data):
        """Valid data should create a MysteryReport."""
        report = MysteryReport(**sample_mystery_report_data)
        assert report.mystery_id == "MYSTERY-1842-BOSTON-001"
        assert report.discrepancy_type == "event_outcome"
        assert report.confidence_level == "medium"

    def test_discrepancy_type_enum_coercion(self, sample_mystery_report_data):
        """String value should be coerced to enum."""
        sample_mystery_report_data["discrepancy_type"] = "date_mismatch"
        report = MysteryReport(**sample_mystery_report_data)
        assert report.discrepancy_type == "date_mismatch"

    def test_invalid_discrepancy_type(self, sample_mystery_report_data):
        """Invalid discrepancy_type should raise ValidationError."""
        sample_mystery_report_data["discrepancy_type"] = "invalid_type"
        with pytest.raises(ValidationError):
            MysteryReport(**sample_mystery_report_data)

    def test_invalid_confidence_level(self, sample_mystery_report_data):
        """Invalid confidence_level should raise ValidationError."""
        sample_mystery_report_data["confidence_level"] = "very_high"
        with pytest.raises(ValidationError):
            MysteryReport(**sample_mystery_report_data)

    def test_analysis_timestamp_auto_generated(self, sample_mystery_report_data):
        """analysis_timestamp should be auto-generated."""
        report = MysteryReport(**sample_mystery_report_data)
        assert report.analysis_timestamp is not None
        assert "T" in report.analysis_timestamp

    def test_narrative_content_optional(self, sample_mystery_report_data):
        """narrative_content should be optional."""
        report = MysteryReport(**sample_mystery_report_data)
        assert report.narrative_content is None


class TestAnalysisResults:
    """Tests for AnalysisResults schema."""

    def test_valid_analysis_results(self, sample_mystery_report_data):
        """Valid data should create AnalysisResults."""
        results = AnalysisResults(
            theme="Boston mysteries",
            source_file="/data/search_results.json",
            mysteries_found=[MysteryReport(**sample_mystery_report_data)],
            total_documents_analyzed=10,
            english_sources_count=6,
            spanish_sources_count=4,
        )
        assert results.theme == "Boston mysteries"
        assert len(results.mysteries_found) == 1

    def test_default_values(self):
        """Default values should be applied correctly."""
        results = AnalysisResults(theme="Test", source_file="/test.json")
        assert results.mysteries_found == []
        assert results.total_documents_analyzed == 0
        assert results.english_sources_count == 0
        assert results.spanish_sources_count == 0
