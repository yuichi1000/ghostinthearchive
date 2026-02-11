"""Unit tests for debate whiteboard tools."""

from unittest.mock import MagicMock

from mystery_agents.tools.debate_tools import append_to_whiteboard


class TestAppendToWhiteboard:
    """append_to_whiteboard のテスト。"""

    def _make_tool_context(self, whiteboard=""):
        """ToolContext モックを作成する。"""
        ctx = MagicMock()
        ctx.state = {"debate_whiteboard": whiteboard}
        return ctx

    def test_append_to_empty_whiteboard(self):
        """空のホワイトボードに最初の発言を追記できる。"""
        ctx = self._make_tool_context("")
        result = append_to_whiteboard("English", 1, "Test contribution", ctx)

        assert "### [Round 1] English Perspective" in ctx.state["debate_whiteboard"]
        assert "Test contribution" in ctx.state["debate_whiteboard"]
        assert "English" in result

    def test_accumulation(self):
        """複数の発言が累積される（上書きされない）。"""
        ctx = self._make_tool_context("")

        append_to_whiteboard("English", 1, "English analysis", ctx)
        append_to_whiteboard("German", 1, "German analysis", ctx)

        whiteboard = ctx.state["debate_whiteboard"]
        assert "English Perspective" in whiteboard
        assert "German Perspective" in whiteboard
        assert "English analysis" in whiteboard
        assert "German analysis" in whiteboard

    def test_round_number_in_output(self):
        """ラウンド番号がフォーマットに含まれる。"""
        ctx = self._make_tool_context("")

        append_to_whiteboard("French", 2, "Round 2 contribution", ctx)

        assert "[Round 2]" in ctx.state["debate_whiteboard"]

    def test_key_not_set_uses_default(self):
        """debate_whiteboard キーが未設定の場合、空文字列がデフォルト。"""
        ctx = MagicMock()
        ctx.state = {}

        append_to_whiteboard("Spanish", 1, "First contribution", ctx)

        assert "### [Round 1] Spanish Perspective" in ctx.state["debate_whiteboard"]
        assert "First contribution" in ctx.state["debate_whiteboard"]

    def test_preserves_existing_content(self):
        """既存コンテンツが保持される。"""
        existing = "### [Round 1] English Perspective\n\nExisting content\n\n"
        ctx = self._make_tool_context(existing)

        append_to_whiteboard("German", 1, "New content", ctx)

        whiteboard = ctx.state["debate_whiteboard"]
        assert "Existing content" in whiteboard
        assert "New content" in whiteboard

    def test_return_message(self):
        """戻り値に speaker と round_number が含まれる。"""
        ctx = self._make_tool_context("")
        result = append_to_whiteboard("Dutch", 2, "contribution", ctx)

        assert "Dutch" in result
        assert "Round 2" in result
