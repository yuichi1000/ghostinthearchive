"""Unit tests for Armchair Polymath agent configuration and callbacks."""

from unittest.mock import MagicMock

import pytest

from mystery_agents.agents.armchair_polymath import (
    _COUNT_WORDS_CALL_KEY,
    _MAX_COUNT_WORDS_CALLS,
    armchair_polymath_agent,
    log_polymath_tool_call,
)


class TestArmchairPolymathTools:
    def test_tools_include_get_search_metadata(self):
        """armchair_polymath_agent の tools に get_search_metadata が含まれる。"""
        tool_functions = [t for t in armchair_polymath_agent.tools if callable(t)]
        tool_names = [t.__name__ for t in tool_functions]
        assert "get_search_metadata" in tool_names


# =====================================================================
# count_words 呼び出し上限ガード
# =====================================================================


@pytest.fixture
def mock_tool_context():
    """Create a mock ToolContext with a dict-like state."""
    ctx = MagicMock()
    ctx.state = {}
    return ctx


@pytest.fixture
def mock_count_words_tool():
    """Create a mock BaseTool with name='count_words'."""
    tool = MagicMock()
    tool.name = "count_words"
    return tool


@pytest.fixture
def mock_other_tool():
    """Create a mock BaseTool with a non-count_words name."""
    tool = MagicMock()
    tool.name = "save_structured_report"
    return tool


class TestCountWordsLimiter:
    """Tests for count_words call limiting in log_polymath_tool_call."""

    def test_allows_count_words_up_to_limit(
        self, mock_count_words_tool, mock_tool_context,
    ):
        """Should allow count_words calls up to _MAX_COUNT_WORDS_CALLS."""
        for _ in range(_MAX_COUNT_WORDS_CALLS):
            result = log_polymath_tool_call(
                mock_count_words_tool, {"text": "report"}, mock_tool_context,
            )
            assert result is None

    def test_blocks_count_words_exceeding_limit(
        self, mock_count_words_tool, mock_tool_context,
    ):
        """Should return a short-circuit result when count_words exceeds the limit."""
        # 上限まで呼ぶ
        for _ in range(_MAX_COUNT_WORDS_CALLS):
            log_polymath_tool_call(
                mock_count_words_tool, {"text": "report"}, mock_tool_context,
            )

        # 上限+1回目はブロックされる
        result = log_polymath_tool_call(
            mock_count_words_tool, {"text": "report"}, mock_tool_context,
        )
        assert result is not None
        assert result["within_range"] is True
        assert "save_structured_report" in result["message"]
        # short-circuit 時に _word_count_verified が設定され、
        # save_structured_report のフラグチェックを通過できること
        assert mock_tool_context.state["_word_count_verified"] is True

    def test_does_not_limit_other_tools(
        self, mock_other_tool, mock_tool_context,
    ):
        """Should not limit calls to tools other than count_words."""
        for _ in range(_MAX_COUNT_WORDS_CALLS + 5):
            result = log_polymath_tool_call(
                mock_other_tool, {}, mock_tool_context,
            )
            assert result is None

    def test_count_words_counter_independent_from_general_counter(
        self, mock_count_words_tool, mock_other_tool, mock_tool_context,
    ):
        """Should track count_words calls separately from the general tool call counter."""
        # 他のツールを多数回呼んでも count_words カウンターに影響しない
        for _ in range(10):
            log_polymath_tool_call(mock_other_tool, {}, mock_tool_context)

        # count_words はまだ呼べるはず
        result = log_polymath_tool_call(
            mock_count_words_tool, {"text": "report"}, mock_tool_context,
        )
        assert result is None

    def test_pre_existing_count_at_limit_blocks_immediately(
        self, mock_count_words_tool, mock_tool_context,
    ):
        """Should block immediately when state already has count at the limit."""
        mock_tool_context.state[_COUNT_WORDS_CALL_KEY] = _MAX_COUNT_WORDS_CALLS

        result = log_polymath_tool_call(
            mock_count_words_tool, {"text": "report"}, mock_tool_context,
        )
        assert result is not None
        assert result["within_range"] is True
        assert mock_tool_context.state["_word_count_verified"] is True
