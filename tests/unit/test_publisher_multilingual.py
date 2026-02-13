"""Unit tests for Publisher multilingual translations map construction."""

import json
from unittest.mock import MagicMock, patch

from mystery_agents.tools.publisher_tools import publish_mystery


def _make_mystery_json(**overrides):
    """Build a minimal valid mystery JSON string for testing."""
    data = {
        "classification": "OCC",
        "state_code": "MA",
        "area_code": "617",
        "title": "Test Mystery",
        "summary": "A test mystery summary.",
        "discrepancy_detected": "Test discrepancy",
        "discrepancy_type": "event_outcome",
        "evidence_a": {"source_type": "newspaper", "source_language": "en",
                       "source_title": "Test", "source_date": "1842-01-01",
                       "source_url": "https://example.com", "relevant_excerpt": "...",
                       "location_context": "Boston"},
        "evidence_b": {"source_type": "newspaper", "source_language": "es",
                       "source_title": "Test ES", "source_date": "1842-02-01",
                       "source_url": "https://example.com/es", "relevant_excerpt": "...",
                       "location_context": "Havana"},
        "hypothesis": "Test hypothesis",
        "alternative_hypotheses": [],
        "confidence_level": "medium",
        "historical_context": {"time_period": "19th Century",
                               "geographic_scope": ["Boston"],
                               "relevant_events": [], "key_figures": [],
                               "political_climate": "Stable"},
        "research_questions": [],
        "story_hooks": [],
        "narrative_content": "# Test Story\nOnce upon a time...",
    }
    data.update(overrides)
    return json.dumps(data, ensure_ascii=False)


def _make_tool_context(state: dict) -> MagicMock:
    """Create a mock ToolContext with the given state dict."""
    ctx = MagicMock()
    ctx.state = state
    return ctx


