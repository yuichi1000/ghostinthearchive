"""Unit tests for shared/logging_config.py — HealthCheckFilter。"""

import logging

from shared.logging_config import HealthCheckFilter


class TestHealthCheckFilter:
    """HealthCheckFilter のテスト。"""

    def _make_record(self, msg: str, level: int = logging.INFO) -> logging.LogRecord:
        """テスト用 LogRecord を生成する。"""
        return logging.LogRecord(
            name="uvicorn.access",
            level=level,
            pathname="",
            lineno=0,
            msg=msg,
            args=(),
            exc_info=None,
        )

    def test_suppresses_health_check_info_log(self):
        """Should suppress INFO log containing /health."""
        f = HealthCheckFilter()
        record = self._make_record('GET /health HTTP/1.1 200')
        assert f.filter(record) is False

    def test_passes_non_health_info_log(self):
        """Should pass INFO log not related to /health."""
        f = HealthCheckFilter()
        record = self._make_record('POST /suggest-theme HTTP/1.1 200')
        assert f.filter(record) is True

    def test_passes_health_check_warning_log(self):
        """Should pass WARNING+ logs even if they contain /health."""
        f = HealthCheckFilter()
        record = self._make_record('/health endpoint error', logging.WARNING)
        assert f.filter(record) is True
