"""Unit tests for multi-stage scriptwriter tools.

save_script_outline / save_segment / finalize_script の 3 ツールをテストする。
podcast_agents/tools/script_tools.py に追加されるツール群。
"""

import json
from unittest.mock import MagicMock

from podcast_agents.tools.script_tools import (
    save_script_outline,
    save_segment,
    finalize_script,
)


class TestSaveScriptOutline:
    """save_script_outline() のテスト。"""

    def _make_tool_context(self) -> MagicMock:
        ctx = MagicMock()
        ctx.state = {}
        return ctx

    def _make_valid_outline(self) -> dict:
        return {
            "episode_title": "The Vanishing Ship of Boston Harbor",
            "estimated_duration_minutes": 20,
            "total_word_target": 3000,
            "segments": [
                {
                    "type": "intro",
                    "label": "Introduction",
                    "key_points": ["Hook about the mystery", "Set the scene"],
                    "word_target": 300,
                },
                {
                    "type": "body",
                    "label": "Historical Background",
                    "key_points": ["Date and location", "Key figures"],
                    "word_target": 600,
                },
                {
                    "type": "body",
                    "label": "The Heart of the Mystery",
                    "key_points": ["Evidence analysis"],
                    "word_target": 800,
                },
                {
                    "type": "outro",
                    "label": "Closing",
                    "key_points": ["Lingering questions"],
                    "word_target": 300,
                },
            ],
        }

    def test_saves_outline_to_state(self):
        """正常な JSON を state["structured_outline"] に保存する。"""
        outline = self._make_valid_outline()
        ctx = self._make_tool_context()

        result = save_script_outline(json.dumps(outline), ctx)
        result_data = json.loads(result)

        assert result_data["status"] == "success"
        assert ctx.state["structured_outline"] == outline

    def test_initializes_segment_buffer(self):
        """segment_buffer を空リストで初期化する。"""
        outline = self._make_valid_outline()
        ctx = self._make_tool_context()

        save_script_outline(json.dumps(outline), ctx)

        assert ctx.state["segment_buffer"] == []

    def test_returns_segment_count(self):
        """セグメント数を返す。"""
        outline = self._make_valid_outline()
        ctx = self._make_tool_context()

        result = save_script_outline(json.dumps(outline), ctx)
        result_data = json.loads(result)

        assert result_data["segment_count"] == 4

    def test_returns_total_word_target(self):
        """合計語数ターゲットを返す。"""
        outline = self._make_valid_outline()
        ctx = self._make_tool_context()

        result = save_script_outline(json.dumps(outline), ctx)
        result_data = json.loads(result)

        assert result_data["total_word_target"] == 3000

    def test_invalid_json_returns_error(self):
        """不正な JSON はエラーを返す。"""
        ctx = self._make_tool_context()

        result = save_script_outline("not valid json {", ctx)
        result_data = json.loads(result)

        assert result_data["status"] == "error"
        assert "Invalid JSON" in result_data["error"]
        assert "structured_outline" not in ctx.state

    def test_missing_segments_returns_error(self):
        """segments がない場合はエラーを返す。"""
        ctx = self._make_tool_context()

        result = save_script_outline(
            json.dumps({"episode_title": "Test"}), ctx
        )
        result_data = json.loads(result)

        assert result_data["status"] == "error"
        assert "segments" in result_data["error"]

    def test_empty_segments_returns_error(self):
        """segments が空配列の場合はエラーを返す。"""
        ctx = self._make_tool_context()

        result = save_script_outline(
            json.dumps({"episode_title": "Test", "segments": []}), ctx
        )
        result_data = json.loads(result)

        assert result_data["status"] == "error"

    def test_warns_on_missing_key_points(self):
        """key_points 欠如のセグメントで warning を含む。"""
        ctx = self._make_tool_context()
        outline = {
            "episode_title": "Test",
            "segments": [
                {"type": "intro", "label": "Intro", "word_target": 300},
            ],
        }

        result = save_script_outline(json.dumps(outline), ctx)
        result_data = json.loads(result)

        assert result_data["status"] == "success"
        assert any("key_points" in w for w in result_data["warnings"])


