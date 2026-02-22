"""shared/orchestrator のレートリミットリトライのユニットテスト。

_is_rate_limit_error() の判定ロジックと、
run_pipeline() が 429 エラー時にリトライすることを検証する。
"""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from shared.orchestrator import (
    _RATE_LIMIT_MAX_RETRIES,
    _RATE_LIMIT_RETRY_DELAY,
    _is_rate_limit_error,
    run_pipeline,
)


class TestIsRateLimitError:
    """_is_rate_limit_error() のテスト。"""

    def test_with_429_in_message(self):
        """エラーメッセージに '429' が含まれる場合に True を返すこと。"""
        exc = Exception("Error code: 429 Too Many Requests")
        assert _is_rate_limit_error(exc) is True

    def test_with_resource_exhausted(self):
        """エラーメッセージに 'RESOURCE_EXHAUSTED' が含まれる場合に True を返すこと。"""
        exc = Exception("RESOURCE_EXHAUSTED: Quota exceeded")
        assert _is_rate_limit_error(exc) is True

    def test_with_other_error(self):
        """429 でも RESOURCE_EXHAUSTED でもないエラーは False を返すこと。"""
        exc = Exception("Internal server error 500")
        assert _is_rate_limit_error(exc) is False

    def test_with_exception_group_containing_429(self):
        """ExceptionGroup 内に 429 エラーがある場合に True を返すこと。"""
        inner = Exception("429 rate limited")
        group = ExceptionGroup("pipeline errors", [inner])
        assert _is_rate_limit_error(group) is True

    def test_with_exception_group_no_rate_limit(self):
        """ExceptionGroup 内にレートリミットエラーがない場合に False を返すこと。"""
        inner = Exception("Some other error")
        group = ExceptionGroup("pipeline errors", [inner])
        assert _is_rate_limit_error(group) is False

    def test_with_nested_exception_group(self):
        """ネストした ExceptionGroup 内の 429 エラーも検出すること。"""
        inner = Exception("RESOURCE_EXHAUSTED")
        inner_group = ExceptionGroup("inner", [inner])
        outer_group = ExceptionGroup("outer", [inner_group])
        assert _is_rate_limit_error(outer_group) is True


class TestRateLimitConstants:
    """レートリミットリトライ定数のテスト。"""

    def test_retry_delay_is_180_seconds(self):
        """リトライ間隔が 180秒（3分）であること。"""
        assert _RATE_LIMIT_RETRY_DELAY == 180

    def test_max_retries_is_2(self):
        """最大リトライ回数が 2回であること（計3回試行）。"""
        assert _RATE_LIMIT_MAX_RETRIES == 2


