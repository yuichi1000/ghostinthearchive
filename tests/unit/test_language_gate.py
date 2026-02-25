"""Unit tests for language gate callbacks.

make_debate_gate, make_debate_loop_gate のテスト。
before_agent_callback として機能し、討論モードのスキップ条件を制御する。

注意: conftest.py で google.genai.types がモックされるため、
types.Content() は MagicMock を返す。スキップ判定は「None でないこと」で検証する。
"""

from unittest.mock import MagicMock

import pytest

from mystery_agents.agents.language_gate import (
    make_debate_gate,
    make_debate_loop_gate,
)


@pytest.fixture
def mock_callback_context():
    """CallbackContext のモックを生成する。"""
    ctx = MagicMock()
    ctx.state = {}
    return ctx


class TestMakeDebateGate:
    """make_debate_gate のテスト。"""

    def test_two_languages_with_meaningful_analysis(self, mock_callback_context):
        """2言語以上 + 有意な分析あり → None（実行）。"""
        mock_callback_context.state = {
            "selected_languages": ["en", "de"],
            "scholar_analysis_en": "Meaningful English analysis...",
            "scholar_analysis_de": "Meaningful German analysis...",
        }
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

    def test_default_all_languages_passes(self, mock_callback_context):
        """デフォルト（全7言語）の場合、有意な分析があれば通過。"""
        mock_callback_context.state = {
            "scholar_analysis_en": "Detailed analysis...",
        }
        gate = make_debate_gate("en")
        result = gate(mock_callback_context)
        assert result is None

    def test_invalid_type_fallback(self, mock_callback_context):
        """不正な型の場合はデフォルト全言語 → 有意な分析がないためスキップ。"""
        mock_callback_context.state = {"selected_languages": 42}
        gate = make_debate_gate("en")
        result = gate(mock_callback_context)
        assert result is not None

    def test_three_languages_with_meaningful_analysis_all_run(self, mock_callback_context):
        """3言語選択 + 有意な分析あり → 全て None を返す。"""
        mock_callback_context.state = {
            "selected_languages": ["en", "de", "fr"],
            "scholar_analysis_en": "English analysis...",
            "scholar_analysis_de": "German analysis...",
            "scholar_analysis_fr": "French analysis...",
        }
        for lang in ["en", "de", "fr"]:
            gate = make_debate_gate(lang)
            assert gate(mock_callback_context) is None

    def test_insufficient_data_analysis_skips(self, mock_callback_context):
        """Scholar が INSUFFICIENT_DATA を出力した場合はスキップ。"""
        mock_callback_context.state = {
            "selected_languages": ["en", "de"],
            "scholar_analysis_en": "INSUFFICIENT_DATA: No English-language documents available.",
            "scholar_analysis_de": "Meaningful German analysis...",
        }
        gate_en = make_debate_gate("en")
        assert gate_en(mock_callback_context) is not None

    def test_not_available_analysis_skips(self, mock_callback_context):
        """Scholar が "Not available" の場合はスキップ。"""
        mock_callback_context.state = {
            "selected_languages": ["en", "de"],
            "scholar_analysis_en": "Not available: en was not selected for this investigation.",
            "scholar_analysis_de": "Meaningful German analysis...",
        }
        gate_en = make_debate_gate("en")
        assert gate_en(mock_callback_context) is not None

    def test_meaningful_analysis_passes(self, mock_callback_context):
        """有意な分析がある場合は通過する。"""
        mock_callback_context.state = {
            "selected_languages": ["en", "de"],
            "scholar_analysis_en": "Detailed analysis of English sources...",
        }
        gate_en = make_debate_gate("en")
        assert gate_en(mock_callback_context) is None

    def test_empty_analysis_skips(self, mock_callback_context):
        """分析が空文字列の場合はスキップ。"""
        mock_callback_context.state = {
            "selected_languages": ["en", "de"],
            "scholar_analysis_en": "",
        }
        gate_en = make_debate_gate("en")
        assert gate_en(mock_callback_context) is not None


class TestMakeDebateLoopGate:
    """make_debate_loop_gate のテスト。"""

    def test_two_meaningful_analyses_passes(self, mock_callback_context):
        """有意な分析が2言語以上 → None（通過）。"""
        mock_callback_context.state = {
            "selected_languages": ["en", "de"],
            "scholar_analysis_en": "English analysis with substance...",
            "scholar_analysis_de": "German analysis with substance...",
        }
        gate = make_debate_loop_gate()
        assert gate(mock_callback_context) is None

    def test_single_meaningful_analysis_skips(self, mock_callback_context):
        """有意な分析が1言語のみ → 非 None（スキップ）。"""
        mock_callback_context.state = {
            "selected_languages": ["en", "de"],
            "scholar_analysis_en": "English analysis...",
            "scholar_analysis_de": "INSUFFICIENT_DATA: No documents.",
        }
        gate = make_debate_loop_gate()
        assert gate(mock_callback_context) is not None

    def test_all_insufficient_data_skips(self, mock_callback_context):
        """全言語 INSUFFICIENT_DATA → スキップ。"""
        mock_callback_context.state = {
            "selected_languages": ["en", "de", "fr"],
            "scholar_analysis_en": "INSUFFICIENT_DATA: No documents.",
            "scholar_analysis_de": "INSUFFICIENT_DATA: No documents.",
            "scholar_analysis_fr": "INSUFFICIENT_DATA: No documents.",
        }
        gate = make_debate_loop_gate()
        assert gate(mock_callback_context) is not None

    def test_not_available_counted_as_not_meaningful(self, mock_callback_context):
        """'Not available' はカウントされない。"""
        mock_callback_context.state = {
            "selected_languages": ["en", "de"],
            "scholar_analysis_en": "Real analysis...",
            "scholar_analysis_de": "Not available: de was not selected.",
        }
        gate = make_debate_loop_gate()
        assert gate(mock_callback_context) is not None

    def test_three_meaningful_passes(self, mock_callback_context):
        """3言語で有意な分析 → 通過。"""
        mock_callback_context.state = {
            "selected_languages": ["en", "de", "fr"],
            "scholar_analysis_en": "English findings...",
            "scholar_analysis_de": "German findings...",
            "scholar_analysis_fr": "French findings...",
        }
        gate = make_debate_loop_gate()
        assert gate(mock_callback_context) is None

    def test_default_all_languages_with_one_analysis_skips(self, mock_callback_context):
        """デフォルト（全7言語）で有意な分析が1言語のみ → スキップ。"""
        mock_callback_context.state = {
            "scholar_analysis_en": "English analysis...",
        }
        gate = make_debate_loop_gate()
        assert gate(mock_callback_context) is not None

    def test_invalid_type_fallback(self, mock_callback_context):
        """selected_languages が不正な型 → フォールバックしてスキップ。"""
        mock_callback_context.state = {"selected_languages": 42}
        gate = make_debate_loop_gate()
        assert gate(mock_callback_context) is not None

    def test_missing_analysis_key_not_meaningful(self, mock_callback_context):
        """分析キーがセッション状態に存在しない場合は有意でない。"""
        mock_callback_context.state = {
            "selected_languages": ["en", "de"],
            "scholar_analysis_en": "English analysis...",
            # scholar_analysis_de は存在しない
        }
        gate = make_debate_loop_gate()
        assert gate(mock_callback_context) is not None
