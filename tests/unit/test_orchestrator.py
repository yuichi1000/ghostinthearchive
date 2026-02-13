"""Unit tests for shared/orchestrator.py"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from shared.orchestrator import PipelineResult, run_pipeline


def _make_event(author: str | None = None, text: str | None = None):
    """テスト用の ADK イベントを生成する。"""
    event = MagicMock()
    event.author = author

    if text:
        part = MagicMock()
        part.text = text
        event.content = MagicMock()
        event.content.parts = [part]
    else:
        event.content = None

    return event


class TestPipelineResult:
    """PipelineResult のデフォルト値テスト"""

    def test_defaults(self):
        result = PipelineResult(run_id="test-123")
        assert result.run_id == "test-123"
        assert result.mystery_id is None
        assert result.logs == []
        assert result.session_state == {}


class TestRunPipeline:
    """run_pipeline() のテスト"""

    @pytest.mark.asyncio
    @patch("shared.orchestrator.complete_pipeline_run")
    @patch("shared.orchestrator.update_agent_completed")
    @patch("shared.orchestrator.update_agent_started", return_value=0)
    @patch("shared.orchestrator.create_pipeline_run", return_value="run-001")
    async def test_creates_pipeline_run_when_not_provided(
        self, mock_create, mock_started, mock_completed, mock_complete
    ):
        """run_id 未指定時に pipeline_run を自動作成する。"""
        agent = MagicMock()

        # Runner.run_async を AsyncGenerator としてモック
        async def mock_run_async(**kwargs):
            return
            yield  # AsyncGenerator にするために必要

        mock_runner_instance = MagicMock()
        mock_runner_instance.run_async = mock_run_async

        # InMemorySessionService のモック
        mock_session = MagicMock()
        mock_session.state = {}

        mock_session_service = AsyncMock()
        mock_session_service.create_session = AsyncMock()
        mock_session_service.get_session = AsyncMock(return_value=mock_session)

        with patch("shared.orchestrator.Runner", return_value=mock_runner_instance), \
             patch("shared.orchestrator.InMemorySessionService", return_value=mock_session_service):
            result = await run_pipeline(
                agent=agent,
                app_name="test_app",
                user_message="test query",
                initial_state={"key": "value"},
                run_type="blog",
            )

        mock_create.assert_called_once_with("blog", query="test query")
        assert result.run_id == "run-001"

    @pytest.mark.asyncio
    @patch("shared.orchestrator.complete_pipeline_run")
    @patch("shared.orchestrator.update_agent_completed")
    @patch("shared.orchestrator.update_agent_started", return_value=0)
    @patch("shared.orchestrator.create_pipeline_run")
    async def test_skips_create_when_run_id_provided(
        self, mock_create, mock_started, mock_completed, mock_complete
    ):
        """run_id 指定時は pipeline_run を新規作成しない。"""
        agent = MagicMock()

        async def mock_run_async(**kwargs):
            return
            yield

        mock_runner_instance = MagicMock()
        mock_runner_instance.run_async = mock_run_async

        mock_session = MagicMock()
        mock_session.state = {}

        mock_session_service = AsyncMock()
        mock_session_service.create_session = AsyncMock()
        mock_session_service.get_session = AsyncMock(return_value=mock_session)

        with patch("shared.orchestrator.Runner", return_value=mock_runner_instance), \
             patch("shared.orchestrator.InMemorySessionService", return_value=mock_session_service):
            result = await run_pipeline(
                agent=agent,
                app_name="test_app",
                user_message="test query",
                initial_state={},
                run_id="existing-run",
            )

        mock_create.assert_not_called()
        assert result.run_id == "existing-run"

    @pytest.mark.asyncio
    @patch("shared.orchestrator.complete_pipeline_run")
    @patch("shared.orchestrator.update_agent_completed")
    @patch("shared.orchestrator.update_agent_started", return_value=0)
    @patch("shared.orchestrator.create_pipeline_run", return_value="run-002")
    async def test_agent_transitions_tracked(
        self, mock_create, mock_started, mock_completed, mock_complete
    ):
        """エージェント遷移が正しく追跡される。"""
        agent = MagicMock()

        events = [
            _make_event(author="librarian", text="Found documents"),
            _make_event(author="scholar", text="Analysis complete"),
        ]

        async def mock_run_async(**kwargs):
            for e in events:
                yield e

        mock_runner_instance = MagicMock()
        mock_runner_instance.run_async = mock_run_async

        mock_session = MagicMock()
        mock_session.state = {}

        mock_session_service = AsyncMock()
        mock_session_service.create_session = AsyncMock()
        mock_session_service.get_session = AsyncMock(return_value=mock_session)

        with patch("shared.orchestrator.Runner", return_value=mock_runner_instance), \
             patch("shared.orchestrator.InMemorySessionService", return_value=mock_session_service):
            result = await run_pipeline(
                agent=agent,
                app_name="test_app",
                user_message="test",
                initial_state={},
            )

        # librarian → scholar の遷移: started が2回、completed も2回
        assert mock_started.call_count == 2
        assert mock_completed.call_count == 2
        assert len(result.logs) == 2
        assert result.logs[0]["agent_name"] == "librarian"
        assert result.logs[1]["agent_name"] == "scholar"

    @pytest.mark.asyncio
    @patch("shared.orchestrator.complete_pipeline_run")
    @patch("shared.orchestrator.update_agent_completed")
    @patch("shared.orchestrator.update_agent_started", return_value=0)
    @patch("shared.orchestrator.create_pipeline_run", return_value="run-003")
    async def test_skip_authors_are_ignored(
        self, mock_create, mock_started, mock_completed, mock_complete
    ):
        """skip_authors に含まれるエージェントはログ対象外。"""
        agent = MagicMock()

        events = [
            _make_event(author="ghost_commander", text="Starting"),
            _make_event(author="librarian", text="Found documents"),
        ]

        async def mock_run_async(**kwargs):
            for e in events:
                yield e

        mock_runner_instance = MagicMock()
        mock_runner_instance.run_async = mock_run_async

        mock_session = MagicMock()
        mock_session.state = {}

        mock_session_service = AsyncMock()
        mock_session_service.create_session = AsyncMock()
        mock_session_service.get_session = AsyncMock(return_value=mock_session)

        with patch("shared.orchestrator.Runner", return_value=mock_runner_instance), \
             patch("shared.orchestrator.InMemorySessionService", return_value=mock_session_service):
            result = await run_pipeline(
                agent=agent,
                app_name="test_app",
                user_message="test",
                initial_state={},
                skip_authors={"ghost_commander"},
            )

        # ghost_commander はスキップ、librarian のみ記録
        assert mock_started.call_count == 1
        assert len(result.logs) == 1
        assert result.logs[0]["agent_name"] == "librarian"

    @pytest.mark.asyncio
    @patch("shared.orchestrator.complete_pipeline_run")
    @patch("shared.orchestrator.update_agent_completed")
    @patch("shared.orchestrator.update_agent_started", return_value=0)
    @patch("shared.orchestrator.create_pipeline_run", return_value="run-004")
    async def test_on_text_callback_called(
        self, mock_create, mock_started, mock_completed, mock_complete
    ):
        """テキスト出力時に on_text コールバックが呼ばれる。"""
        agent = MagicMock()
        received_texts = []

        events = [
            _make_event(author="storyteller", text="Once upon a time"),
        ]

        async def mock_run_async(**kwargs):
            for e in events:
                yield e

        mock_runner_instance = MagicMock()
        mock_runner_instance.run_async = mock_run_async

        mock_session = MagicMock()
        mock_session.state = {}

        mock_session_service = AsyncMock()
        mock_session_service.create_session = AsyncMock()
        mock_session_service.get_session = AsyncMock(return_value=mock_session)

        with patch("shared.orchestrator.Runner", return_value=mock_runner_instance), \
             patch("shared.orchestrator.InMemorySessionService", return_value=mock_session_service):
            await run_pipeline(
                agent=agent,
                app_name="test_app",
                user_message="test",
                initial_state={},
                on_text=lambda t: received_texts.append(t),
            )

        assert received_texts == ["Once upon a time"]

    @pytest.mark.asyncio
    @patch("shared.orchestrator.error_pipeline_run")
    @patch("shared.orchestrator.create_pipeline_run", return_value="run-005")
    async def test_error_marks_pipeline_run(self, mock_create, mock_error):
        """例外発生時に pipeline_run をエラーマークする。"""
        agent = MagicMock()

        async def mock_run_async(**kwargs):
            raise RuntimeError("Something went wrong")
            yield

        mock_runner_instance = MagicMock()
        mock_runner_instance.run_async = mock_run_async

        mock_session_service = AsyncMock()
        mock_session_service.create_session = AsyncMock()

        with patch("shared.orchestrator.Runner", return_value=mock_runner_instance), \
             patch("shared.orchestrator.InMemorySessionService", return_value=mock_session_service):
            with pytest.raises(RuntimeError, match="Something went wrong"):
                await run_pipeline(
                    agent=agent,
                    app_name="test_app",
                    user_message="test",
                    initial_state={},
                )

        mock_error.assert_called_once_with("run-005", "Something went wrong")

    @pytest.mark.asyncio
    @patch("shared.orchestrator.complete_pipeline_run")
    @patch("shared.orchestrator.update_agent_completed")
    @patch("shared.orchestrator.update_agent_started", return_value=0)
    @patch("shared.orchestrator.create_pipeline_run", return_value="run-006")
    async def test_mystery_id_extracted_from_session_state(
        self, mock_create, mock_started, mock_completed, mock_complete
    ):
        """blog パイプラインでは session state から mystery_id を抽出する。"""
        agent = MagicMock()

        async def mock_run_async(**kwargs):
            return
            yield

        mock_runner_instance = MagicMock()
        mock_runner_instance.run_async = mock_run_async

        mock_session = MagicMock()
        mock_session.state = {
            "published_episode": '{"mystery_id": "OCC-MA-617-20260208143025", "status": "success"}'
        }

        mock_session_service = AsyncMock()
        mock_session_service.create_session = AsyncMock()
        mock_session_service.get_session = AsyncMock(return_value=mock_session)

        with patch("shared.orchestrator.Runner", return_value=mock_runner_instance), \
             patch("shared.orchestrator.InMemorySessionService", return_value=mock_session_service):
            result = await run_pipeline(
                agent=agent,
                app_name="test_app",
                user_message="test",
                initial_state={},
                run_type="blog",
            )

        assert result.mystery_id == "OCC-MA-617-20260208143025"
        mock_complete.assert_called_once_with("run-006", mystery_id="OCC-MA-617-20260208143025")

    @pytest.mark.asyncio
    @patch("shared.orchestrator.complete_pipeline_run")
    @patch("shared.orchestrator.create_pipeline_run", return_value="run-007")
    async def test_podcast_run_type_no_mystery_id_extraction(
        self, mock_create, mock_complete
    ):
        """podcast パイプラインでは mystery_id 抽出をスキップする。"""
        agent = MagicMock()

        async def mock_run_async(**kwargs):
            return
            yield

        mock_runner_instance = MagicMock()
        mock_runner_instance.run_async = mock_run_async

        mock_session = MagicMock()
        mock_session.state = {}

        mock_session_service = AsyncMock()
        mock_session_service.create_session = AsyncMock()
        mock_session_service.get_session = AsyncMock(return_value=mock_session)

        with patch("shared.orchestrator.Runner", return_value=mock_runner_instance), \
             patch("shared.orchestrator.InMemorySessionService", return_value=mock_session_service):
            result = await run_pipeline(
                agent=agent,
                app_name="test_app",
                user_message="test",
                initial_state={},
                run_type="podcast",
            )

        assert result.mystery_id is None
