"""Unit tests for Publisher multilingual translations map construction."""

import json
import logging
from pathlib import Path
from unittest.mock import MagicMock, patch

from mystery_agents.tools.publisher_tools import publish_mystery
from mystery_agents.tools.publisher_utils import _extract_json_from_text
from tests.fakes import make_tool_context

_FIXTURES_DIR = Path(__file__).parent.parent / "fixtures"


def _make_mystery_json(**overrides):
    """Build a minimal valid mystery JSON string for testing."""
    with open(_FIXTURES_DIR / "minimal_mystery.json", "r", encoding="utf-8") as f:
        data = json.load(f)
    data.update(overrides)
    return json.dumps(data, ensure_ascii=False)


class TestPublisherTranslationsMap:
    """Tests for translations map construction from session state."""

    @patch("mystery_agents.tools.image_upload.get_storage_bucket")
    @patch("mystery_agents.tools.publisher_tools.get_firestore_client")
    def test_builds_translations_map_from_session_state(
        self, mock_get_db, mock_get_bucket
    ):
        """Should collect all 3 language translations into a translations map."""
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

        tool_context = make_tool_context(state)
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

    @patch("mystery_agents.tools.image_upload.get_storage_bucket")
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

        tool_context = make_tool_context(state)
        result = publish_mystery(_make_mystery_json(), "", tool_context)
        result_data = json.loads(result)

        assert result_data["status"] == "success"
        saved_data = mock_db.collection.return_value.document.return_value.set.call_args[0][0]

        assert "translations" in saved_data
        assert "ja" in saved_data["translations"]
        assert "es" not in saved_data["translations"]
        assert "de" not in saved_data["translations"]

    @patch("mystery_agents.tools.image_upload.get_storage_bucket")
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

        tool_context = make_tool_context(state)
        result = publish_mystery(_make_mystery_json(), "", tool_context)
        result_data = json.loads(result)

        assert result_data["status"] == "success"
        saved_data = mock_db.collection.return_value.document.return_value.set.call_args[0][0]
        assert "translations" not in saved_data

    @patch("mystery_agents.tools.image_upload.get_storage_bucket")
    @patch("mystery_agents.tools.publisher_tools.get_firestore_client")
    def test_handles_dict_translation_result(
        self, mock_get_db, mock_get_bucket
    ):
        """Should handle translation results that are already dicts (not JSON strings)."""
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        mock_get_bucket.return_value = MagicMock()

        state = {
            "translation_result_de": {
                "title": "Testgeheimnis",
                "summary": "Testzusammenfassung",
            },
        }

        tool_context = make_tool_context(state)
        result = publish_mystery(_make_mystery_json(), "", tool_context)
        result_data = json.loads(result)

        assert result_data["status"] == "success"
        saved_data = mock_db.collection.return_value.document.return_value.set.call_args[0][0]
        assert saved_data["translations"]["de"]["title"] == "Testgeheimnis"

    @patch("mystery_agents.tools.image_upload.get_storage_bucket")
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
            "translation_result_es": "this is { not valid json",
        }

        tool_context = make_tool_context(state)
        result = publish_mystery(_make_mystery_json(), "", tool_context)
        result_data = json.loads(result)

        assert result_data["status"] == "success"
        saved_data = mock_db.collection.return_value.document.return_value.set.call_args[0][0]
        assert "ja" in saved_data["translations"]
        assert "es" not in saved_data["translations"]

    @patch("mystery_agents.tools.image_upload.get_storage_bucket")
    @patch("mystery_agents.tools.publisher_tools.get_firestore_client")
    def test_all_three_languages_in_translations(
        self, mock_get_db, mock_get_bucket
    ):
        """Should include all 3 languages when all translations succeed."""
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        mock_get_bucket.return_value = MagicMock()

        state = {}
        for lang in ["ja", "es", "de"]:
            state[f"translation_result_{lang}"] = json.dumps({
                "title": f"Title in {lang}",
                "summary": f"Summary in {lang}",
            })

        tool_context = make_tool_context(state)
        result = publish_mystery(_make_mystery_json(), "", tool_context)
        result_data = json.loads(result)

        assert result_data["status"] == "success"
        saved_data = mock_db.collection.return_value.document.return_value.set.call_args[0][0]
        assert set(saved_data["translations"].keys()) == {"ja", "es", "de"}


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

    @patch("mystery_agents.tools.image_upload.get_storage_bucket")
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

        tool_context = make_tool_context(state)
        result = publish_mystery(_make_mystery_json(), "", tool_context)
        result_data = json.loads(result)

        assert result_data["status"] == "success"
        saved_data = mock_db.collection.return_value.document.return_value.set.call_args[0][0]

        assert saved_data["translations"]["ja"]["title"] == "日本語タイトル"
        assert saved_data["translations"]["es"]["title"] == "Título en español"
        assert saved_data["translations"]["de"]["title"] == "Deutscher Titel"

    @patch("mystery_agents.tools.image_upload.get_storage_bucket")
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

        tool_context = make_tool_context(state)
        with caplog.at_level(logging.INFO, logger="mystery_agents.tools.publisher_tools"):
            publish_mystery(_make_mystery_json(), "", tool_context)

        assert any("Translations collected" in msg for msg in caplog.messages)
        assert any("['ja']" in msg for msg in caplog.messages)


