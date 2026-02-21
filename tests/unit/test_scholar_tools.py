"""Unit tests for Scholar tools - save_structured_report.

Tests for saving structured analysis reports to session state via tool_context.
"""

import json
from unittest.mock import MagicMock

from mystery_agents.tools.scholar_tools import (
    _validate_evidence,
    save_structured_report,
)


class TestSaveStructuredReport:
    """Tests for save_structured_report()."""

    def test_saves_report_to_session_state(self):
        """Should save parsed JSON to tool_context.state['structured_report']."""
        report_data = {
            "title": "The Vanishing Ship",
            "summary": "A ship disappeared",
            "evidence_a": {"source_url": "https://example.com", "source_date": "1842-03-15"},
            "evidence_b": {"source_url": "https://example.com/es", "source_date": "1842-03-20"},
            "hypothesis": "The ship faked its sinking",
            "alternative_hypotheses": ["Mistaken identity"],
            "classification": "OCC",
            "country_code": "US",
            "region_code": "BOS",
        }
        report_json = json.dumps(report_data)

        mock_tool_context = MagicMock()
        mock_tool_context.state = {}

        result = save_structured_report(report_json, mock_tool_context)
        result_data = json.loads(result)

        assert result_data["status"] == "success"
        assert "structured_report" in mock_tool_context.state
        assert mock_tool_context.state["structured_report"] == report_data

    def test_returns_saved_field_names(self):
        """Should return the list of saved field names."""
        report_data = {
            "title": "Test",
            "hypothesis": "Test hypothesis",
            "evidence_a": {},
        }
        report_json = json.dumps(report_data)

        mock_tool_context = MagicMock()
        mock_tool_context.state = {}

        result = save_structured_report(report_json, mock_tool_context)
        result_data = json.loads(result)

        assert set(result_data["fields_saved"]) == {"title", "hypothesis", "evidence_a"}

    def test_handles_invalid_json(self):
        """Should return error for invalid JSON input."""
        mock_tool_context = MagicMock()
        mock_tool_context.state = {}

        result = save_structured_report("not valid json", mock_tool_context)
        result_data = json.loads(result)

        assert result_data["status"] == "error"
        assert "Invalid JSON" in result_data["error"]
        assert "structured_report" not in mock_tool_context.state

    def test_overwrites_previous_report(self):
        """Should overwrite any previous structured_report in state."""
        mock_tool_context = MagicMock()
        mock_tool_context.state = {
            "structured_report": {"old": "data"},
        }

        new_report = {"title": "New Report", "hypothesis": "New hypothesis"}
        result = save_structured_report(json.dumps(new_report), mock_tool_context)
        result_data = json.loads(result)

        assert result_data["status"] == "success"
        assert mock_tool_context.state["structured_report"] == new_report
        assert "old" not in mock_tool_context.state["structured_report"]

    def test_preserves_all_fields(self):
        """Should preserve all fields from the input JSON including nested objects."""
        report_data = {
            "title": "Test Mystery",
            "summary": "Summary",
            "discrepancy_detected": "Discrepancy",
            "discrepancy_type": "event_outcome",
            "evidence_a": {
                "source_type": "newspaper",
                "source_language": "en",
                "source_title": "Boston Daily",
                "source_date": "1842-03-15",
                "source_url": "https://example.com",
                "relevant_excerpt": "The vessel departed...",
                "location_context": "Boston Harbor",
            },
            "evidence_b": {
                "source_type": "newspaper",
                "source_language": "es",
                "source_title": "Diario de la Marina",
                "source_date": "1842-03-20",
                "source_url": "https://example.com/es",
                "relevant_excerpt": "El buque llegó...",
                "location_context": "Havana",
            },
            "additional_evidence": [],
            "hypothesis": "Hypothesis text",
            "alternative_hypotheses": ["Alt 1", "Alt 2"],
            "confidence_level": "medium",
            "historical_context": {
                "time_period": "Early 19th Century",
                "geographic_scope": ["Boston", "Havana"],
                "relevant_events": ["War of 1812"],
                "key_figures": ["Captain Smith"],
                "political_climate": "Tensions",
            },
            "research_questions": ["What cargo?"],
            "story_hooks": ["Ghost ship"],
            "classification": "OCC",
            "country_code": "US",
            "region_code": "BOS",
        }
        report_json = json.dumps(report_data)

        mock_tool_context = MagicMock()
        mock_tool_context.state = {}

        save_structured_report(report_json, mock_tool_context)

        saved = mock_tool_context.state["structured_report"]
        assert saved["evidence_a"]["source_url"] == "https://example.com"
        assert saved["evidence_b"]["source_language"] == "es"
        assert saved["historical_context"]["geographic_scope"] == ["Boston", "Havana"]
        assert saved["classification"] == "OCC"


