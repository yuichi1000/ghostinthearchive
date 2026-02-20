"""Unit tests for Publisher multilingual translations map construction."""

import json
import logging
from unittest.mock import MagicMock, patch

from mystery_agents.tools.publisher_tools import _extract_json_from_text, publish_mystery


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


class TestExtractJsonFromText:
    """Tests for _extract_json_from_text helper."""

    def test_parses_raw_json(self):
        """素の JSON 文字列をパースできること。"""
        text = '{"title": "Test", "summary": "Hello"}'
        result = _extract_json_from_text(text)
        assert result == {"title": "Test", "summary": "Hello"}

    def test_parses_json_in_markdown_codeblock(self):
        """```json ... ``` で包まれた JSON をパースできること。"""
        text = '```json\n{"title": "Test", "summary": "Hello"}\n```'
        result = _extract_json_from_text(text)
        assert result == {"title": "Test", "summary": "Hello"}

    def test_parses_json_in_plain_codeblock(self):
        """``` ... ```（json タグなし）で包まれた JSON をパースできること。"""
        text = '```\n{"title": "Test"}\n```'
        result = _extract_json_from_text(text)
        assert result == {"title": "Test"}

    def test_parses_json_with_surrounding_text(self):
        """前後に余計なテキストがあるコードブロック内の JSON をパースできること。"""
        text = 'Here is the translation:\n```json\n{"title": "Test"}\n```\nDone.'
        result = _extract_json_from_text(text)
        assert result == {"title": "Test"}

    def test_returns_none_for_broken_text(self):
        """完全に壊れたテキストでは None を返すこと。"""
        result = _extract_json_from_text("this is not json at all")
        assert result is None

    def test_returns_none_for_empty_string(self):
        """空文字列では None を返すこと。"""
        result = _extract_json_from_text("")
        assert result is None

    def test_returns_none_for_json_array(self):
        """JSON 配列では None を返すこと（dict のみ受け付ける）。"""
        result = _extract_json_from_text('[1, 2, 3]')
        assert result is None

    def test_handles_multiline_json_in_codeblock(self):
        """複数行 JSON のコードブロックをパースできること。"""
        text = '```json\n{\n  "title": "テスト",\n  "summary": "要約"\n}\n```'
        result = _extract_json_from_text(text)
        assert result == {"title": "テスト", "summary": "要約"}


class TestPublisherCodeblockTranslation:
    """Tests for Publisher handling markdown codeblock-wrapped translations."""

    @patch("mystery_agents.tools.publisher_tools.get_storage_bucket")
    @patch("mystery_agents.tools.publisher_tools.get_firestore_client")
    def test_parses_codeblock_wrapped_translation(
        self, mock_get_db, mock_get_bucket
    ):
        """コードブロックで包まれた翻訳結果を正しくパースすること。"""
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        mock_get_bucket.return_value = MagicMock()

        state = {
            "translation_result_ja": json.dumps({"title": "日本語タイトル"}),
            "translation_result_es": '```json\n{"title": "Título en español", "summary": "Resumen"}\n```',
            "translation_result_de": 'Here is the translation:\n```json\n{"title": "Deutscher Titel"}\n```',
        }

        tool_context = _make_tool_context(state)
        result = publish_mystery(_make_mystery_json(), "", tool_context)
        result_data = json.loads(result)

        assert result_data["status"] == "success"
        saved_data = mock_db.collection.return_value.document.return_value.set.call_args[0][0]

        assert saved_data["translations"]["ja"]["title"] == "日本語タイトル"
        assert saved_data["translations"]["es"]["title"] == "Título en español"
        assert saved_data["translations"]["de"]["title"] == "Deutscher Titel"

    @patch("mystery_agents.tools.publisher_tools.get_storage_bucket")
    @patch("mystery_agents.tools.publisher_tools.get_firestore_client")
    def test_logs_translation_summary(
        self, mock_get_db, mock_get_bucket, caplog
    ):
        """翻訳収集のサマリログが出力されること。"""
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        mock_get_bucket.return_value = MagicMock()

        state = {
            "translation_result_ja": json.dumps({"title": "日本語"}),
            "translation_result_es": "NO_TRANSLATION: No content.",
        }

        tool_context = _make_tool_context(state)
        with caplog.at_level(logging.INFO, logger="mystery_agents.tools.publisher_tools"):
            publish_mystery(_make_mystery_json(), "", tool_context)

        assert any("Translations collected" in msg for msg in caplog.messages)
        assert any("['ja']" in msg for msg in caplog.messages)


