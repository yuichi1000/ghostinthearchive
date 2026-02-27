"""Unit tests for shared/orchestrator.py"""

import asyncio
import json
from unittest.mock import MagicMock, patch

import pytest

from shared.orchestrator import (
    PipelineResult,
    _build_state_summary,
    _detect_gate_failure,
    _extract_mystery_id,
    _format_exception_group,
    run_pipeline,
)
from shared.state_keys import PUBLISHED_EPISODE, PUBLISHED_MYSTERY_ID
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
    @patch("shared.orchestrator.error_pipeline_run")
    @patch("shared.orchestrator.update_agent_completed")
    @patch("shared.orchestrator.update_agent_started", return_value=0)
    @patch("shared.orchestrator.create_pipeline_run", return_value="run-001")
    async def test_creates_pipeline_run_when_not_provided(
        self, mock_create, mock_started, mock_completed, mock_error
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
    @patch("shared.orchestrator.error_pipeline_run")
    @patch("shared.orchestrator.update_agent_completed")
    @patch("shared.orchestrator.update_agent_started", return_value=0)
    @patch("shared.orchestrator.create_pipeline_run")
    async def test_skips_create_when_run_id_provided(
        self, mock_create, mock_started, mock_completed, mock_error
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
    @patch("shared.orchestrator.error_pipeline_run")
    @patch("shared.orchestrator.update_agent_completed")
    @patch("shared.orchestrator.update_agent_started", return_value=0)
    @patch("shared.orchestrator.create_pipeline_run", return_value="run-002")
    async def test_agent_transitions_tracked(
        self, mock_create, mock_started, mock_completed, mock_error
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
    @patch("shared.orchestrator.error_pipeline_run")
    @patch("shared.orchestrator.update_agent_completed")
    @patch("shared.orchestrator.update_agent_started", return_value=0)
    @patch("shared.orchestrator.create_pipeline_run", return_value="run-003")
    async def test_skip_authors_are_ignored(
        self, mock_create, mock_started, mock_completed, mock_error
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
    @patch("shared.orchestrator.error_pipeline_run")
    @patch("shared.orchestrator.update_agent_completed")
    @patch("shared.orchestrator.update_agent_started", return_value=0)
    @patch("shared.orchestrator.create_pipeline_run", return_value="run-004")
    async def test_on_text_callback_called(
        self, mock_create, mock_started, mock_completed, mock_error
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

        mock_error.assert_called_once_with(
            "run-005", "Something went wrong",
            error_detail={
                "error_type": "exception",
                "exception_class": "RuntimeError",
                "pipeline_log": [],
            },
        )

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

    @pytest.mark.asyncio
    @patch("shared.orchestrator.complete_pipeline_run")
    @patch("shared.orchestrator.update_agent_completed")
    @patch("shared.orchestrator.update_agent_started", return_value=0)
    @patch("shared.orchestrator.create_pipeline_run", return_value="run-008")
    async def test_mystery_id_from_published_mystery_id_state(
        self, mock_create, mock_started, mock_completed, mock_complete
    ):
        """published_mystery_id が優先的に使用される。"""
        fake_session = FakeInMemorySessionService(
            post_run_state={
                "published_mystery_id": "HIS-NY-212-20260215100000",
                "published_episode": "The mystery has been published successfully!",
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

        assert result.mystery_id == "HIS-NY-212-20260215100000"
        mock_complete.assert_called_once_with("run-008", mystery_id="HIS-NY-212-20260215100000")

    @pytest.mark.asyncio
    @patch("shared.orchestrator.complete_pipeline_run")
    @patch("shared.orchestrator.update_agent_completed")
    @patch("shared.orchestrator.update_agent_started", return_value=0)
    @patch("shared.orchestrator.create_pipeline_run", return_value="run-009")
    async def test_fallback_to_published_episode_with_leading_whitespace(
        self, mock_create, mock_started, mock_completed, mock_complete
    ):
        """published_mystery_id がない場合、published_episode を strip してフォールバック。"""
        fake_session = FakeInMemorySessionService(
            post_run_state={
                "published_episode": '\n{"mystery_id": "FLK-MA-978-20260215120000", "status": "success"}'
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

        assert result.mystery_id == "FLK-MA-978-20260215120000"


class TestParallelAgentTracking:
    """並列エージェントのインターリーブイベント追跡テスト"""

    @pytest.mark.asyncio
    @patch("shared.orchestrator.error_pipeline_run")
    @patch("shared.orchestrator.update_agent_completed")
    @patch("shared.orchestrator.update_agent_started", return_value=0)
    @patch("shared.orchestrator.create_pipeline_run", return_value="run-100")
    async def test_interleaved_parallel_events_single_entry(
        self, mock_create, mock_started, mock_completed, mock_error
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
    @patch("shared.orchestrator.error_pipeline_run")
    @patch("shared.orchestrator.update_agent_completed")
    @patch("shared.orchestrator.update_agent_started", return_value=0)
    @patch("shared.orchestrator.create_pipeline_run", return_value="run-101")
    async def test_skip_author_triggers_stage_boundary(
        self, mock_create, mock_started, mock_completed, mock_error
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
    @patch("shared.orchestrator.error_pipeline_run")
    @patch("shared.orchestrator.update_agent_completed")
    @patch("shared.orchestrator.update_agent_started", return_value=0)
    @patch("shared.orchestrator.create_pipeline_run", return_value="run-102")
    async def test_skipped_agent_empty_text_short_duration_removed(
        self, mock_create, mock_started, mock_completed, mock_error
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
    @patch("shared.orchestrator.error_pipeline_run")
    @patch("shared.orchestrator.update_agent_completed")
    @patch("shared.orchestrator.update_agent_started", return_value=0)
    @patch("shared.orchestrator.create_pipeline_run", return_value="run-200")
    async def test_sequential_agent_auto_completes_predecessor(
        self, mock_create, mock_started, mock_completed, mock_error
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
    @patch("shared.orchestrator.error_pipeline_run")
    @patch("shared.orchestrator.update_agent_completed")
    @patch("shared.orchestrator.update_agent_started", return_value=0)
    @patch("shared.orchestrator.create_pipeline_run", return_value="run-201")
    async def test_sequential_agents_does_not_affect_non_members(
        self, mock_create, mock_started, mock_completed, mock_error
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
    @patch("shared.orchestrator.error_pipeline_run")
    @patch("shared.orchestrator.update_agent_completed")
    @patch("shared.orchestrator.update_agent_started", return_value=0)
    @patch("shared.orchestrator.create_pipeline_run", return_value="run-202")
    async def test_no_sequential_agents_same_behavior(
        self, mock_create, mock_started, mock_completed, mock_error
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


class TestDetectGateFailure:
    """_detect_gate_failure() の単体テスト"""

    def test_empty_state_returns_insufficient_data_message(self):
        """空セッション → 資料不足メッセージを返す。"""
        message, detail = _detect_gate_failure({})
        assert "資料が見つからなかった" in message
        assert detail["error_type"] == "gate_failure"
        assert detail["failed_stage"] == "scholar/polymath"

    def test_insufficient_mystery_report_returns_message(self):
        """mystery_report が INSUFFICIENT_DATA → 資料不足メッセージ。"""
        state = {"mystery_report": "INSUFFICIENT_DATA: No data available"}
        message, detail = _detect_gate_failure(state)
        assert "資料が見つからなかった" in message
        assert detail["error_type"] == "gate_failure"

    def test_no_creative_content_returns_message(self):
        """mystery_report あり + creative_content が NO_CONTENT → 記事生成失敗メッセージ。"""
        state = {
            "mystery_report": "A valid report about historical mysteries...",
            "creative_content": "NO_CONTENT: Story generation failed",
        }
        message, detail = _detect_gate_failure(state)
        assert "記事の生成に失敗" in message
        assert detail["failed_stage"] == "storyteller"

    def test_both_present_returns_publish_error(self):
        """全フィールド有意 + mystery_id なし → 公開処理失敗メッセージ。"""
        state = {
            "mystery_report": "A valid detailed analysis...",
            "creative_content": "A compelling blog post about...",
        }
        message, detail = _detect_gate_failure(state)
        assert "公開処理で問題" in message
        assert detail["error_type"] == "publish_failed"
        assert detail["failed_stage"] == "publisher"

    def test_empty_creative_content_returns_message(self):
        """mystery_report あり + creative_content が空文字 → 記事生成失敗メッセージ。"""
        state = {
            "mystery_report": "A valid analysis result...",
            "creative_content": "",
        }
        message, detail = _detect_gate_failure(state)
        assert "記事の生成に失敗" in message

    def test_includes_state_summary(self):
        """error_detail に session_state_summary が含まれる。"""
        state = {
            "mystery_report": "A valid detailed analysis...",
            "creative_content": "A compelling blog post about...",
            "structured_report": {"title": "test"},
        }
        _, detail = _detect_gate_failure(state)
        summary = detail["session_state_summary"]
        assert "present" in summary["mystery_report"]
        assert "present" in summary["creative_content"]
        assert "present (dict, 1 keys)" == summary["structured_report"]
        assert summary["image_metadata"] == "missing"
        assert summary["published_mystery_id"] == "missing"


    def test_includes_storyteller_llm_metadata_when_present(self):
        """storyteller_llm_metadata があれば error_detail に含まれる。"""
        llm_meta = {
            "finish_reason": "SAFETY",
            "error_code": "SAFETY_FILTER",
            "error_message": "Content blocked",
            "has_content": False,
            "prompt_tokens": 5000,
            "output_tokens": 0,
        }
        state = {
            "mystery_report": "A valid analysis...",
            "creative_content": "",
            "storyteller_llm_metadata": llm_meta,
        }
        _, detail = _detect_gate_failure(state)
        assert detail["storyteller_llm_metadata"] == llm_meta
        assert detail["failed_stage"] == "storyteller"

    def test_no_storyteller_llm_metadata_when_absent(self):
        """storyteller_llm_metadata がない場合は error_detail に含まれない。"""
        state = {
            "mystery_report": "A valid analysis...",
            "creative_content": "",
        }
        _, detail = _detect_gate_failure(state)
        assert "storyteller_llm_metadata" not in detail


class TestGateFailureIntegration:
    """blog パイプラインのゲート失敗 → error_pipeline_run の統合テスト"""

    @pytest.mark.asyncio
    @patch("shared.orchestrator.error_pipeline_run")
    @patch("shared.orchestrator.complete_pipeline_run")
    @patch("shared.orchestrator.create_pipeline_run", return_value="run-300")
    async def test_blog_gate_failure_marks_error(
        self, mock_create, mock_complete, mock_error
    ):
        """mystery_report が INSUFFICIENT_DATA → error_pipeline_run が呼ばれる。"""
        fake_session = FakeInMemorySessionService(
            post_run_state={
                "mystery_report": "INSUFFICIENT_DATA: All scholars failed",
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

        assert result.mystery_id is None
        mock_error.assert_called_once()
        assert "資料が見つからなかった" in mock_error.call_args[0][1]
        # error_detail が渡される
        error_detail = mock_error.call_args[1]["error_detail"]
        assert error_detail["error_type"] == "gate_failure"
        assert "session_state_summary" in error_detail
        mock_complete.assert_not_called()

    @pytest.mark.asyncio
    @patch("shared.orchestrator.error_pipeline_run")
    @patch("shared.orchestrator.complete_pipeline_run")
    @patch("shared.orchestrator.create_pipeline_run", return_value="run-301")
    async def test_blog_gate_failure_no_creative_content(
        self, mock_create, mock_complete, mock_error
    ):
        """creative_content が NO_CONTENT → error_pipeline_run が呼ばれる。"""
        fake_session = FakeInMemorySessionService(
            post_run_state={
                "mystery_report": "Valid analysis content here...",
                "creative_content": "NO_CONTENT: generation failed",
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

        assert result.mystery_id is None
        mock_error.assert_called_once()
        assert "記事の生成に失敗" in mock_error.call_args[0][1]
        # error_detail が渡される
        error_detail = mock_error.call_args[1]["error_detail"]
        assert error_detail["failed_stage"] == "storyteller"
        mock_complete.assert_not_called()

    @pytest.mark.asyncio
    @patch("shared.orchestrator.error_pipeline_run")
    @patch("shared.orchestrator.complete_pipeline_run")
    @patch("shared.orchestrator.update_agent_completed")
    @patch("shared.orchestrator.update_agent_started", return_value=0)
    @patch("shared.orchestrator.create_pipeline_run", return_value="run-302")
    async def test_blog_success_not_affected(
        self, mock_create, mock_started, mock_completed, mock_complete, mock_error
    ):
        """mystery_id あり → 従来通り complete_pipeline_run が呼ばれる。"""
        fake_session = FakeInMemorySessionService(
            post_run_state={
                "published_episode": '{"mystery_id": "HIS-NY-212-20260210120000"}',
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

        assert result.mystery_id == "HIS-NY-212-20260210120000"
        mock_complete.assert_called_once_with("run-302", mystery_id="HIS-NY-212-20260210120000")
        mock_error.assert_not_called()

    @pytest.mark.asyncio
    @patch("shared.orchestrator.error_pipeline_run")
    @patch("shared.orchestrator.complete_pipeline_run")
    @patch("shared.orchestrator.create_pipeline_run", return_value="run-303")
    async def test_podcast_not_affected(
        self, mock_create, mock_complete, mock_error
    ):
        """podcast パイプラインは mystery_id なしでも complete_pipeline_run。"""
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
        mock_complete.assert_called_once_with("run-303", mystery_id=None)
        mock_error.assert_not_called()


class TestFormatExceptionGroup:
    """_format_exception_group() の単体テスト"""

    def test_plain_exception_returns_str(self):
        """通常例外は str(exc) を返す。"""
        exc = RuntimeError("something broke")
        assert _format_exception_group(exc) == "something broke"

    def test_single_sub_exception(self):
        """サブ例外1個の ExceptionGroup を展開する。"""
        inner = ValueError("bad value")
        group = ExceptionGroup("group", [inner])
        result = _format_exception_group(group)
        assert "ValueError: bad value" in result

    def test_multiple_sub_exceptions(self):
        """サブ例外複数の ExceptionGroup を展開する。"""
        group = ExceptionGroup("group", [
            RuntimeError("err1"),
            TypeError("err2"),
        ])
        result = _format_exception_group(group)
        assert "RuntimeError: err1" in result
        assert "TypeError: err2" in result
        assert " | " in result

    def test_nested_exception_group(self):
        """ネストした ExceptionGroup を再帰的に展開する。"""
        inner_group = ExceptionGroup("inner", [KeyError("missing")])
        outer_group = ExceptionGroup("outer", [
            inner_group,
            IOError("disk full"),
        ])
        result = _format_exception_group(outer_group)
        assert "KeyError" in result
        assert "IOError" in result or "OSError" in result


class TestExceptionGroupInPipeline:
    """run_pipeline で ExceptionGroup 発生時のサブ例外展開テスト"""

    @pytest.mark.asyncio
    @patch("shared.orchestrator.error_pipeline_run")
    @patch("shared.orchestrator.create_pipeline_run", return_value="run-400")
    async def test_exception_group_unwrapped_in_error_message(
        self, mock_create, mock_error
    ):
        """ExceptionGroup 発生時に error_pipeline_run にサブ例外詳細が渡される。"""
        async def error_run_async(**kwargs):
            raise ExceptionGroup("TaskGroup errors", [
                RuntimeError("tool X failed"),
                ValueError("invalid input"),
            ])
            yield

        runner = MagicMock()
        runner.run_async = error_run_async
        fake_session = FakeInMemorySessionService()

        with patch("shared.orchestrator.Runner", return_value=runner), \
             patch("shared.orchestrator.InMemorySessionService", return_value=fake_session):
            with pytest.raises(ExceptionGroup):
                await run_pipeline(
                    agent=MagicMock(),
                    app_name="test_app",
                    user_message="test",
                    initial_state={},
                )

        # サブ例外の詳細が error_pipeline_run に渡される
        error_msg = mock_error.call_args[0][1]
        assert "RuntimeError: tool X failed" in error_msg
        assert "ValueError: invalid input" in error_msg
        # error_detail に exception_class が含まれる
        error_detail = mock_error.call_args[1]["error_detail"]
        assert error_detail["error_type"] == "exception"
        assert error_detail["exception_class"] == "ExceptionGroup"


class TestErrorRemainingAgents:
    """エラー発生時に running エージェントがエラーマークされるテスト"""

    @pytest.mark.asyncio
    @patch("shared.orchestrator.error_pipeline_run")
    @patch("shared.orchestrator.update_agent_started", return_value=0)
    @patch("shared.orchestrator.create_pipeline_run", return_value="run-500")
    async def test_running_agents_marked_error_on_exception(
        self, mock_create, mock_started, mock_error
    ):
        """例外発生時に running 中のエージェントが status: "error" になること。"""
        async def error_after_events(**kwargs):
            yield _make_event(author="librarian", text="Searching...")
            yield _make_event(author="scholar", text="Analyzing...")
            raise RuntimeError("OpenRouter API failed")
            yield

        runner = MagicMock()
        runner.run_async = error_after_events
        fake_session = FakeInMemorySessionService()

        with patch("shared.orchestrator.Runner", return_value=runner), \
             patch("shared.orchestrator.InMemorySessionService", return_value=fake_session):
            with pytest.raises(RuntimeError, match="OpenRouter API failed"):
                await run_pipeline(
                    agent=MagicMock(),
                    app_name="test_app",
                    user_message="test",
                    initial_state={},
                )

        # error_pipeline_run の error_detail に pipeline_log が含まれる
        mock_error.assert_called_once()
        error_detail = mock_error.call_args[1]["error_detail"]
        pipeline_log = error_detail["pipeline_log"]

        # librarian と scholar が error ステータスになっている
        error_agents = [log for log in pipeline_log if log["status"] == "error"]
        error_names = {log["agent_name"] for log in error_agents}
        assert {"librarian", "scholar"} == error_names

    @pytest.mark.asyncio
    @patch("shared.orchestrator.error_pipeline_run")
    @patch("shared.orchestrator.update_agent_started", return_value=0)
    @patch("shared.orchestrator.create_pipeline_run", return_value="run-501")
    async def test_running_agents_marked_error_on_timeout(
        self, mock_create, mock_started, mock_error
    ):
        """タイムアウト時に running 中のエージェントが status: "error" になること。"""
        async def slow_events(**kwargs):
            yield _make_event(author="storyteller", text="Writing...")
            await asyncio.sleep(10)
            yield

        runner = MagicMock()
        runner.run_async = slow_events
        fake_session = FakeInMemorySessionService()

        with patch("shared.orchestrator.Runner", return_value=runner), \
             patch("shared.orchestrator.InMemorySessionService", return_value=fake_session):
            with pytest.raises(TimeoutError):
                await run_pipeline(
                    agent=MagicMock(),
                    app_name="test_app",
                    user_message="test",
                    initial_state={},
                    timeout_seconds=0.01,
                )

        # error_pipeline_run の error_detail に pipeline_log が含まれる
        mock_error.assert_called_once()
        error_detail = mock_error.call_args[1]["error_detail"]
        pipeline_log = error_detail["pipeline_log"]

        # storyteller が error ステータスになっている
        error_agents = [log for log in pipeline_log if log["status"] == "error"]
        assert len(error_agents) == 1
        assert error_agents[0]["agent_name"] == "storyteller"

    @pytest.mark.asyncio
    @patch("shared.orchestrator.error_pipeline_run")
    @patch("shared.orchestrator.update_agent_started", return_value=0)
    @patch("shared.orchestrator.create_pipeline_run", return_value="run-502")
    async def test_error_detail_includes_pipeline_log(
        self, mock_create, mock_started, mock_error
    ):
        """error_detail に pipeline_log キーが含まれること。"""
        async def error_run_async(**kwargs):
            yield _make_event(author="librarian", text="Found docs")
            raise RuntimeError("Unexpected error")
            yield

        runner = MagicMock()
        runner.run_async = error_run_async
        fake_session = FakeInMemorySessionService()

        with patch("shared.orchestrator.Runner", return_value=runner), \
             patch("shared.orchestrator.InMemorySessionService", return_value=fake_session):
            with pytest.raises(RuntimeError):
                await run_pipeline(
                    agent=MagicMock(),
                    app_name="test_app",
                    user_message="test",
                    initial_state={},
                )

        error_detail = mock_error.call_args[1]["error_detail"]
        assert "pipeline_log" in error_detail
        assert isinstance(error_detail["pipeline_log"], list)


class TestExtractMysteryId:
    """_extract_mystery_id: セッション状態から mystery_id を抽出する純粋関数。"""

    def test_from_published_mystery_id_key(self):
        """Should return mystery_id from PUBLISHED_MYSTERY_ID (priority 1)."""
        state = {PUBLISHED_MYSTERY_ID: "OCC-US-BOS-20260207143025"}
        assert _extract_mystery_id(state) == "OCC-US-BOS-20260207143025"

    def test_from_published_episode_json_string(self):
        """Should extract mystery_id from PUBLISHED_EPISODE JSON string (fallback)."""
        state = {
            PUBLISHED_EPISODE: json.dumps({
                "status": "success",
                "mystery_id": "HIS-GB-EDI-20260301120000",
            }),
        }
        assert _extract_mystery_id(state) == "HIS-GB-EDI-20260301120000"

    def test_from_published_episode_dict(self):
        """Should extract mystery_id from PUBLISHED_EPISODE dict."""
        state = {
            PUBLISHED_EPISODE: {
                "status": "success",
                "mystery_id": "FLK-JP-KYO-20260315090000",
            },
        }
        assert _extract_mystery_id(state) == "FLK-JP-KYO-20260315090000"

    def test_published_mystery_id_takes_priority(self):
        """Should prefer PUBLISHED_MYSTERY_ID over PUBLISHED_EPISODE."""
        state = {
            PUBLISHED_MYSTERY_ID: "OCC-US-BOS-20260207143025",
            PUBLISHED_EPISODE: json.dumps({"mystery_id": "WRONG-ID"}),
        }
        assert _extract_mystery_id(state) == "OCC-US-BOS-20260207143025"

    def test_empty_state_returns_none(self):
        """Should return None for empty session state."""
        assert _extract_mystery_id({}) is None

    def test_no_mystery_id_in_published_episode(self):
        """Should return None when PUBLISHED_EPISODE has no mystery_id."""
        state = {PUBLISHED_EPISODE: json.dumps({"status": "error"})}
        assert _extract_mystery_id(state) is None

    def test_invalid_json_returns_none(self):
        """Should return None when PUBLISHED_EPISODE is invalid JSON."""
        state = {PUBLISHED_EPISODE: "not valid json"}
        assert _extract_mystery_id(state) is None

    def test_non_json_text_returns_none(self):
        """Should return None when PUBLISHED_EPISODE is plain text."""
        state = {PUBLISHED_EPISODE: "Pipeline completed successfully"}
        assert _extract_mystery_id(state) is None

    def test_empty_string_published_episode(self):
        """Should return None when PUBLISHED_EPISODE is empty string."""
        state = {PUBLISHED_EPISODE: ""}
        assert _extract_mystery_id(state) is None


class TestBuildStateSummary:
    """_build_state_summary() の単体テスト"""

    def test_missing_keys(self):
        """存在しないキーは 'missing' と表示される。"""
        summary = _build_state_summary({})["session_state_summary"]
        assert summary["mystery_report"] == "missing"
        assert summary["creative_content"] == "missing"
        assert summary["structured_report"] == "missing"
        assert summary["image_metadata"] == "missing"
        assert summary["published_mystery_id"] == "missing"
        assert summary["published_episode"] == "missing"

    def test_string_values(self):
        """文字列値は文字数付きで表示される。"""
        state = {"mystery_report": "x" * 100, "creative_content": "hello"}
        summary = _build_state_summary(state)["session_state_summary"]
        assert summary["mystery_report"] == "present (100 chars)"
        assert summary["creative_content"] == "present (5 chars)"

    def test_dict_values(self):
        """dict 値はキー数付きで表示される。"""
        state = {"structured_report": {"a": 1, "b": 2, "c": 3}}
        summary = _build_state_summary(state)["session_state_summary"]
        assert summary["structured_report"] == "present (dict, 3 keys)"

    def test_other_types(self):
        """その他の型は型名付きで表示される。"""
        state = {"image_metadata": 42}
        summary = _build_state_summary(state)["session_state_summary"]
        assert summary["image_metadata"] == "present (int)"

    def test_mixed_state(self):
        """複合状態が正しくサマリ化される。"""
        state = {
            "mystery_report": "A valid analysis...",
            "creative_content": "A blog post...",
            "structured_report": {"title": "test", "classification": "HIS"},
            "image_metadata": {"url": "https://..."},
        }
        summary = _build_state_summary(state)["session_state_summary"]
        assert "present" in summary["mystery_report"]
        assert "present" in summary["creative_content"]
        assert "present (dict, 2 keys)" == summary["structured_report"]
        assert "present (dict, 1 keys)" == summary["image_metadata"]
        assert summary["published_mystery_id"] == "missing"
        assert summary["published_episode"] == "missing"