class TestValidateEvidence:
    """Tests for _validate_evidence() helper."""

    def test_valid_evidence_returns_no_warnings(self):
        """正常な evidence は警告なし。"""
        evidence = {
            "source_url": "https://example.com",
            "relevant_excerpt": "The vessel departed Boston Harbor...",
        }
        warnings = _validate_evidence(evidence, "evidence_a")
        assert warnings == []

    def test_empty_excerpt_returns_warning(self):
        """relevant_excerpt が空文字 → 警告。"""
        evidence = {
            "source_url": "https://example.com",
            "relevant_excerpt": "",
        }
        warnings = _validate_evidence(evidence, "evidence_a")
        assert len(warnings) == 1
        assert "relevant_excerpt" in warnings[0]

    def test_missing_excerpt_returns_warning(self):
        """relevant_excerpt キーがない → 警告。"""
        evidence = {
            "source_url": "https://example.com",
        }
        warnings = _validate_evidence(evidence, "evidence_b")
        assert len(warnings) == 1
        assert "relevant_excerpt" in warnings[0]

    def test_empty_source_url_returns_warning(self):
        """source_url が空文字 → 警告。"""
        evidence = {
            "source_url": "",
            "relevant_excerpt": "Some text",
        }
        warnings = _validate_evidence(evidence, "evidence_a")
        assert len(warnings) == 1
        assert "source_url" in warnings[0]

    def test_missing_source_url_returns_warning(self):
        """source_url キーがない → 警告。"""
        evidence = {
            "relevant_excerpt": "Some text",
        }
        warnings = _validate_evidence(evidence, "evidence_a")
        assert len(warnings) == 1
        assert "source_url" in warnings[0]

    def test_both_empty_returns_two_warnings(self):
        """両方空 → 警告2件。"""
        evidence = {
            "source_url": "",
            "relevant_excerpt": "",
        }
        warnings = _validate_evidence(evidence, "evidence_a")
        assert len(warnings) == 2

    def test_whitespace_only_excerpt_returns_warning(self):
        """空白のみの excerpt → 警告。"""
        evidence = {
            "source_url": "https://example.com",
            "relevant_excerpt": "   ",
        }
        warnings = _validate_evidence(evidence, "evidence_a")
        assert len(warnings) == 1
        assert "relevant_excerpt" in warnings[0]


class TestSaveStructuredReportEvidenceValidation:
    """Tests for evidence validation in save_structured_report()."""

    def test_empty_excerpt_in_evidence_a_warns_but_saves(self):
        """evidence_a の excerpt が空 → 警告付きで保存される。"""
        report_data = {
            "title": "Test",
            "evidence_a": {
                "source_url": "https://example.com",
                "relevant_excerpt": "",
            },
            "evidence_b": {
                "source_url": "https://example.com/b",
                "relevant_excerpt": "Valid excerpt",
            },
        }
        mock_ctx = MagicMock()
        mock_ctx.state = {}

        result = save_structured_report(json.dumps(report_data), mock_ctx)
        result_data = json.loads(result)

        assert result_data["status"] == "success"
        assert len(result_data["warnings"]) > 0
        # evidence_a は除外されない（構造上必須）
        assert "evidence_a" in mock_ctx.state["structured_report"]

    def test_empty_excerpt_in_additional_evidence_filtered_out(self):
        """additional_evidence の excerpt が空 → フィルタリングされる。"""
        report_data = {
            "title": "Test",
            "evidence_a": {
                "source_url": "https://example.com",
                "relevant_excerpt": "Valid",
            },
            "additional_evidence": [
                {
                    "source_url": "https://example.com/1",
                    "relevant_excerpt": "Good excerpt",
                },
                {
                    "source_url": "https://example.com/2",
                    "relevant_excerpt": "",
                },
                {
                    "source_url": "https://example.com/3",
                    "relevant_excerpt": "Another good one",
                },
            ],
        }
        mock_ctx = MagicMock()
        mock_ctx.state = {}

        result = save_structured_report(json.dumps(report_data), mock_ctx)
        result_data = json.loads(result)

        assert result_data["status"] == "success"
        saved = mock_ctx.state["structured_report"]
        # 空 excerpt の項目がフィルタリングされて2件のみ
        assert len(saved["additional_evidence"]) == 2
        assert all(
            ev["relevant_excerpt"] for ev in saved["additional_evidence"]
        )

    def test_all_additional_evidence_empty_results_in_empty_list(self):
        """全 additional_evidence が空 excerpt → 空リスト。"""
        report_data = {
            "title": "Test",
            "additional_evidence": [
                {"source_url": "https://a.com", "relevant_excerpt": ""},
                {"source_url": "https://b.com", "relevant_excerpt": "  "},
            ],
        }
        mock_ctx = MagicMock()
        mock_ctx.state = {}

        result = save_structured_report(json.dumps(report_data), mock_ctx)
        result_data = json.loads(result)

        assert result_data["status"] == "success"
        assert mock_ctx.state["structured_report"]["additional_evidence"] == []

    def test_valid_report_has_no_warnings(self):
        """全 evidence が正常 → warnings 空リスト。"""
        report_data = {
            "title": "Test",
            "evidence_a": {
                "source_url": "https://example.com",
                "relevant_excerpt": "Excerpt A",
            },
            "evidence_b": {
                "source_url": "https://example.com/b",
                "relevant_excerpt": "Excerpt B",
            },
            "additional_evidence": [
                {
                    "source_url": "https://example.com/c",
                    "relevant_excerpt": "Excerpt C",
                },
            ],
        }
        mock_ctx = MagicMock()
        mock_ctx.state = {}

        result = save_structured_report(json.dumps(report_data), mock_ctx)
        result_data = json.loads(result)

        assert result_data["status"] == "success"
        assert result_data["warnings"] == []