class TestPublisherTranslationDiagnostics:
    """翻訳収集の DEBUG 診断ログテスト。"""

    @patch("mystery_agents.tools.image_upload.get_storage_bucket")
    @patch("mystery_agents.tools.publisher_tools.get_firestore_client")
    def test_logs_none_state_as_diagnostic(
        self, mock_get_db, mock_get_bucket, caplog
    ):
        """translation_result が None の場合に診断ログが出力されること。"""
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        mock_get_bucket.return_value = MagicMock()

        # es のみセット、ja と de は未設定（None）
        state = {
            "translation_result_es": json.dumps({
                "title": "Título",
                "summary": "Resumen de prueba",
            }),
        }

        tool_context = make_tool_context(state)
        with caplog.at_level(logging.DEBUG, logger="mystery_agents.tools.publisher_tools"):
            publish_mystery(_make_mystery_json(), "", tool_context)

        # None のキーに対する診断ログ
        diag_msgs = [m for m in caplog.messages if "translation_diag" in m]
        assert any("ja" in m and "未設定または None" in m for m in diag_msgs)
        assert any("de" in m and "未設定または None" in m for m in diag_msgs)
        # 値がある es に対する診断ログ
        assert any("es" in m and "type=str" in m for m in diag_msgs)

    @patch("mystery_agents.tools.image_upload.get_storage_bucket")
    @patch("mystery_agents.tools.publisher_tools.get_firestore_client")
    def test_logs_empty_string_as_diagnostic(
        self, mock_get_db, mock_get_bucket, caplog
    ):
        """translation_result が空文字列の場合に診断ログが出力されること。"""
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        mock_get_bucket.return_value = MagicMock()

        state = {
            "translation_result_ja": "",
            "translation_result_es": json.dumps({
                "title": "Título",
                "summary": "Resumen de prueba",
            }),
        }

        tool_context = make_tool_context(state)
        with caplog.at_level(logging.DEBUG, logger="mystery_agents.tools.publisher_tools"):
            publish_mystery(_make_mystery_json(), "", tool_context)

        diag_msgs = [m for m in caplog.messages if "translation_diag" in m]
        assert any("ja" in m and "空文字列" in m for m in diag_msgs)

    @patch("mystery_agents.tools.image_upload.get_storage_bucket")
    @patch("mystery_agents.tools.publisher_tools.get_firestore_client")
    def test_logs_json_parse_failure_with_length(
        self, mock_get_db, mock_get_bucket, caplog
    ):
        """JSON パース失敗時に文字列長がログに含まれること。"""
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        mock_get_bucket.return_value = MagicMock()

        broken_json = "this is { not valid json at all" * 10
        state = {
            "translation_result_es": broken_json,
        }

        tool_context = make_tool_context(state)
        with caplog.at_level(logging.WARNING, logger="mystery_agents.tools.publisher_tools"):
            publish_mystery(_make_mystery_json(), "", tool_context)

        assert any(
            f"len={len(broken_json)}" in m
            for m in caplog.messages
            if "Failed to parse" in m
        )