class TestSaveSegment:
    """save_segment() のテスト。"""

    def _make_tool_context(self, with_buffer: bool = True) -> MagicMock:
        ctx = MagicMock()
        ctx.state = {}
        if with_buffer:
            ctx.state["segment_buffer"] = []
        return ctx

    def _make_valid_segment(self) -> dict:
        return {
            "type": "intro",
            "label": "Introduction",
            "text": "Welcome to Ghost in the Archive. Tonight we explore a mystery...",
            "notes": "SFX: archive door creaking",
        }

    def test_appends_to_buffer(self):
        """セグメントを buffer に追加する。"""
        segment = self._make_valid_segment()
        ctx = self._make_tool_context()

        result = save_segment(json.dumps(segment), ctx)
        result_data = json.loads(result)

        assert result_data["status"] == "success"
        assert len(ctx.state["segment_buffer"]) == 1
        assert ctx.state["segment_buffer"][0] == segment

    def test_accumulates_segments(self):
        """複数回呼び出しで累積する（上書きしない）。"""
        ctx = self._make_tool_context()
        seg1 = {"type": "intro", "label": "Intro", "text": "Welcome..."}
        seg2 = {"type": "body", "label": "Body", "text": "In 1842..."}

        save_segment(json.dumps(seg1), ctx)
        save_segment(json.dumps(seg2), ctx)

        assert len(ctx.state["segment_buffer"]) == 2
        assert ctx.state["segment_buffer"][0]["type"] == "intro"
        assert ctx.state["segment_buffer"][1]["type"] == "body"

    def test_returns_segment_index(self):
        """セグメントのインデックスを返す。"""
        ctx = self._make_tool_context()
        segment = self._make_valid_segment()

        result = save_segment(json.dumps(segment), ctx)
        result_data = json.loads(result)

        assert result_data["segment_index"] == 0

    def test_returns_word_count(self):
        """セグメントの語数を返す。"""
        ctx = self._make_tool_context()
        segment = self._make_valid_segment()

        result = save_segment(json.dumps(segment), ctx)
        result_data = json.loads(result)

        assert result_data["word_count"] > 0

    def test_returns_cumulative_word_count(self):
        """累積語数を返す。"""
        ctx = self._make_tool_context()
        seg1 = {"type": "intro", "label": "Intro", "text": "one two three"}
        seg2 = {"type": "body", "label": "Body", "text": "four five six seven"}

        save_segment(json.dumps(seg1), ctx)
        result = save_segment(json.dumps(seg2), ctx)
        result_data = json.loads(result)

        assert result_data["cumulative_word_count"] == 7

    def test_invalid_json_returns_error(self):
        """不正な JSON はエラーを返す。"""
        ctx = self._make_tool_context()

        result = save_segment("not valid json {", ctx)
        result_data = json.loads(result)

        assert result_data["status"] == "error"
        assert "Invalid JSON" in result_data["error"]

    def test_missing_text_returns_error(self):
        """text 欠如はエラーを返す。"""
        ctx = self._make_tool_context()

        result = save_segment(
            json.dumps({"type": "intro", "label": "Intro"}), ctx
        )
        result_data = json.loads(result)

        assert result_data["status"] == "error"
        assert "text" in result_data["error"]

    def test_empty_text_returns_error(self):
        """空テキストはエラーを返す。"""
        ctx = self._make_tool_context()

        result = save_segment(
            json.dumps({"type": "intro", "label": "Intro", "text": "  "}), ctx
        )
        result_data = json.loads(result)

        assert result_data["status"] == "error"
        assert "text" in result_data["error"]

    def test_auto_initializes_buffer(self):
        """segment_buffer 未初期化でも自動初期化する。"""
        ctx = self._make_tool_context(with_buffer=False)
        segment = self._make_valid_segment()

        result = save_segment(json.dumps(segment), ctx)
        result_data = json.loads(result)

        assert result_data["status"] == "success"
        assert len(ctx.state["segment_buffer"]) == 1


