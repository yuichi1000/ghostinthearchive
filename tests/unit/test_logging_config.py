"""Unit tests for shared/logging_config.py"""

import asyncio
import json
import logging
import os
from unittest.mock import patch

import pytest

from shared.logging_config import (
    CloudJsonFormatter,
    PipelineContext,
    PlainTextFormatter,
    StructuredLogFilter,
    get_pipeline_context,
    set_pipeline_context,
    setup_logging,
)


@pytest.fixture(autouse=True)
def _reset_context():
    """テストごとにコンテキストをリセットする。"""
    set_pipeline_context(PipelineContext())
    yield
    set_pipeline_context(PipelineContext())


@pytest.fixture(autouse=True)
def _reset_root_logger():
    """テストごとに root logger をリセットする。"""
    root = logging.getLogger()
    original_handlers = root.handlers[:]
    original_level = root.level
    yield
    root.handlers = original_handlers
    root.level = original_level


class TestPipelineContext:
    """PipelineContext と contextvars の基本テスト"""

    def test_default_context_is_empty(self):
        ctx = get_pipeline_context()
        assert ctx.run_id == ""
        assert ctx.pipeline_type == ""
        assert ctx.mystery_id == ""

    def test_set_and_get_context(self):
        set_pipeline_context(
            PipelineContext(run_id="run-123", pipeline_type="blog", mystery_id="OCC-MA-617-20260220")
        )
        ctx = get_pipeline_context()
        assert ctx.run_id == "run-123"
        assert ctx.pipeline_type == "blog"
        assert ctx.mystery_id == "OCC-MA-617-20260220"

    def test_partial_context(self):
        set_pipeline_context(PipelineContext(pipeline_type="curator"))
        ctx = get_pipeline_context()
        assert ctx.run_id == ""
        assert ctx.pipeline_type == "curator"


class TestContextVarsAsyncIsolation:
    """contextvars のタスク間スコープ分離テスト"""

    @pytest.mark.asyncio
    async def test_context_copied_to_child_task(self):
        """asyncio.create_task() でコンテキストが子タスクにコピーされる。"""
        set_pipeline_context(PipelineContext(run_id="parent-run"))

        child_run_id = None

        async def child():
            nonlocal child_run_id
            child_run_id = get_pipeline_context().run_id

        await asyncio.create_task(child())
        assert child_run_id == "parent-run"

    @pytest.mark.asyncio
    async def test_child_task_mutation_does_not_affect_parent(self):
        """子タスクでのコンテキスト変更が親に影響しない。"""
        set_pipeline_context(PipelineContext(run_id="parent-run"))

        async def child():
            set_pipeline_context(PipelineContext(run_id="child-run"))

        await asyncio.create_task(child())
        assert get_pipeline_context().run_id == "parent-run"


class TestStructuredLogFilter:
    """StructuredLogFilter のテスト"""

    def test_injects_context_fields(self):
        set_pipeline_context(
            PipelineContext(run_id="run-456", pipeline_type="podcast")
        )
        record = logging.LogRecord(
            name="test", level=logging.INFO, pathname="", lineno=0,
            msg="hello", args=(), exc_info=None,
        )
        f = StructuredLogFilter()
        assert f.filter(record) is True
        assert record.run_id == "run-456"
        assert record.pipeline_type == "podcast"
        assert record.mystery_id == ""

    def test_empty_context_still_sets_attributes(self):
        record = logging.LogRecord(
            name="test", level=logging.INFO, pathname="", lineno=0,
            msg="hello", args=(), exc_info=None,
        )
        f = StructuredLogFilter()
        f.filter(record)
        assert record.run_id == ""
        assert record.pipeline_type == ""
        assert record.mystery_id == ""