class TestPublisherLanguageValidation:
    """翻訳言語バリデーションによる拒否テスト。"""

    @patch("mystery_agents.tools.publisher_tools.get_storage_bucket")
    @patch("mystery_agents.tools.publisher_tools.get_firestore_client")
    def test_rejects_english_text_as_french(
        self, mock_get_db, mock_get_bucket
    ):
        """英語テキストをフランス語翻訳として拒否すること。"""
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        mock_get_bucket.return_value = MagicMock()

        # 英語テキストがそのままフランス語翻訳として返された場合
        english_as_french = {
            "title": "The Ghost Ship of Boston Harbor",
            "summary": "The mystery of a ship that vanished in 1842",
            "narrative_content": (
                "A cargo ship docked at Boston Harbor vanished overnight. "
                "All crew members went missing, and the hull was never found again. "
                "Local fishermen claimed to have witnessed a ghost ship on foggy nights, "
                "but the authorities did not include their testimony in official records. "
                "The investigation was conducted by the maritime authorities of the time."
            ),
        }

        state = {
            "translation_result_ja": json.dumps({
                "title": "ボストン港の幽霊船",
                "summary": "1842年に消えた船の謎",
                "narrative_content": (
                    "ボストン港に停泊していた貨物船が一夜にして姿を消した。"
                    "乗組員は全員行方不明となり、船体は二度と発見されなかった。"
                ),
            }),
            "translation_result_fr": json.dumps(english_as_french),
        }

        tool_context = _make_tool_context(state)
        with patch("shared.pipeline_failure.log_pipeline_failure"):
            result = publish_mystery(_make_mystery_json(), "", tool_context)
        result_data = json.loads(result)

        assert result_data["status"] == "success"
        saved_data = mock_db.collection.return_value.document.return_value.set.call_args[0][0]

        # 日本語は通過、フランス語は拒否されること
        assert "ja" in saved_data["translations"]
        assert "fr" not in saved_data["translations"]

    @patch("mystery_agents.tools.publisher_tools.get_storage_bucket")
    @patch("mystery_agents.tools.publisher_tools.get_firestore_client")
    def test_accepts_valid_french_translation(
        self, mock_get_db, mock_get_bucket
    ):
        """正常なフランス語翻訳は通過すること。"""
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        mock_get_bucket.return_value = MagicMock()

        state = {
            "translation_result_fr": json.dumps({
                "title": "Le navire fantôme du port de Boston",
                "summary": "Le mystère d'un navire disparu en 1842",
                "narrative_content": (
                    "Un cargo amarré au port de Boston a disparu du jour au lendemain. "
                    "Tous les membres d'équipage ont disparu et la coque n'a jamais été retrouvée. "
                    "Des pêcheurs locaux affirment avoir aperçu un navire fantôme les nuits de brouillard, "
                    "mais les autorités n'ont pas inclus leur témoignage dans les registres officiels."
                ),
            }),
        }

        tool_context = _make_tool_context(state)
        result = publish_mystery(_make_mystery_json(), "", tool_context)
        result_data = json.loads(result)

        assert result_data["status"] == "success"
        saved_data = mock_db.collection.return_value.document.return_value.set.call_args[0][0]
        assert "fr" in saved_data["translations"]

    @patch("mystery_agents.tools.publisher_tools.get_storage_bucket")
    @patch("mystery_agents.tools.publisher_tools.get_firestore_client")
    def test_logs_warning_on_rejection(
        self, mock_get_db, mock_get_bucket, caplog
    ):
        """拒否時に warning ログが出力されること。"""
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        mock_get_bucket.return_value = MagicMock()

        state = {
            "translation_result_fr": json.dumps({
                "title": "The Ghost Ship",
                "summary": "A mystery of vanished ship",
                "narrative_content": (
                    "A cargo ship docked at Boston Harbor vanished overnight. "
                    "All crew members went missing, and the hull was never found again. "
                    "Local fishermen claimed to have witnessed a ghost ship on foggy nights, "
                    "but the authorities did not include their testimony in official records."
                ),
            }),
        }

        tool_context = _make_tool_context(state)
        with caplog.at_level(logging.WARNING, logger="mystery_agents.tools.publisher_tools"):
            with patch("shared.pipeline_failure.log_pipeline_failure"):
                publish_mystery(_make_mystery_json(), "", tool_context)

        assert any("Translation rejected" in msg for msg in caplog.messages)
        assert any("'fr'" in msg for msg in caplog.messages)
