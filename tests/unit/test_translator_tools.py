"""Unit tests for translator_agents/tools/firestore_tools.py.

Tests for loading English mystery fields and saving Japanese translation results.
Updated for English-first content generation (base fields in English, *_ja for Japanese).
"""

import json
from unittest.mock import MagicMock, patch


from translator_agents.tools.firestore_tools import (
    load_mystery_for_translation,
    save_translation_result,
)

FIRESTORE_CLIENT_PATH = "translator_agents.tools.firestore_tools.get_firestore_client"


# =============================================================================
# load_mystery_for_translation tests
# =============================================================================


class TestLoadMysteryForTranslation:
    """Tests for load_mystery_for_translation()."""

    def test_returns_english_base_fields(self, sample_mystery_report_data):
        """Should return English base fields for translation."""
        mock_doc = MagicMock()
        mock_doc.exists = True
        mock_doc.to_dict.return_value = sample_mystery_report_data

        mock_client = MagicMock()
        mock_client.collection.return_value.document.return_value.get.return_value = mock_doc

        with patch(FIRESTORE_CLIENT_PATH, return_value=mock_client):
            result = load_mystery_for_translation("TEST-ID")

        assert result is not None
        assert result["mystery_id"] == "TEST-ID"
        assert result["title"] == "The Vanishing of the Santa Maria"
        assert result["summary"] == "A Spanish merchant vessel disappeared near Boston Harbor in 1842."
        assert result["hypothesis"] == "The ship may have faked its sinking to smuggle cargo"
        assert result["alternative_hypotheses"] == ["Mistaken identity", "Clerical error in records"]
        assert result["political_climate"] == "Tensions between US and Spain over Florida"
        assert result["story_hooks"] == ["Ghost ship that never sank"]

    def test_does_not_include_evidence_fields(self, sample_mystery_report_data):
        """Evidence fields should NOT be included (evidence stays in English)."""
        mock_doc = MagicMock()
        mock_doc.exists = True
        mock_doc.to_dict.return_value = sample_mystery_report_data

        mock_client = MagicMock()
        mock_client.collection.return_value.document.return_value.get.return_value = mock_doc

        with patch(FIRESTORE_CLIENT_PATH, return_value=mock_client):
            result = load_mystery_for_translation("TEST-ID")

        assert "evidence_a" not in result
        assert "evidence_b" not in result
        assert "additional_evidence" not in result

    def test_missing_fields_default_to_empty(self):
        """Missing fields should default to empty strings/lists."""
        data = {
            "title": "Test",
            "summary": "Test summary",
        }
        mock_doc = MagicMock()
        mock_doc.exists = True
        mock_doc.to_dict.return_value = data

        mock_client = MagicMock()
        mock_client.collection.return_value.document.return_value.get.return_value = mock_doc

        with patch(FIRESTORE_CLIENT_PATH, return_value=mock_client):
            result = load_mystery_for_translation("TEST-ID")

        assert result["narrative_content"] == ""
        assert result["discrepancy_detected"] == ""
        assert result["hypothesis"] == ""
        assert result["alternative_hypotheses"] == []
        assert result["political_climate"] == ""
        assert result["story_hooks"] == []

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

    def test_saves_ja_fields(self):
        """Japanese translation fields (*_ja) are written to Firestore."""
        translation_data = {
            "title_ja": "サンタマリア号の消失",
            "summary_ja": "1842年、ボストン港付近でスペイン商船が消失した。",
            "narrative_content_ja": "記事本文の日本語訳",
            "discrepancy_detected_ja": "矛盾の説明",
            "hypothesis_ja": "仮説の日本語訳",
            "alternative_hypotheses_ja": ["代替仮説1"],
            "historical_context_ja": {
                "political_climate": "米国とスペインの緊張関係",
            },
            "story_hooks_ja": ["沈まなかった幽霊船"],
        }
        translation_json = json.dumps(translation_data)

        mock_client = MagicMock()

        with patch(FIRESTORE_CLIENT_PATH, return_value=mock_client), \
             patch("translator_agents.tools.firestore_tools._trigger_revalidation"):
            result = save_translation_result("TEST-ID", translation_json)

        result_data = json.loads(result)
        assert result_data["status"] == "success"

        update_call = mock_client.collection.return_value.document.return_value.update
        update_call.assert_called_once()
        update_data = update_call.call_args[0][0]

        assert update_data["title_ja"] == "サンタマリア号の消失"
        assert update_data["summary_ja"] == "1842年、ボストン港付近でスペイン商船が消失した。"
        assert update_data["narrative_content_ja"] == "記事本文の日本語訳"
        assert update_data["hypothesis_ja"] == "仮説の日本語訳"
        assert update_data["alternative_hypotheses_ja"] == ["代替仮説1"]
        assert update_data["story_hooks_ja"] == ["沈まなかった幽霊船"]
        assert update_data["historical_context_ja"]["political_climate"] == "米国とスペインの緊張関係"

    def test_does_not_save_evidence_fields(self):
        """Evidence *_en fields should NOT be written (evidence stays in English)."""
        translation_data = {
            "title_ja": "テスト",
            "summary_ja": "テスト要約",
            "narrative_content_ja": "本文",
            "discrepancy_detected_ja": "",
            "hypothesis_ja": "",
            "alternative_hypotheses_ja": [],
            "story_hooks_ja": [],
        }
        translation_json = json.dumps(translation_data)

        mock_client = MagicMock()

        with patch(FIRESTORE_CLIENT_PATH, return_value=mock_client), \
             patch("translator_agents.tools.firestore_tools._trigger_revalidation"):
            save_translation_result("TEST-ID", translation_json)

        update_data = mock_client.collection.return_value.document.return_value.update.call_args[0][0]
        assert "evidence_a_en" not in update_data
        assert "evidence_b_en" not in update_data
        assert "additional_evidence_en" not in update_data

    def test_does_not_change_status(self):
        """Should NOT change the status field (articles published with both EN+JA)."""
        translation_data = {
            "title_ja": "テスト",
            "summary_ja": "テスト要約",
            "narrative_content_ja": "本文",
            "discrepancy_detected_ja": "",
            "hypothesis_ja": "",
            "alternative_hypotheses_ja": [],
            "story_hooks_ja": [],
        }
        translation_json = json.dumps(translation_data)

        mock_client = MagicMock()

        with patch(FIRESTORE_CLIENT_PATH, return_value=mock_client), \
             patch("translator_agents.tools.firestore_tools._trigger_revalidation"):
            save_translation_result("TEST-ID", translation_json)

        update_data = mock_client.collection.return_value.document.return_value.update.call_args[0][0]
        assert "status" not in update_data

    def test_handles_markdown_wrapped_json(self):
        """Should extract JSON from Markdown code blocks."""
        translation_data = {
            "title_ja": "マークダウンテスト",
            "summary_ja": "テスト",
            "narrative_content_ja": "本文",
            "discrepancy_detected_ja": "",
            "hypothesis_ja": "",
            "alternative_hypotheses_ja": [],
            "story_hooks_ja": [],
        }
        markdown_json = f"```json\n{json.dumps(translation_data)}\n```"

        mock_client = MagicMock()

        with patch(FIRESTORE_CLIENT_PATH, return_value=mock_client), \
             patch("translator_agents.tools.firestore_tools._trigger_revalidation"):
            result = save_translation_result("TEST-ID", markdown_json)

        result_data = json.loads(result)
        assert result_data["status"] == "success"

        update_data = mock_client.collection.return_value.document.return_value.update.call_args[0][0]
        assert update_data["title_ja"] == "マークダウンテスト"

    def test_handles_political_climate_fallback(self):
        """Should support political_climate_ja as direct key fallback."""
        translation_data = {
            "title_ja": "テスト",
            "summary_ja": "テスト",
            "narrative_content_ja": "本文",
            "discrepancy_detected_ja": "",
            "hypothesis_ja": "",
            "alternative_hypotheses_ja": [],
            "political_climate_ja": "日本語の政治情勢",
            "story_hooks_ja": [],
        }
        translation_json = json.dumps(translation_data)

        mock_client = MagicMock()

        with patch(FIRESTORE_CLIENT_PATH, return_value=mock_client), \
             patch("translator_agents.tools.firestore_tools._trigger_revalidation"):
            save_translation_result("TEST-ID", translation_json)

        update_data = mock_client.collection.return_value.document.return_value.update.call_args[0][0]
        assert update_data["historical_context_ja"]["political_climate"] == "日本語の政治情勢"

    def test_error_handling_sets_error_status(self):
        """Should set error status on failure."""
        mock_client = MagicMock()
        mock_client.collection.return_value.document.return_value.update.side_effect = Exception("DB error")

        with patch(FIRESTORE_CLIENT_PATH, return_value=mock_client):
            result = save_translation_result("TEST-ID", '{"title_ja": "test"}')

        result_data = json.loads(result)
        assert result_data["status"] == "error"
        assert "DB error" in result_data["error"]