class TestPublisherLanguageValidation:
    """翻訳言語バリデーションによる拒否テスト。"""

    @patch("mystery_agents.tools.image_upload.get_storage_bucket")
    @patch("mystery_agents.tools.publisher_tools.get_firestore_client")
    def test_rejects_english_text_as_spanish(
        self, mock_get_db, mock_get_bucket
    ):
        """英語テキストをスペイン語翻訳として拒否すること。"""
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        mock_get_bucket.return_value = MagicMock()

        # 英語テキストがそのままスペイン語翻訳として返された場合
        english_as_spanish = {
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
            "translation_result_es": json.dumps(english_as_spanish),
        }

        tool_context = make_tool_context(state)
        with patch("shared.pipeline_failure.log_pipeline_failure"):
            result = publish_mystery(_make_mystery_json(), "", tool_context)
        result_data = json.loads(result)

        assert result_data["status"] == "success"
        saved_data = mock_db.collection.return_value.document.return_value.set.call_args[0][0]

        # 日本語は通過、スペイン語は拒否されること
        assert "ja" in saved_data["translations"]
        assert "es" not in saved_data["translations"]

    @patch("mystery_agents.tools.image_upload.get_storage_bucket")
    @patch("mystery_agents.tools.publisher_tools.get_firestore_client")
    def test_accepts_valid_spanish_translation(
        self, mock_get_db, mock_get_bucket
    ):
        """正常なスペイン語翻訳は通過すること。"""
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        mock_get_bucket.return_value = MagicMock()

        state = {
            "translation_result_es": json.dumps({
                "title": "El barco fantasma del puerto de Boston",
                "summary": "El misterio de un barco que desapareció en 1842",
                "narrative_content": (
                    "Un carguero amarrado en el puerto de Boston desapareció de la noche a la mañana. "
                    "Todos los miembros de la tripulación desaparecieron y el casco nunca fue encontrado. "
                    "Los pescadores locales afirmaron haber avistado un barco fantasma en las noches de niebla, "
                    "pero las autoridades no incluyeron su testimonio en los registros oficiales."
                ),
            }),
        }

        tool_context = make_tool_context(state)
        result = publish_mystery(_make_mystery_json(), "", tool_context)
        result_data = json.loads(result)

        assert result_data["status"] == "success"
        saved_data = mock_db.collection.return_value.document.return_value.set.call_args[0][0]
        assert "es" in saved_data["translations"]

    @patch("mystery_agents.tools.image_upload.get_storage_bucket")
    @patch("mystery_agents.tools.publisher_tools.get_firestore_client")
    def test_logs_warning_on_rejection(
        self, mock_get_db, mock_get_bucket, caplog
    ):
        """拒否時に warning ログが出力されること。"""
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        mock_get_bucket.return_value = MagicMock()

        state = {
            "translation_result_es": json.dumps({
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

        tool_context = make_tool_context(state)
        with caplog.at_level(logging.WARNING, logger="mystery_agents.tools.publisher_tools"):
            with patch("shared.pipeline_failure.log_pipeline_failure"):
                publish_mystery(_make_mystery_json(), "", tool_context)

        assert any("Translation rejected" in msg for msg in caplog.messages)
        assert any("'es'" in msg for msg in caplog.messages)
