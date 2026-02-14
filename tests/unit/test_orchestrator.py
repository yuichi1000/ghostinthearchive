"""Unit tests for shared/orchestrator.py"""

from unittest.mock import MagicMock, patch

import pytest

from shared.orchestrator import PipelineResult, run_pipeline
from tests.fakes import FakeInMemorySessionService


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


def _make_runner(events=None):
    """テスト用の Runner モックを生成する。

    events が None の場合は空の AsyncGenerator を返す。
    """
    async def mock_run_async(**kwargs):
        if events:
            for e in events:
                yield e
        return
        yield  # AsyncGenerator にするために必要

    runner = MagicMock()
    runner.run_async = mock_run_async
    return runner


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
        fake_session = FakeInMemorySessionService()

        with patch("shared.orchestrator.Runner", return_value=_make_runner()), \
             patch("shared.orchestrator.InMemorySessionService", return_value=fake_session):
            result = await run_pipeline(
                agent=MagicMock(),
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
        fake_session = FakeInMemorySessionService()

        with patch("shared.orchestrator.Runner", return_value=_make_runner()), \
             patch("shared.orchestrator.InMemorySessionService", return_value=fake_session):
            result = await run_pipeline(
                agent=MagicMock(),
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
        events = [
            _make_event(author="librarian", text="Found documents"),
            _make_event(author="scholar", text="Analysis complete"),
        ]
        fake_session = FakeInMemorySessionService()

        with patch("shared.orchestrator.Runner", return_value=_make_runner(events)), \
             patch("shared.orchestrator.InMemorySessionService", return_value=fake_session):
            result = await run_pipeline(
                agent=MagicMock(),
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
        events = [
            _make_event(author="ghost_commander", text="Starting"),
            _make_event(author="librarian", text="Found documents"),
        ]
        fake_session = FakeInMemorySessionService()

        with patch("shared.orchestrator.Runner", return_value=_make_runner(events)), \
             patch("shared.orchestrator.InMemorySessionService", return_value=fake_session):
            result = await run_pipeline(
                agent=MagicMock(),
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
        received_texts = []
        events = [
            _make_event(author="storyteller", text="Once upon a time"),
        ]
        fake_session = FakeInMemorySessionService()

        with patch("shared.orchestrator.Runner", return_value=_make_runner(events)), \
             patch("shared.orchestrator.InMemorySessionService", return_value=fake_session):
            await run_pipeline(
                agent=MagicMock(),
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
        async def error_run_async(**kwargs):
            raise RuntimeError("Something went wrong")
            yield

        runner = MagicMock()
        runner.run_async = error_run_async
        fake_session = FakeInMemorySessionService()

        with patch("shared.orchestrator.Runner", return_value=runner), \
             patch("shared.orchestrator.InMemorySessionService", return_value=fake_session):
            with pytest.raises(RuntimeError, match="Something went wrong"):
                await run_pipeline(
                    agent=MagicMock(),
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
        # Runner 実行後のセッション状態をシミュレート
        fake_session = FakeInMemorySessionService(
            post_run_state={
                "published_episode": '{"mystery_id": "OCC-MA-617-20260208143025", "status": "success"}'
            }
        )

        with patch("shared.orchestrator.Runner", return_value=_make_runner()), \
             patch("shared.orchestrator.InMemorySessionService", return_value=fake_session):
            result = await run_pipeline(
                agent=MagicMock(),
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
        fake_session = FakeInMemorySessionService()

        with patch("shared.orchestrator.Runner", return_value=_make_runner()), \
             patch("shared.orchestrator.InMemorySessionService", return_value=fake_session):
            result = await run_pipeline(
                agent=MagicMock(),
                app_name="test_app",
                user_message="test",
                initial_state={},
                run_type="podcast",
            )

        assert result.mystery_id is None


class TestParallelAgentTracking:
    """並列エージェントのインターリーブイベント追跡テスト"""

    @pytest.mark.asyncio
    @patch("shared.orchestrator.complete_pipeline_run")
    @patch("shared.orchestrator.update_agent_completed")
    @patch("shared.orchestrator.update_agent_started", return_value=0)
    @patch("shared.orchestrator.create_pipeline_run", return_value="run-100")
    async def test_interleaved_parallel_events_single_entry(
        self, mock_create, mock_started, mock_completed, mock_complete
    ):
        """並列エージェントの交互イベントが1エントリずつに集約される。"""
        events = [
            # ParallelAgent 内でインターリーブ
            _make_event(author="librarian_en", text="Searching LOC..."),
            _make_event(author="librarian_es", text="Buscando en DPLA..."),
            _make_event(author="librarian_en", text="Found 5 documents"),
            _make_event(author="librarian_es", text="Encontré 3 documentos"),
        ]
        fake_session = FakeInMemorySessionService()

        with patch("shared.orchestrator.Runner", return_value=_make_runner(events)), \
             patch("shared.orchestrator.InMemorySessionService", return_value=fake_session):
            result = await run_pipeline(
                agent=MagicMock(),
                app_name="test_app",
                user_message="test",
                initial_state={},
            )

        # 各エージェントが1エントリのみ（2重エントリなし）
        assert mock_started.call_count == 2
        assert len(result.logs) == 2
        assert result.logs[0]["agent_name"] == "librarian_en"
        assert result.logs[1]["agent_name"] == "librarian_es"

        # テキストが蓄積されている
        assert "Searching LOC..." in result.logs[0]["output_summary"]
        assert "Buscando en DPLA..." in result.logs[1]["output_summary"]

    @pytest.mark.asyncio
    @patch("shared.orchestrator.complete_pipeline_run")
    @patch("shared.orchestrator.update_agent_completed")
    @patch("shared.orchestrator.update_agent_started", return_value=0)
    @patch("shared.orchestrator.create_pipeline_run", return_value="run-101")
    async def test_skip_author_triggers_stage_boundary(
        self, mock_create, mock_started, mock_completed, mock_complete
    ):
        """skip_authors イベントがステージ境界として機能し、前ステージを一括完了する。"""
        events = [
            _make_event(author="librarian_en", text="Found docs"),
            _make_event(author="librarian_es", text="Encontré docs"),
            # ステージ境界: scholar_block（skip_authors）
            _make_event(author="scholar_block"),
            _make_event(author="scholar_en", text="Analysis done"),
        ]
        fake_session = FakeInMemorySessionService()

        with patch("shared.orchestrator.Runner", return_value=_make_runner(events)), \
             patch("shared.orchestrator.InMemorySessionService", return_value=fake_session):
            result = await run_pipeline(
                agent=MagicMock(),
                app_name="test_app",
                user_message="test",
                initial_state={},
                skip_authors={"scholar_block"},
            )

        # librarian_en, librarian_es, scholar_en の3エントリ
        assert len(result.logs) == 3
        # scholar_block のイベントで librarian 2つが完了済み
        assert result.logs[0]["status"] == "completed"
        assert result.logs[1]["status"] == "completed"
        assert result.logs[2]["status"] == "completed"

    @pytest.mark.asyncio
    @patch("shared.orchestrator.complete_pipeline_run")
    @patch("shared.orchestrator.update_agent_completed")
    @patch("shared.orchestrator.update_agent_started", return_value=0)
    @patch("shared.orchestrator.create_pipeline_run", return_value="run-102")
    async def test_skipped_agent_empty_text_short_duration_removed(
        self, mock_create, mock_started, mock_completed, mock_complete
    ):
        """空テキスト + 短時間のスキップエージェントがログから除去される。"""
        # language_gate でスキップされたエージェント: テキストなし
        events = [
            _make_event(author="librarian_en", text="Found documents"),
            _make_event(author="librarian_de"),  # テキストなし = スキップ
        ]
        fake_session = FakeInMemorySessionService()

        with patch("shared.orchestrator.Runner", return_value=_make_runner(events)), \
             patch("shared.orchestrator.InMemorySessionService", return_value=fake_session):
            result = await run_pipeline(
                agent=MagicMock(),
                app_name="test_app",
                user_message="test",
                initial_state={},
            )

        # librarian_de はスキップ判定（テストでは duration ≈ 0 なので除去される）
        # librarian_en のみ残る
        agent_names = [log["agent_name"] for log in result.logs]
        assert "librarian_en" in agent_names
        # librarian_de は空テキスト + 短時間で除去される
        assert "librarian_de" not in agent_names


class TestSequentialAgentCompletion:
    """sequential_agents による直列完了テスト"""

    @pytest.mark.asyncio
    @patch("shared.orchestrator.complete_pipeline_run")
    @patch("shared.orchestrator.update_agent_completed")
    @patch("shared.orchestrator.update_agent_started", return_value=0)
    @patch("shared.orchestrator.create_pipeline_run", return_value="run-200")
    async def test_sequential_agent_auto_completes_predecessor(
        self, mock_create, mock_started, mock_completed, mock_complete
    ):
        """sequential_agents 内で新エージェント開始時に前のエージェントが自動完了される。"""
        events = [
            _make_event(author="script_planner", text="Outline done"),
            _make_event(author="scriptwriter", text="Writing segment 1"),
            _make_event(author="scriptwriter", text="Writing segment 2"),
            _make_event(author="podcast_translator_ja", text="翻訳中"),
        ]
        fake_session = FakeInMemorySessionService()

        with patch("shared.orchestrator.Runner", return_value=_make_runner(events)), \
             patch("shared.orchestrator.InMemorySessionService", return_value=fake_session):
            result = await run_pipeline(
                agent=MagicMock(),
                app_name="test_app",
                user_message="test",
                initial_state={},
                skip_authors={"podcast_script_commander"},
                sequential_agents={"script_planner", "scriptwriter", "podcast_translator_ja"},
            )

        # 3エージェントすべてが記録される
        assert len(result.logs) == 3
        assert result.logs[0]["agent_name"] == "script_planner"
        assert result.logs[1]["agent_name"] == "scriptwriter"
        assert result.logs[2]["agent_name"] == "podcast_translator_ja"

        # すべて completed
        assert all(log["status"] == "completed" for log in result.logs)

    @pytest.mark.asyncio
    @patch("shared.orchestrator.complete_pipeline_run")
    @patch("shared.orchestrator.update_agent_completed")
    @patch("shared.orchestrator.update_agent_started", return_value=0)
    @patch("shared.orchestrator.create_pipeline_run", return_value="run-201")
    async def test_sequential_agents_does_not_affect_non_members(
        self, mock_create, mock_started, mock_completed, mock_complete
    ):
        """sequential_agents に含まれないエージェントは直列完了の対象外。"""
        events = [
            _make_event(author="script_planner", text="Outline done"),
            _make_event(author="other_agent", text="I'm not sequential"),
            _make_event(author="scriptwriter", text="Writing"),
        ]
        fake_session = FakeInMemorySessionService()

        with patch("shared.orchestrator.Runner", return_value=_make_runner(events)), \
             patch("shared.orchestrator.InMemorySessionService", return_value=fake_session):
            result = await run_pipeline(
                agent=MagicMock(),
                app_name="test_app",
                user_message="test",
                initial_state={},
                sequential_agents={"script_planner", "scriptwriter"},
            )

        # script_planner は scriptwriter 開始時に自動完了
        # other_agent は sequential_agents 外なので影響を受けない
        agent_names = [log["agent_name"] for log in result.logs]
        assert "script_planner" in agent_names
        assert "other_agent" in agent_names
        assert "scriptwriter" in agent_names
        assert len(result.logs) == 3

    @pytest.mark.asyncio
    @patch("shared.orchestrator.complete_pipeline_run")
    @patch("shared.orchestrator.update_agent_completed")
    @patch("shared.orchestrator.update_agent_started", return_value=0)
    @patch("shared.orchestrator.create_pipeline_run", return_value="run-202")
    async def test_no_sequential_agents_same_behavior(
        self, mock_create, mock_started, mock_completed, mock_complete
    ):
        """sequential_agents 未指定時は従来と同じ挙動。"""
        events = [
            _make_event(author="script_planner", text="Outline done"),
            _make_event(author="scriptwriter", text="Writing"),
        ]
        fake_session = FakeInMemorySessionService()

        with patch("shared.orchestrator.Runner", return_value=_make_runner(events)), \
             patch("shared.orchestrator.InMemorySessionService", return_value=fake_session):
            result = await run_pipeline(
                agent=MagicMock(),
                app_name="test_app",
                user_message="test",
                initial_state={},
            )

        assert len(result.logs) == 2
        assert result.logs[0]["agent_name"] == "script_planner"
        assert result.logs[1]["agent_name"] == "scriptwriter"
