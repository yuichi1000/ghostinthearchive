"""討論収束判定テスト。

check_debate_convergence ツールのロジックを検証する:
- ラウンド1のみ → 継続
- ラウンド2で同内容繰り返し → 収束 + escalate
- ラウンド2で新論点多数 → 継続
- ホワイトボード空 → 継続
- ヘルパー関数（_extract_rounds, _extract_words）の正常動作
"""

from unittest.mock import MagicMock

import pytest

from mystery_agents.tools.debate_tools import (
    _extract_rounds,
    _extract_words,
    check_debate_convergence,
)


@pytest.fixture
def mock_tool_context():
    """ToolContext のモックを生成する。"""
    ctx = MagicMock()
    ctx.state = {}
    ctx.actions = MagicMock()
    ctx.actions.escalate = False
    return ctx


class TestExtractRounds:
    """_extract_rounds ヘルパーのテスト。"""

    def test_empty_whiteboard(self):
        assert _extract_rounds("") == {}

    def test_single_round(self):
        wb = "### [Round 1] English Perspective\n\nSome analysis here.\n\n"
        rounds = _extract_rounds(wb)
        assert 1 in rounds
        assert "Some analysis here" in rounds[1]

    def test_two_rounds(self):
        wb = (
            "### [Round 1] English Perspective\n\nFirst round English.\n\n"
            "### [Round 1] German Perspective\n\nFirst round German.\n\n"
            "### [Round 2] English Perspective\n\nSecond round English.\n\n"
            "### [Round 2] German Perspective\n\nSecond round German.\n\n"
        )
        rounds = _extract_rounds(wb)
        assert len(rounds) == 2
        assert "First round English" in rounds[1]
        assert "First round German" in rounds[1]
        assert "Second round English" in rounds[2]
        assert "Second round German" in rounds[2]


class TestExtractWords:
    """_extract_words ヘルパーのテスト。"""

    def test_empty_text(self):
        assert _extract_words("") == set()

    def test_filters_short_words(self):
        words = _extract_words("a an the cat dog")
        assert "cat" in words
        assert "dog" in words
        assert "a" not in words
        assert "an" not in words

    def test_lowercases(self):
        words = _extract_words("English German FRENCH")
        assert "english" in words
        assert "german" in words
        assert "french" in words


class TestCheckDebateConvergence:
    """check_debate_convergence ツールのテスト。"""

    def test_empty_whiteboard_continues(self, mock_tool_context):
        """ホワイトボードが空 → 継続。"""
        mock_tool_context.state["debate_whiteboard"] = ""
        result = check_debate_convergence(mock_tool_context)
        assert "continue" in result.lower()
        assert not mock_tool_context.actions.escalate

    def test_single_round_continues(self, mock_tool_context):
        """ラウンド1のみ → 継続。"""
        mock_tool_context.state["debate_whiteboard"] = (
            "### [Round 1] English Perspective\n\n"
            "The historical records show a discrepancy in the dates.\n\n"
            "### [Round 1] German Perspective\n\n"
            "German sources confirm the anomaly in colonial records.\n\n"
        )
        result = check_debate_convergence(mock_tool_context)
        assert "continue" in result.lower()
        assert not mock_tool_context.actions.escalate

    def test_converged_same_content(self, mock_tool_context):
        """ラウンド2で同じ内容を繰り返し → 収束 + escalate。"""
        shared_text = (
            "The historical records show a discrepancy in the dates. "
            "German sources confirm the anomaly in colonial records. "
            "The evidence suggests a deliberate omission of key facts."
        )
        mock_tool_context.state["debate_whiteboard"] = (
            f"### [Round 1] English Perspective\n\n{shared_text}\n\n"
            f"### [Round 1] German Perspective\n\n{shared_text}\n\n"
            f"### [Round 2] English Perspective\n\n{shared_text}\n\n"
            f"### [Round 2] German Perspective\n\n{shared_text}\n\n"
        )
        result = check_debate_convergence(mock_tool_context)
        assert "converged" in result.lower()
        assert mock_tool_context.actions.escalate is True

    def test_not_converged_new_arguments(self, mock_tool_context):
        """ラウンド2で全く新しい論点 → 継続。"""
        mock_tool_context.state["debate_whiteboard"] = (
            "### [Round 1] English Perspective\n\n"
            "The historical records show discrepancy dates colonial period.\n\n"
            "### [Round 1] German Perspective\n\n"
            "German sources confirm anomaly colonial records immigration.\n\n"
            "### [Round 2] English Perspective\n\n"
            "Completely different perspective about maritime trade networks "
            "and Portuguese exploration routes through Atlantic ocean. "
            "Sephardic Jewish communities established synagogues throughout "
            "Caribbean islands and maintained correspondence with Amsterdam.\n\n"
            "### [Round 2] German Perspective\n\n"
            "Overlooked archaeological evidence from excavation sites reveals "
            "previously unknown settlement patterns along Mississippi river. "
            "Huguenot refugees brought viticulture techniques and religious "
            "manuscripts documenting persecution experiences.\n\n"
        )
        result = check_debate_convergence(mock_tool_context)
        assert "not converged" in result.lower()
        assert not mock_tool_context.actions.escalate

    def test_no_whiteboard_key(self, mock_tool_context):
        """debate_whiteboard キーが存在しない → 継続。"""
        result = check_debate_convergence(mock_tool_context)
        assert "continue" in result.lower()
        assert not mock_tool_context.actions.escalate