class TestCloudJsonFormatter:
    """CloudJsonFormatter の JSON 出力テスト"""

    def _make_record(self, msg="test message", level=logging.INFO, **extra):
        record = logging.LogRecord(
            name="shared.orchestrator", level=level, pathname="", lineno=0,
            msg=msg, args=(), exc_info=None,
        )
        # extra フィールドをシミュレート
        for k, v in extra.items():
            setattr(record, k, v)
        # StructuredLogFilter の効果をシミュレート
        if not hasattr(record, "run_id"):
            record.run_id = ""
        if not hasattr(record, "pipeline_type"):
            record.pipeline_type = ""
        if not hasattr(record, "mystery_id"):
            record.mystery_id = ""
        return record

    def test_basic_json_output(self):
        formatter = CloudJsonFormatter()
        record = self._make_record()
        output = formatter.format(record)
        data = json.loads(output)
        assert data["severity"] == "INFO"
        assert data["message"] == "test message"
        assert data["logger"] == "shared.orchestrator"
        assert "timestamp" in data

    def test_severity_mapping(self):
        formatter = CloudJsonFormatter()
        for level, expected in [
            (logging.DEBUG, "DEBUG"),
            (logging.INFO, "INFO"),
            (logging.WARNING, "WARNING"),
            (logging.ERROR, "ERROR"),
            (logging.CRITICAL, "CRITICAL"),
        ]:
            record = self._make_record(level=level)
            data = json.loads(formatter.format(record))
            assert data["severity"] == expected

    def test_context_fields_included_when_set(self):
        formatter = CloudJsonFormatter()
        record = self._make_record(
            run_id="run-789",
            pipeline_type="blog",
            mystery_id="HIS-NY-212-20260220",
        )
        data = json.loads(formatter.format(record))
        assert data["run_id"] == "run-789"
        assert data["pipeline_type"] == "blog"
        assert data["mystery_id"] == "HIS-NY-212-20260220"

    def test_empty_context_fields_excluded(self):
        formatter = CloudJsonFormatter()
        record = self._make_record()
        data = json.loads(formatter.format(record))
        assert "run_id" not in data
        assert "pipeline_type" not in data
        assert "mystery_id" not in data

    def test_extra_fields_included(self):
        formatter = CloudJsonFormatter()
        record = self._make_record(
            agent_name="Scholar",
            duration_seconds=12.5,
            status="completed",
        )
        data = json.loads(formatter.format(record))
        assert data["agent_name"] == "Scholar"
        assert data["duration_seconds"] == 12.5
        assert data["status"] == "completed"

    def test_exception_included(self):
        formatter = CloudJsonFormatter()
        try:
            raise ValueError("test error")
        except ValueError:
            import sys
            record = self._make_record()
            record.exc_info = sys.exc_info()
        data = json.loads(formatter.format(record))
        assert "exception" in data
        assert "ValueError: test error" in data["exception"]

    def test_percent_formatting_applied(self):
        """% フォーマットが正しく適用される。"""
        record = logging.LogRecord(
            name="test", level=logging.INFO, pathname="", lineno=0,
            msg="Agent %s completed in %.1fs", args=("Scholar", 12.5),
            exc_info=None,
        )
        record.run_id = ""
        record.pipeline_type = ""
        record.mystery_id = ""
        formatter = CloudJsonFormatter()
        data = json.loads(formatter.format(record))
        assert data["message"] == "Agent Scholar completed in 12.5s"


class TestPlainTextFormatter:
    """PlainTextFormatter のテスト"""

    def test_basic_format(self):
        formatter = PlainTextFormatter()
        record = logging.LogRecord(
            name="test.module", level=logging.INFO, pathname="", lineno=0,
            msg="hello world", args=(), exc_info=None,
        )
        record.run_id = ""
        record.pipeline_type = ""
        record.mystery_id = ""
        output = formatter.format(record)
        assert "test.module" in output
        assert "[INFO]" in output
        assert "hello world" in output
        # コンテキストなしなら [] 部分は付かない
        assert output.endswith("hello world")

    def test_context_appended(self):
        formatter = PlainTextFormatter()
        record = logging.LogRecord(
            name="test", level=logging.INFO, pathname="", lineno=0,
            msg="hello", args=(), exc_info=None,
        )
        record.run_id = "run-123"
        record.pipeline_type = "blog"
        record.mystery_id = ""
        output = formatter.format(record)
        assert "[run_id=run-123, pipeline_type=blog]" in output


class TestSetupLogging:
    """setup_logging() のテスト"""

    def test_local_uses_plain_text(self):
        with patch.dict(os.environ, {}, clear=True):
            # K_SERVICE がない → ローカル
            os.environ.pop("K_SERVICE", None)
            setup_logging(force=True)

        root = logging.getLogger()
        assert len(root.handlers) == 1
        assert isinstance(root.handlers[0].formatter, PlainTextFormatter)

    def test_cloud_run_uses_json(self):
        with patch.dict(os.environ, {"K_SERVICE": "pipeline-service"}):
            setup_logging(force=True)

        root = logging.getLogger()
        assert len(root.handlers) == 1
        assert isinstance(root.handlers[0].formatter, CloudJsonFormatter)

    def test_filter_attached(self):
        setup_logging(force=True)
        root = logging.getLogger()
        filters = root.handlers[0].filters
        assert any(isinstance(f, StructuredLogFilter) for f in filters)

    def test_idempotent_without_force(self):
        setup_logging(force=True)
        root = logging.getLogger()
        handler_count = len(root.handlers)
        setup_logging()  # force=False → 追加しない
        assert len(root.handlers) == handler_count

    def test_force_replaces_handlers(self):
        setup_logging(force=True)
        setup_logging(force=True)
        root = logging.getLogger()
        assert len(root.handlers) == 1

    def test_integration_json_output(self):
        """setup_logging → logger.info → JSON 出力の統合テスト。"""
        with patch.dict(os.environ, {"K_SERVICE": "test-service"}):
            setup_logging(force=True)

        set_pipeline_context(PipelineContext(run_id="int-test", pipeline_type="blog"))

        test_logger = logging.getLogger("integration_test")
        # ハンドラの出力をキャプチャ
        handler = logging.getLogger().handlers[0]
        record = test_logger.makeRecord(
            "integration_test", logging.INFO, "", 0,
            "Agent started", (), None,
        )
        record.agent_name = "Scholar"  # extra フィールド
        handler.handle(record)
        # テストは例外なく完了すれば OK（出力は stdout に書かれる）
