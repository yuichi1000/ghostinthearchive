"""Unit tests for translator_agents/tools/firestore_tools.py.

Tests for evidence extraction, loading, and saving in the translation pipeline.
"""

import json
from unittest.mock import MagicMock, patch

import pytest

from translator_agents.tools.firestore_tools import (
    _extract_translatable_evidence,
    load_mystery_for_translation,
    save_translation_result,
)

FIRESTORE_CLIENT_PATH = "translator_agents.tools.firestore_tools.get_firestore_client"


# =============================================================================
# _extract_translatable_evidence tests
# =============================================================================


class TestExtractTranslatableEvidence:
    """Tests for _extract_translatable_evidence()."""

    def test_extracts_all_fields(self, sample_evidence_data):
        """All evidence fields are extracted correctly."""
        result = _extract_translatable_evidence(sample_evidence_data)

        assert result["source_type"] == "newspaper"
        assert result["source_language"] == "en"
        assert result["source_title"] == "Boston Daily Advertiser"
        assert result["source_date"] == "1842-03-15"
        assert result["source_url"] == "https://chroniclingamerica.loc.gov/lccn/sn12345/"
        assert result["relevant_excerpt"] == "The vessel was last seen departing the harbor..."
        assert result["location_context"] == "Boston Harbor"

    def test_empty_dict(self):
        """Empty dict returns defaults for all fields."""
        result = _extract_translatable_evidence({})

        assert result["source_type"] == ""
        assert result["source_language"] == ""
        assert result["source_title"] == ""
        assert result["source_date"] is None
        assert result["source_url"] == ""
        assert result["relevant_excerpt"] == ""
        assert result["location_context"] is None

    def test_missing_optional_fields(self):
        """Optional fields (source_date, location_context) default to None."""
        evidence = {
            "source_type": "newspaper",
            "source_language": "en",
            "source_title": "Test Paper",
            "source_url": "https://example.com",
            "relevant_excerpt": "Some text",
        }
        result = _extract_translatable_evidence(evidence)

        assert result["source_date"] is None
        assert result["location_context"] is None
        assert result["source_title"] == "Test Paper"
        assert result["relevant_excerpt"] == "Some text"

    def test_empty_relevant_excerpt(self):
        """Empty relevant_excerpt (e.g. map/image source) is preserved."""
        evidence = {
            "source_type": "newspaper",
            "source_language": "en",
            "source_title": "Historical Map",
            "source_url": "https://example.com/map",
            "relevant_excerpt": "",
        }
        result = _extract_translatable_evidence(evidence)

        assert result["relevant_excerpt"] == ""


# =============================================================================
# load_mystery_for_translation tests
# =============================================================================


class TestLoadMysteryForTranslation:
    """Tests for load_mystery_for_translation()."""

    def test_includes_evidence_fields(self, sample_mystery_report_data):
        """Evidence fields are included in the returned dict."""
        mock_doc = MagicMock()
        mock_doc.exists = True
        mock_doc.to_dict.return_value = sample_mystery_report_data

        mock_client = MagicMock()
        mock_client.collection.return_value.document.return_value.get.return_value = mock_doc

        with patch(FIRESTORE_CLIENT_PATH, return_value=mock_client):
            result = load_mystery_for_translation("TEST-ID")

        assert result is not None
        assert "evidence_a" in result
        assert "evidence_b" in result
        assert "additional_evidence" in result

        # Verify evidence_a fields
        assert result["evidence_a"]["source_type"] == "newspaper"
        assert result["evidence_a"]["source_language"] == "en"
        assert result["evidence_a"]["source_title"] == "Boston Daily Advertiser"

        # Verify evidence_b fields
        assert result["evidence_b"]["source_language"] == "es"
        assert result["evidence_b"]["source_title"] == "Diario de la Marina"

        # Verify additional_evidence is a list
        assert isinstance(result["additional_evidence"], list)
        assert len(result["additional_evidence"]) == 0

    def test_includes_evidence_with_additional(self, sample_mystery_report_data):
        """Additional evidence list items are extracted correctly."""
        extra_evidence = {
            "source_type": "newspaper",
            "source_language": "en",
            "source_title": "New York Herald",
            "source_date": "1842-04-01",
            "source_url": "https://example.com/nyh",
            "relevant_excerpt": "Further reports confirm...",
            "location_context": "New York",
        }
        sample_mystery_report_data["additional_evidence"] = [extra_evidence]

        mock_doc = MagicMock()
        mock_doc.exists = True
        mock_doc.to_dict.return_value = sample_mystery_report_data

        mock_client = MagicMock()
        mock_client.collection.return_value.document.return_value.get.return_value = mock_doc

        with patch(FIRESTORE_CLIENT_PATH, return_value=mock_client):
            result = load_mystery_for_translation("TEST-ID")

        assert len(result["additional_evidence"]) == 1
        assert result["additional_evidence"][0]["source_title"] == "New York Herald"
        assert result["additional_evidence"][0]["relevant_excerpt"] == "Further reports confirm..."

    def test_missing_evidence_defaults_to_empty(self):
        """Missing evidence fields default to empty structures."""
        data_without_evidence = {
            "title": "Test",
            "summary": "Test summary",
            "narrative_content": "Some content",
            "discrepancy_detected": "",
            "hypothesis": "",
            "alternative_hypotheses": [],
            "historical_context": {},
            "story_hooks": [],
        }
        mock_doc = MagicMock()
        mock_doc.exists = True
        mock_doc.to_dict.return_value = data_without_evidence

        mock_client = MagicMock()
        mock_client.collection.return_value.document.return_value.get.return_value = mock_doc

        with patch(FIRESTORE_CLIENT_PATH, return_value=mock_client):
            result = load_mystery_for_translation("TEST-ID")

        assert result["evidence_a"]["source_type"] == ""
        assert result["evidence_b"]["source_type"] == ""
        assert result["additional_evidence"] == []

    def test_returns_none_for_missing_document(self):
        """Returns None when document does not exist."""
        mock_doc = MagicMock()
        mock_doc.exists = False

        mock_client = MagicMock()
        mock_client.collection.return_value.document.return_value.get.return_value = mock_doc

        with patch(FIRESTORE_CLIENT_PATH, return_value=mock_client):
            result = load_mystery_for_translation("NONEXISTENT-ID")

        assert result is None


