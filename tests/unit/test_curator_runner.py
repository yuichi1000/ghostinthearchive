"""Unit tests for curator_agents/runner.py — ADK 軽量実行ヘルパー。"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest


class TestRunSingleAgent:
    """run_single_agent() のテスト。"""

    @pytest.mark.asyncio
    async def test_collects_text_from_events(self):
        """Should concatenate text from all event parts."""
        # 2つのイベントを返すモック
        event1 = MagicMock()
        part1 = MagicMock()
        part1.text = "Hello "
        event1.content.parts = [part1]

        event2 = MagicMock()
        part2 = MagicMock()
        part2.text = "World"
        event2.content.parts = [part2]

        async def mock_run_async(**kwargs):
            yield event1
            yield event2

        with patch("curator_agents.runner.Runner") as MockRunner, \
             patch("curator_agents.runner.InMemorySessionService") as MockSession:
            mock_runner = MagicMock()
            mock_runner.run_async = mock_run_async
            MockRunner.return_value = mock_runner
            mock_session = AsyncMock()
            MockSession.return_value = mock_session

            from curator_agents.runner import run_single_agent

            result = await run_single_agent(
                MagicMock(),
                app_name="test_app",
                user_id="user1",
                session_id="sess1",
                state={"key": "value"},
                user_message="test message",
            )

        assert result == "Hello World"
        # セッション作成時に state が渡されることを検証
        mock_session.create_session.assert_called_once()
        call_kwargs = mock_session.create_session.call_args.kwargs
        assert call_kwargs["state"] == {"key": "value"}
        assert call_kwargs["user_id"] == "user1"

    @pytest.mark.asyncio
    async def test_returns_empty_string_when_no_events(self):
        """Should return empty string when agent produces no output."""

        async def mock_run_async(**kwargs):
            return
            yield  # noqa: RET504 — async generator requires yield

        with patch("curator_agents.runner.Runner") as MockRunner, \
             patch("curator_agents.runner.InMemorySessionService") as MockSession:
            mock_runner = MagicMock()
            mock_runner.run_async = mock_run_async
            MockRunner.return_value = mock_runner
            mock_session = AsyncMock()
            MockSession.return_value = mock_session

            from curator_agents.runner import run_single_agent

            result = await run_single_agent(
                MagicMock(),
                app_name="test_app",
                user_id="user1",
                session_id="sess1",
                state={},
                user_message="test",
            )

        assert result == ""

    @pytest.mark.asyncio
    async def test_skips_events_without_content(self):
        """Should skip events with no content or no parts."""
        # content が None のイベント
        event_no_content = MagicMock()
        event_no_content.content = None

        # content.parts が None のイベント
        event_no_parts = MagicMock()
        event_no_parts.content.parts = None

        # 正常なイベント
        event_ok = MagicMock()
        part = MagicMock()
        part.text = "result"
        event_ok.content.parts = [part]

        async def mock_run_async(**kwargs):
            yield event_no_content
            yield event_no_parts
            yield event_ok

        with patch("curator_agents.runner.Runner") as MockRunner, \
             patch("curator_agents.runner.InMemorySessionService") as MockSession:
            mock_runner = MagicMock()
            mock_runner.run_async = mock_run_async
            MockRunner.return_value = mock_runner
            mock_session = AsyncMock()
            MockSession.return_value = mock_session

            from curator_agents.runner import run_single_agent

            result = await run_single_agent(
                MagicMock(),
                app_name="test_app",
                user_id="u",
                session_id="s",
                state={},
                user_message="msg",
            )

        assert result == "result"
