"""Unit tests for Scholar tools - save_structured_report.

Tests for saving structured analysis reports to session state via tool_context.
"""

import json
from unittest.mock import MagicMock

from archive_agents.tools.scholar_tools import save_structured_report


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
            "state_code": "MA",
            "area_code": "617",
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
            "state_code": "MA",
            "area_code": "617",
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
