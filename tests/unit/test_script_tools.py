"""Unit tests for podcast_agents/tools/script_tools.py - save_podcast_script."""

import json
from unittest.mock import MagicMock

from podcast_agents.tools.script_tools import save_podcast_script


class TestSavePodcastScript:
    """Tests for save_podcast_script()."""

    def _make_tool_context(self) -> MagicMock:
        ctx = MagicMock()
        ctx.state = {}
        return ctx

    def _make_valid_script(self) -> dict:
        return {
            "episode_title": "The Vanishing Ship of Boston Harbor",
            "estimated_duration_minutes": 20,
            "segments": [
                {
                    "type": "intro",
                    "label": "Introduction",
                    "text": "Welcome to Ghost in the Archive...",
                    "notes": "SFX: archive door",
                },
                {
                    "type": "body",
                    "label": "Historical Background",
                    "text": "In the spring of 1842...",
                    "notes": "",
                },
                {
                    "type": "outro",
                    "label": "Closing",
                    "text": "Until next time, keep digging...",
                    "notes": "SFX: lingering sound",
                },
            ],
        }

    def test_saves_to_session_state(self):
        """正常な JSON を session state に保存する。"""
        script = self._make_valid_script()
        ctx = self._make_tool_context()

        result = save_podcast_script(json.dumps(script), ctx)
        result_data = json.loads(result)

        assert result_data["status"] == "success"
        assert "structured_script" in ctx.state
        assert ctx.state["structured_script"] == script

    def test_returns_segment_count(self):
        """セグメント数を返す。"""
        script = self._make_valid_script()
        ctx = self._make_tool_context()

        result = save_podcast_script(json.dumps(script), ctx)
        result_data = json.loads(result)

        assert result_data["segment_count"] == 3

    def test_returns_episode_title(self):
        """エピソードタイトルを返す。"""
        script = self._make_valid_script()
        ctx = self._make_tool_context()

        result = save_podcast_script(json.dumps(script), ctx)
        result_data = json.loads(result)

        assert result_data["episode_title"] == "The Vanishing Ship of Boston Harbor"

    def test_returns_estimated_duration(self):
        """想定再生時間を返す。"""
        script = self._make_valid_script()
        ctx = self._make_tool_context()

        result = save_podcast_script(json.dumps(script), ctx)
        result_data = json.loads(result)

        assert result_data["estimated_duration_minutes"] == 20

    def test_invalid_json_returns_error(self):
        """不正な JSON はエラーを返す。"""
        ctx = self._make_tool_context()

        result = save_podcast_script("not valid json {", ctx)
        result_data = json.loads(result)

        assert result_data["status"] == "error"
        assert "Invalid JSON" in result_data["error"]
        assert "structured_script" not in ctx.state

    def test_missing_segments_returns_error(self):
        """segments がない場合はエラーを返す。"""
        ctx = self._make_tool_context()
        script = {"episode_title": "Test", "estimated_duration_minutes": 10}

        result = save_podcast_script(json.dumps(script), ctx)
        result_data = json.loads(result)

        assert result_data["status"] == "error"
        assert "segments" in result_data["error"]

    def test_empty_segments_returns_error(self):
        """segments が空配列の場合はエラーを返す。"""
        ctx = self._make_tool_context()
        script = {
            "episode_title": "Test",
            "estimated_duration_minutes": 10,
            "segments": [],
        }

        result = save_podcast_script(json.dumps(script), ctx)
        result_data = json.loads(result)

        assert result_data["status"] == "error"

    def test_warns_on_missing_episode_title(self):
        """episode_title 欠如で warning を含む。"""
        ctx = self._make_tool_context()
        script = {
            "segments": [
                {"type": "intro", "label": "Intro", "text": "Hello"},
            ],
        }

        result = save_podcast_script(json.dumps(script), ctx)
        result_data = json.loads(result)

        assert result_data["status"] == "success"
        assert any("episode_title" in w for w in result_data["warnings"])

    def test_warns_on_invalid_segment_type(self):
        """不正なセグメントタイプで warning を含む。"""
        ctx = self._make_tool_context()
        script = {
            "episode_title": "Test",
            "segments": [
                {"type": "invalid_type", "label": "Bad", "text": "Hello"},
            ],
        }

        result = save_podcast_script(json.dumps(script), ctx)
        result_data = json.loads(result)

        assert result_data["status"] == "success"
        assert any("invalid type" in w for w in result_data["warnings"])

    def test_warns_on_empty_segment_text(self):
        """空テキストのセグメントで warning を含む。"""
        ctx = self._make_tool_context()
        script = {
            "episode_title": "Test",
            "segments": [
                {"type": "intro", "label": "Intro", "text": ""},
            ],
        }

        result = save_podcast_script(json.dumps(script), ctx)
        result_data = json.loads(result)

        assert result_data["status"] == "success"
        assert any("text is empty" in w for w in result_data["warnings"])
