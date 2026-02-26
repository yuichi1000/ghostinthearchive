"""Unit tests for Polymath before_tool_callback (tool call logging)."""

from unittest.mock import MagicMock

from mystery_agents.agents.armchair_polymath import (
    POLYMATH_MAX_OUTPUT_TOKENS,
    log_polymath_tool_call,
)


class TestLogPolymathToolCall:
    """log_polymath_tool_call コールバックのテスト。"""

    def _make_tool_context(self):
        ctx = MagicMock()
        ctx.state = {}
        return ctx

    def _make_tool(self, name: str):
        tool = MagicMock()
        tool.name = name
        return tool

    def test_returns_none(self):
        """常に None を返す（ツール実行をブロックしない）。"""
        ctx = self._make_tool_context()
        tool = self._make_tool("get_search_metadata")
        result = log_polymath_tool_call(tool, {}, ctx)
        assert result is None

    def test_increments_counter(self):
        """呼び出しごとにカウンターがインクリメントされる。"""
        ctx = self._make_tool_context()
        tool = self._make_tool("get_search_metadata")

        log_polymath_tool_call(tool, {}, ctx)
        assert ctx.state["polymath_tool_call_count"] == 1

        log_polymath_tool_call(tool, {}, ctx)
        assert ctx.state["polymath_tool_call_count"] == 2

    def test_counter_persists_across_tools(self):
        """異なるツールでもカウンターが共有される。"""
        ctx = self._make_tool_context()
        tool_a = self._make_tool("get_search_metadata")
        tool_b = self._make_tool("search_academic_papers")

        log_polymath_tool_call(tool_a, {}, ctx)
        log_polymath_tool_call(tool_b, {"query": "test"}, ctx)
        assert ctx.state["polymath_tool_call_count"] == 2

    def test_truncates_large_args(self, caplog):
        """200字超の args 値がログ上でトランケートされる。"""
        import logging

        ctx = self._make_tool_context()
        tool = self._make_tool("save_structured_report")
        long_value = "x" * 300

        with caplog.at_level(logging.INFO):
            log_polymath_tool_call(tool, {"report_json": long_value}, ctx)

        # ログにトランケートされた値が含まれる（原文300字ではなく切り詰め）
        log_text = caplog.text
        assert "save_structured_report" in log_text
        assert long_value not in log_text  # 元の300字はそのまま出ない
        assert "..." in log_text  # トランケートマーカーがある


class TestPolymathMaxOutputTokens:
    """POLYMATH_MAX_OUTPUT_TOKENS 定数のテスト。"""

    def test_max_output_tokens_value(self):
        """65536 であること。"""
        assert POLYMATH_MAX_OUTPUT_TOKENS == 65536
