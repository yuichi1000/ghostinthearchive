"""Unit tests for podcast_agents/agents/pipeline_gate.py — make_script_gate()."""

from unittest.mock import MagicMock

from podcast_agents.agents.pipeline_gate import make_script_gate


def _make_callback_context(state: dict) -> MagicMock:
    """CallbackContext のフェイクを生成する。"""
    ctx = MagicMock()
    ctx.state = state
    return ctx


class TestMakeScriptGate:
    """make_script_gate() の通過/スキップ判定テスト。"""

    def test_passes_when_creative_content_is_meaningful(self):
        """creative_content に有意なテキストがあれば None を返す（通過）。"""
        gate = make_script_gate()
        ctx = _make_callback_context({"creative_content": "A blog article about ghosts."})
        assert gate(ctx) is None

    def test_skips_when_creative_content_is_empty(self):
        """creative_content が空文字なら Content を返す（スキップ）。"""
        gate = make_script_gate()
        ctx = _make_callback_context({"creative_content": ""})
        result = gate(ctx)
        assert result is not None

    def test_skips_when_creative_content_is_missing(self):
        """creative_content がセッション状態にない場合はスキップ。"""
        gate = make_script_gate()
        ctx = _make_callback_context({})
        result = gate(ctx)
        assert result is not None

    def test_skips_when_creative_content_starts_with_no_content(self):
        """creative_content が NO_CONTENT で始まる場合はスキップ。"""
        gate = make_script_gate()
        ctx = _make_callback_context({"creative_content": "NO_CONTENT: Pipeline failed."})
        result = gate(ctx)
        assert result is not None

    def test_skip_message_contains_no_script(self, caplog):
        """スキップ時のログメッセージに NO_SCRIPT が含まれる。"""
        import logging

        gate = make_script_gate()
        ctx = _make_callback_context({"creative_content": ""})
        with caplog.at_level(logging.WARNING):
            gate(ctx)
        assert any("NO_SCRIPT" in record.message for record in caplog.records)

    def test_each_call_returns_independent_gate(self):
        """make_script_gate() は呼び出しごとに独立したゲートを返す。"""
        gate_a = make_script_gate()
        gate_b = make_script_gate()
        assert gate_a is not gate_b
