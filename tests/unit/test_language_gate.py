"""Unit tests for language gate callbacks.

make_language_gate と make_debate_gate のテスト。
before_agent_callback として機能し、未選択言語のエージェントをスキップする。

注意: conftest.py で google.genai.types がモックされるため、
types.Content() は MagicMock を返す。スキップ判定は「None でないこと」で検証する。
"""

from unittest.mock import MagicMock

import pytest

from mystery_agents.agents.language_gate import make_debate_gate, make_language_gate


@pytest.fixture
def mock_callback_context():
    """CallbackContext のモックを生成する。"""
    ctx = MagicMock()
    ctx.state = {}
    return ctx


class TestMakeLanguageGate:
    """make_language_gate のテスト。"""

    def test_selected_language_returns_none(self, mock_callback_context):
        """選択言語に含まれる場合は None を返す（実行続行）。"""
        mock_callback_context.state = {"selected_languages": ["en", "de"]}
        gate = make_language_gate("en")
        result = gate(mock_callback_context)
        assert result is None

    def test_unselected_language_returns_skip(self, mock_callback_context):
        """選択言語に含まれない場合は非 None を返す（スキップ）。"""
        mock_callback_context.state = {"selected_languages": ["en", "de"]}
        gate = make_language_gate("fr")
        result = gate(mock_callback_context)
        assert result is not None

    def test_default_en_only_when_not_set(self, mock_callback_context):
        """selected_languages 未設定時は en のみ実行。"""
        mock_callback_context.state = {}
        gate_en = make_language_gate("en")
        gate_de = make_language_gate("de")
        assert gate_en(mock_callback_context) is None
        assert gate_de(mock_callback_context) is not None

    def test_invalid_type_fallback_to_en(self, mock_callback_context):
        """selected_languages が不正な型の場合は en にフォールバック。"""
        mock_callback_context.state = {"selected_languages": "not_a_list"}
        gate_en = make_language_gate("en")
        gate_de = make_language_gate("de")
        assert gate_en(mock_callback_context) is None
        assert gate_de(mock_callback_context) is not None

    def test_all_languages_selected(self, mock_callback_context):
        """全言語選択時は全て None を返す。"""
        mock_callback_context.state = {
            "selected_languages": ["en", "de", "es", "fr", "nl", "pt"]
        }
        for lang in ["en", "de", "es", "fr", "nl", "pt"]:
            gate = make_language_gate(lang)
            assert gate(mock_callback_context) is None


class TestMakeDebateGate:
    """make_debate_gate のテスト。"""

    def test_two_languages_selected_returns_none(self, mock_callback_context):
        """2言語以上 + 選択済み → None（実行）。"""
        mock_callback_context.state = {"selected_languages": ["en", "de"]}
        gate = make_debate_gate("en")
        result = gate(mock_callback_context)
        assert result is None

    def test_single_language_returns_skip(self, mock_callback_context):
        """1言語のみ → 非 None（スキップ）。"""
        mock_callback_context.state = {"selected_languages": ["en"]}
        gate = make_debate_gate("en")
        result = gate(mock_callback_context)
        assert result is not None

    def test_unselected_language_returns_skip(self, mock_callback_context):
        """選択されていない言語 → 非 None（スキップ）。"""
        mock_callback_context.state = {"selected_languages": ["en", "de"]}
        gate = make_debate_gate("fr")
        result = gate(mock_callback_context)
        assert result is not None

    def test_default_single_en_skips(self, mock_callback_context):
        """デフォルト（en のみ）の場合はスキップ。"""
        mock_callback_context.state = {}
        gate = make_debate_gate("en")
        result = gate(mock_callback_context)
        assert result is not None

    def test_invalid_type_fallback(self, mock_callback_context):
        """不正な型の場合はデフォルト en のみ → スキップ。"""
        mock_callback_context.state = {"selected_languages": 42}
        gate = make_debate_gate("en")
        result = gate(mock_callback_context)
        assert result is not None

    def test_three_languages_all_run(self, mock_callback_context):
        """3言語選択時は全て None を返す。"""
        mock_callback_context.state = {"selected_languages": ["en", "de", "fr"]}
        for lang in ["en", "de", "fr"]:
            gate = make_debate_gate(lang)
            assert gate(mock_callback_context) is None