class TestFinalizeScript:
    """finalize_script() のテスト。"""

    def _make_tool_context(
        self,
        segments: list | None = None,
        outline: dict | None = None,
    ) -> MagicMock:
        ctx = MagicMock()
        ctx.state = {}
        if segments is not None:
            ctx.state["segment_buffer"] = segments
        if outline is not None:
            ctx.state["structured_outline"] = outline
        return ctx

    def _make_segments(self) -> list[dict]:
        return [
            {"type": "intro", "label": "Introduction", "text": "Welcome..."},
            {"type": "body", "label": "Background", "text": "In 1842..."},
            {"type": "outro", "label": "Closing", "text": "Until next time..."},
        ]

    def _make_outline(self) -> dict:
        return {
            "episode_title": "The Vanishing Ship",
            "estimated_duration_minutes": 20,
        }

    def test_assembles_structured_script(self):
        """buffer から structured_script を組み立てる。"""
        ctx = self._make_tool_context(
            segments=self._make_segments(),
            outline=self._make_outline(),
        )

        result = finalize_script(ctx)
        result_data = json.loads(result)

        assert result_data["status"] == "success"
        script = ctx.state["structured_script"]
        assert script["episode_title"] == "The Vanishing Ship"
        assert script["estimated_duration_minutes"] == 20
        assert len(script["segments"]) == 3

    def test_uses_episode_title_from_outline(self):
        """episode_title を structured_outline から取得する。"""
        ctx = self._make_tool_context(
            segments=self._make_segments(),
            outline={"episode_title": "Custom Title", "estimated_duration_minutes": 15},
        )

        finalize_script(ctx)

        assert ctx.state["structured_script"]["episode_title"] == "Custom Title"

    def test_returns_segment_count(self):
        """セグメント数を返す。"""
        ctx = self._make_tool_context(
            segments=self._make_segments(),
            outline=self._make_outline(),
        )

        result = finalize_script(ctx)
        result_data = json.loads(result)

        assert result_data["segment_count"] == 3

    def test_returns_total_word_count(self):
        """合計語数を返す。"""
        ctx = self._make_tool_context(
            segments=self._make_segments(),
            outline=self._make_outline(),
        )

        result = finalize_script(ctx)
        result_data = json.loads(result)

        assert result_data["total_word_count"] > 0

    def test_empty_buffer_returns_error(self):
        """buffer が空の場合はエラーを返す。"""
        ctx = self._make_tool_context(segments=[], outline=self._make_outline())

        result = finalize_script(ctx)
        result_data = json.loads(result)

        assert result_data["status"] == "error"
        assert "empty" in result_data["error"].lower()

    def test_missing_buffer_returns_error(self):
        """buffer がない場合はエラーを返す。"""
        ctx = self._make_tool_context(outline=self._make_outline())

        result = finalize_script(ctx)
        result_data = json.loads(result)

        assert result_data["status"] == "error"

    def test_warns_on_missing_intro(self):
        """intro セグメントがない場合は warning を含む。"""
        segments = [
            {"type": "body", "label": "Body", "text": "Content..."},
            {"type": "outro", "label": "Closing", "text": "Bye..."},
        ]
        ctx = self._make_tool_context(
            segments=segments, outline=self._make_outline()
        )

        result = finalize_script(ctx)
        result_data = json.loads(result)

        assert result_data["status"] == "success"
        assert any("intro" in w.lower() for w in result_data["warnings"])

    def test_warns_on_missing_outro(self):
        """outro セグメントがない場合は warning を含む。"""
        segments = [
            {"type": "intro", "label": "Intro", "text": "Welcome..."},
            {"type": "body", "label": "Body", "text": "Content..."},
        ]
        ctx = self._make_tool_context(
            segments=segments, outline=self._make_outline()
        )

        result = finalize_script(ctx)
        result_data = json.loads(result)

        assert result_data["status"] == "success"
        assert any("outro" in w.lower() for w in result_data["warnings"])

    def test_writes_to_structured_script_key(self):
        """state["structured_script"] に保存する（cli.py 互換）。"""
        ctx = self._make_tool_context(
            segments=self._make_segments(),
            outline=self._make_outline(),
        )

        finalize_script(ctx)

        assert "structured_script" in ctx.state
        script = ctx.state["structured_script"]
        assert "segments" in script
        assert "episode_title" in script

    def test_works_without_outline(self):
        """structured_outline がなくてもフォールバックで動作する。"""
        ctx = self._make_tool_context(segments=self._make_segments())

        result = finalize_script(ctx)
        result_data = json.loads(result)

        assert result_data["status"] == "success"
        # デフォルト値が使われる
        script = ctx.state["structured_script"]
        assert "episode_title" in script