class TestPublisherTranslationsMap:
    """Tests for translations map construction from session state."""

    @patch("mystery_agents.tools.publisher_tools.get_storage_bucket")
    @patch("mystery_agents.tools.publisher_tools.get_firestore_client")
    def test_builds_translations_map_from_session_state(
        self, mock_get_db, mock_get_bucket
    ):
        """Should collect all 6 language translations into a translations map."""
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        mock_get_bucket.return_value = MagicMock()

        state = {
            "translation_result_ja": json.dumps({
                "title": "テストミステリー",
                "summary": "テスト要約",
            }),
            "translation_result_es": json.dumps({
                "title": "Misterio de prueba",
                "summary": "Resumen de prueba",
            }),
            "translation_result_de": json.dumps({
                "title": "Testgeheimnis",
                "summary": "Testzusammenfassung",
            }),
        }

        tool_context = _make_tool_context(state)
        result = publish_mystery(_make_mystery_json(), "", tool_context)
        result_data = json.loads(result)

        assert result_data["status"] == "success"
        saved_data = mock_db.collection.return_value.document.return_value.set.call_args[0][0]

        assert "translations" in saved_data
        assert "ja" in saved_data["translations"]
        assert "es" in saved_data["translations"]
        assert "de" in saved_data["translations"]
        assert saved_data["translations"]["ja"]["title"] == "テストミステリー"
        assert saved_data["translations"]["es"]["title"] == "Misterio de prueba"

    @patch("mystery_agents.tools.publisher_tools.get_storage_bucket")
    @patch("mystery_agents.tools.publisher_tools.get_firestore_client")
    def test_skips_no_translation_results(
        self, mock_get_db, mock_get_bucket
    ):
        """Should skip languages that returned NO_TRANSLATION."""
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        mock_get_bucket.return_value = MagicMock()

        state = {
            "translation_result_ja": json.dumps({"title": "日本語タイトル"}),
            "translation_result_es": "NO_TRANSLATION: No content to translate.",
            "translation_result_de": None,
        }

        tool_context = _make_tool_context(state)
        result = publish_mystery(_make_mystery_json(), "", tool_context)
        result_data = json.loads(result)

        assert result_data["status"] == "success"
        saved_data = mock_db.collection.return_value.document.return_value.set.call_args[0][0]

        assert "translations" in saved_data
        assert "ja" in saved_data["translations"]
        assert "es" not in saved_data["translations"]
        assert "de" not in saved_data["translations"]

    @patch("mystery_agents.tools.publisher_tools.get_storage_bucket")
    @patch("mystery_agents.tools.publisher_tools.get_firestore_client")
    def test_no_translations_key_when_all_fail(
        self, mock_get_db, mock_get_bucket
    ):
        """Should not include translations key when no translations available."""
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        mock_get_bucket.return_value = MagicMock()

        state = {
            "translation_result_ja": "NO_TRANSLATION: No content.",
            "translation_result_es": "NO_TRANSLATION: No content.",
        }

        tool_context = _make_tool_context(state)
        result = publish_mystery(_make_mystery_json(), "", tool_context)
        result_data = json.loads(result)

        assert result_data["status"] == "success"
        saved_data = mock_db.collection.return_value.document.return_value.set.call_args[0][0]
        assert "translations" not in saved_data

    @patch("mystery_agents.tools.publisher_tools.get_storage_bucket")
    @patch("mystery_agents.tools.publisher_tools.get_firestore_client")
    def test_handles_dict_translation_result(
        self, mock_get_db, mock_get_bucket
    ):
        """Should handle translation results that are already dicts (not JSON strings)."""
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        mock_get_bucket.return_value = MagicMock()

        state = {
            "translation_result_fr": {
                "title": "Mystère de test",
                "summary": "Résumé de test",
            },
        }

        tool_context = _make_tool_context(state)
        result = publish_mystery(_make_mystery_json(), "", tool_context)
        result_data = json.loads(result)

        assert result_data["status"] == "success"
        saved_data = mock_db.collection.return_value.document.return_value.set.call_args[0][0]
        assert saved_data["translations"]["fr"]["title"] == "Mystère de test"

    @patch("mystery_agents.tools.publisher_tools.get_storage_bucket")
    @patch("mystery_agents.tools.publisher_tools.get_firestore_client")
    def test_handles_malformed_json_translation(
        self, mock_get_db, mock_get_bucket
    ):
        """Should skip translations with malformed JSON gracefully."""
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        mock_get_bucket.return_value = MagicMock()

        state = {
            "translation_result_ja": json.dumps({"title": "正常な翻訳"}),
            "translation_result_nl": "this is { not valid json",
        }

        tool_context = _make_tool_context(state)
        result = publish_mystery(_make_mystery_json(), "", tool_context)
        result_data = json.loads(result)

        assert result_data["status"] == "success"
        saved_data = mock_db.collection.return_value.document.return_value.set.call_args[0][0]
        assert "ja" in saved_data["translations"]
        assert "nl" not in saved_data["translations"]

    @patch("mystery_agents.tools.publisher_tools.get_storage_bucket")
    @patch("mystery_agents.tools.publisher_tools.get_firestore_client")
    def test_all_six_languages_in_translations(
        self, mock_get_db, mock_get_bucket
    ):
        """Should include all 6 languages when all translations succeed."""
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        mock_get_bucket.return_value = MagicMock()

        state = {}
        for lang in ["ja", "es", "de", "fr", "nl", "pt"]:
            state[f"translation_result_{lang}"] = json.dumps({
                "title": f"Title in {lang}",
                "summary": f"Summary in {lang}",
            })

        tool_context = _make_tool_context(state)
        result = publish_mystery(_make_mystery_json(), "", tool_context)
        result_data = json.loads(result)

        assert result_data["status"] == "success"
        saved_data = mock_db.collection.return_value.document.return_value.set.call_args[0][0]
        assert set(saved_data["translations"].keys()) == {"ja", "es", "de", "fr", "nl", "pt"}