# =============================================================================
# save_translation_result tests
# =============================================================================


class TestSaveTranslationResult:
    """Tests for save_translation_result()."""

    def test_saves_evidence_en_fields(self):
        """Evidence_en fields are written to Firestore."""
        translation_data = {
            "title_en": "The Vanishing Ship",
            "summary_en": "A ship disappeared",
            "narrative_content_en": "Story content",
            "discrepancy_detected_en": "Discrepancy",
            "hypothesis_en": "Hypothesis",
            "alternative_hypotheses_en": ["Alt 1"],
            "political_climate_en": "Tensions",
            "story_hooks_en": ["Hook 1"],
            "evidence_a_en": {
                "source_type": "newspaper",
                "source_language": "en",
                "source_title": "Boston Daily Advertiser",
                "source_date": "1842-03-15",
                "source_url": "https://example.com",
                "relevant_excerpt": "The vessel departed...",
                "location_context": "Boston Harbor",
            },
            "evidence_b_en": {
                "source_type": "newspaper",
                "source_language": "es",
                "source_title": "Diario de la Marina",
                "source_date": "1842-03-20",
                "source_url": "https://example.com/es",
                "relevant_excerpt": "The ship arrived...",
                "location_context": "Havana",
            },
            "additional_evidence_en": [],
        }
        translation_json = json.dumps(translation_data)

        mock_client = MagicMock()

        with patch(FIRESTORE_CLIENT_PATH, return_value=mock_client), \
             patch("translator_agents.tools.firestore_tools._trigger_revalidation"):
            result = save_translation_result("TEST-ID", translation_json)

        result_data = json.loads(result)
        assert result_data["status"] == "success"

        # Verify the update call includes evidence_en fields
        update_call = mock_client.collection.return_value.document.return_value.update
        update_call.assert_called_once()
        update_data = update_call.call_args[0][0]

        assert update_data["evidence_a_en"] == translation_data["evidence_a_en"]
        assert update_data["evidence_b_en"] == translation_data["evidence_b_en"]
        assert update_data["additional_evidence_en"] == []

    def test_saves_without_evidence_en(self):
        """Works correctly when evidence_en fields are not in translation result."""
        translation_data = {
            "title_en": "Test Title",
            "summary_en": "Test Summary",
            "narrative_content_en": "Content",
            "discrepancy_detected_en": "",
            "hypothesis_en": "",
            "alternative_hypotheses_en": [],
            "political_climate_en": "",
            "story_hooks_en": [],
        }
        translation_json = json.dumps(translation_data)

        mock_client = MagicMock()

        with patch(FIRESTORE_CLIENT_PATH, return_value=mock_client), \
             patch("translator_agents.tools.firestore_tools._trigger_revalidation"):
            result = save_translation_result("TEST-ID", translation_json)

        result_data = json.loads(result)
        assert result_data["status"] == "success"

        update_data = mock_client.collection.return_value.document.return_value.update.call_args[0][0]
        # Should default to empty dict/list
        assert update_data["evidence_a_en"] == {}
        assert update_data["evidence_b_en"] == {}
        assert update_data["additional_evidence_en"] == []
