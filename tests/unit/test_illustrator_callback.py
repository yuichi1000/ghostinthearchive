"""Unit tests for Illustrator before_tool_callback (generate_image call limiter)."""

from unittest.mock import MagicMock

import pytest

from mystery_agents.agents.illustrator import (
    MAX_GENERATE_IMAGE_CALLS,
    _STATE_KEY,
    _limit_generate_image_calls,
)


@pytest.fixture
def mock_tool_context():
    """Create a mock ToolContext with a dict-like state."""
    ctx = MagicMock()
    ctx.state = {}
    return ctx


@pytest.fixture
def mock_generate_image_tool():
    """Create a mock BaseTool with name='generate_image'."""
    tool = MagicMock()
    tool.name = "generate_image"
    return tool


@pytest.fixture
def mock_other_tool():
    """Create a mock BaseTool with a non-generate_image name."""
    tool = MagicMock()
    tool.name = "some_other_tool"
    return tool


class TestLimitGenerateImageCalls:
    """Tests for _limit_generate_image_calls callback."""

    def test_allows_first_call(self, mock_generate_image_tool, mock_tool_context):
        """Should allow the first generate_image call."""
        result = _limit_generate_image_calls(mock_generate_image_tool, {}, mock_tool_context)
        assert result is None
        assert mock_tool_context.state[_STATE_KEY] == 1

    def test_allows_calls_up_to_limit(self, mock_generate_image_tool, mock_tool_context):
        """Should allow calls up to MAX_GENERATE_IMAGE_CALLS."""
        for i in range(MAX_GENERATE_IMAGE_CALLS):
            result = _limit_generate_image_calls(mock_generate_image_tool, {}, mock_tool_context)
            assert result is None
        assert mock_tool_context.state[_STATE_KEY] == MAX_GENERATE_IMAGE_CALLS

    def test_blocks_call_exceeding_limit(self, mock_generate_image_tool, mock_tool_context):
        """Should block the call that exceeds MAX_GENERATE_IMAGE_CALLS."""
        # Exhaust the limit
        for _ in range(MAX_GENERATE_IMAGE_CALLS):
            _limit_generate_image_calls(mock_generate_image_tool, {}, mock_tool_context)

        # Next call should be blocked
        result = _limit_generate_image_calls(mock_generate_image_tool, {}, mock_tool_context)
        assert result is not None
        assert result["status"] == "error"
        assert str(MAX_GENERATE_IMAGE_CALLS) in result["error"]

    def test_ignores_other_tools(self, mock_other_tool, mock_tool_context):
        """Should not limit calls to tools other than generate_image."""
        for _ in range(10):
            result = _limit_generate_image_calls(mock_other_tool, {}, mock_tool_context)
            assert result is None
        assert _STATE_KEY not in mock_tool_context.state

    def test_counter_persists_in_state(self, mock_generate_image_tool, mock_tool_context):
        """Should correctly increment counter across calls."""
        _limit_generate_image_calls(mock_generate_image_tool, {}, mock_tool_context)
        assert mock_tool_context.state[_STATE_KEY] == 1

        _limit_generate_image_calls(mock_generate_image_tool, {}, mock_tool_context)
        assert mock_tool_context.state[_STATE_KEY] == 2

        _limit_generate_image_calls(mock_generate_image_tool, {}, mock_tool_context)
        assert mock_tool_context.state[_STATE_KEY] == 3

    def test_pre_existing_count_respected(self, mock_generate_image_tool, mock_tool_context):
        """Should respect a pre-existing count in state."""
        mock_tool_context.state[_STATE_KEY] = MAX_GENERATE_IMAGE_CALLS
        result = _limit_generate_image_calls(mock_generate_image_tool, {}, mock_tool_context)
        assert result is not None
        assert result["status"] == "error"

    def test_max_calls_constant_is_3(self):
        """MAX_GENERATE_IMAGE_CALLS should be 3."""
        assert MAX_GENERATE_IMAGE_CALLS == 3