class TestRunPipelineRetry:
    """run_pipeline() のレートリミットリトライのテスト。"""

    @pytest.mark.asyncio
    async def test_retries_on_rate_limit(self):
        """429 エラー時にリトライされ、2回目で成功すること。"""
        mock_agent = MagicMock()

        # Runner.run_async のモック:
        # 1回目: 429 例外を送出
        # 2回目: 正常終了（空のイベントストリーム）
        call_count = 0

        async def mock_run_async(**kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise Exception("429 Too Many Requests")
            # 2回目: 空のイベントストリーム（正常終了）
            return
            yield  # async generator にする

        mock_runner_cls = MagicMock()
        mock_runner_instance = MagicMock()
        mock_runner_instance.run_async = mock_run_async
        mock_runner_cls.return_value = mock_runner_instance

        mock_session_service_cls = MagicMock()
        mock_session_service = AsyncMock()
        mock_session = MagicMock()
        mock_session.state = {"pipeline_log": []}
        mock_session_service.create_session = AsyncMock()
        mock_session_service.get_session = AsyncMock(return_value=mock_session)
        mock_session_service_cls.return_value = mock_session_service

        with (
            patch("shared.orchestrator.Runner", mock_runner_cls),
            patch("shared.orchestrator.InMemorySessionService", mock_session_service_cls),
            patch("shared.orchestrator.create_pipeline_run", return_value="test-run-id"),
            patch("shared.orchestrator.set_pipeline_context"),
            patch("shared.orchestrator.update_agent_started"),
            patch("shared.orchestrator.update_agent_completed"),
            patch("shared.orchestrator.complete_pipeline_run"),
            patch("shared.orchestrator.error_pipeline_run"),
            patch("shared.orchestrator._RATE_LIMIT_RETRY_DELAY", 0),  # テストではスリープしない
        ):
            result = await run_pipeline(
                agent=mock_agent,
                app_name="test_app",
                user_message="test query",
                initial_state={},
                run_type="podcast",  # blog だとゲート失敗判定が必要
            )

        assert result.run_id == "test-run-id"
        assert call_count == 2  # 1回目失敗 + 2回目成功

    @pytest.mark.asyncio
    async def test_raises_after_max_retries(self):
        """最大リトライ回数を超えた場合に例外が送出されること。"""
        mock_agent = MagicMock()

        async def mock_run_async(**kwargs):
            raise Exception("429 Too Many Requests")
            yield  # async generator にする

        mock_runner_cls = MagicMock()
        mock_runner_instance = MagicMock()
        mock_runner_instance.run_async = mock_run_async
        mock_runner_cls.return_value = mock_runner_instance

        mock_session_service_cls = MagicMock()
        mock_session_service = AsyncMock()
        mock_session_service.create_session = AsyncMock()
        mock_session_service_cls.return_value = mock_session_service

        with (
            patch("shared.orchestrator.Runner", mock_runner_cls),
            patch("shared.orchestrator.InMemorySessionService", mock_session_service_cls),
            patch("shared.orchestrator.create_pipeline_run", return_value="test-run-id"),
            patch("shared.orchestrator.set_pipeline_context"),
            patch("shared.orchestrator.update_agent_started"),
            patch("shared.orchestrator.update_agent_completed"),
            patch("shared.orchestrator.complete_pipeline_run"),
            patch("shared.orchestrator.error_pipeline_run") as mock_error,
            patch("shared.orchestrator._RATE_LIMIT_RETRY_DELAY", 0),
        ):
            with pytest.raises(Exception, match="429"):
                await run_pipeline(
                    agent=mock_agent,
                    app_name="test_app",
                    user_message="test query",
                    initial_state={},
                    run_type="podcast",
                )

    @pytest.mark.asyncio
    async def test_non_rate_limit_error_not_retried(self):
        """429 以外のエラーはリトライせずに即座に送出されること。"""
        mock_agent = MagicMock()
        call_count = 0

        async def mock_run_async(**kwargs):
            nonlocal call_count
            call_count += 1
            raise Exception("Internal server error 500")
            yield

        mock_runner_cls = MagicMock()
        mock_runner_instance = MagicMock()
        mock_runner_instance.run_async = mock_run_async
        mock_runner_cls.return_value = mock_runner_instance

        mock_session_service_cls = MagicMock()
        mock_session_service = AsyncMock()
        mock_session_service.create_session = AsyncMock()
        mock_session_service_cls.return_value = mock_session_service

        with (
            patch("shared.orchestrator.Runner", mock_runner_cls),
            patch("shared.orchestrator.InMemorySessionService", mock_session_service_cls),
            patch("shared.orchestrator.create_pipeline_run", return_value="test-run-id"),
            patch("shared.orchestrator.set_pipeline_context"),
            patch("shared.orchestrator.update_agent_started"),
            patch("shared.orchestrator.update_agent_completed"),
            patch("shared.orchestrator.complete_pipeline_run"),
            patch("shared.orchestrator.error_pipeline_run"),
            patch("shared.orchestrator._RATE_LIMIT_RETRY_DELAY", 0),
        ):
            with pytest.raises(Exception, match="500"):
                await run_pipeline(
                    agent=mock_agent,
                    app_name="test_app",
                    user_message="test query",
                    initial_state={},
                    run_type="podcast",
                )

        assert call_count == 1  # リトライなし
