"""Unit tests for Pydantic schemas."""

import pytest
from pydantic import ValidationError

from mystery_agents.schemas.mystery_report import (
    AnalysisResults,
    MysteryReport,
)


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

    def test_additional_evidence_within_limit(self, sample_mystery_report_data, sample_evidence_data):
        """additional_evidence with 5 or fewer items should pass validation."""
        sample_mystery_report_data["additional_evidence"] = [
            {**sample_evidence_data, "source_title": f"Source {i}"} for i in range(5)
        ]
        report = MysteryReport(**sample_mystery_report_data)
        assert len(report.additional_evidence) == 5

    def test_additional_evidence_exceeds_limit(self, sample_mystery_report_data, sample_evidence_data):
        """additional_evidence with more than 5 items should raise ValidationError."""
        sample_mystery_report_data["additional_evidence"] = [
            {**sample_evidence_data, "source_title": f"Source {i}"} for i in range(6)
        ]
        with pytest.raises(ValidationError):
            MysteryReport(**sample_mystery_report_data)

    def test_missing_required_field_raises_error(self, sample_mystery_report_data):
        """mystery_id 省略で ValidationError が発生する。"""
        del sample_mystery_report_data["mystery_id"]
        with pytest.raises(ValidationError, match="mystery_id"):
            MysteryReport(**sample_mystery_report_data)

    def test_invalid_discrepancy_type_raises_error(self, sample_mystery_report_data):
        """存在しない discrepancy_type で ValidationError が発生する。"""
        sample_mystery_report_data["discrepancy_type"] = "nonexistent_type"
        with pytest.raises(ValidationError):
            MysteryReport(**sample_mystery_report_data)


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
