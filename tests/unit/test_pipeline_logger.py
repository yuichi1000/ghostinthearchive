"""Unit tests for PipelineLogger utility."""


from freezegun import freeze_time

from archive_agents.utils.pipeline_logger import PipelineLogger


class TestPipelineLoggerInit:
    """Tests for PipelineLogger initialization."""

    def test_init_empty_logs(self):
        """New PipelineLogger should have empty logs."""
        logger = PipelineLogger()
        assert logger.logs == []

    def test_init_no_current_agent(self):
        """New PipelineLogger should have no current agent."""
        logger = PipelineLogger()
        assert logger._current_agent is None
        assert logger._start_time is None


class TestStartAgent:
    """Tests for start_agent method."""

    @freeze_time("2024-01-15 12:00:00", tz_offset=0)
    def test_start_agent_creates_entry(self):
        """start_agent should create a log entry with running status."""
        logger = PipelineLogger()
        logger.start_agent("librarian")

        assert len(logger.logs) == 1
        log = logger.logs[0]
        assert log["agent_name"] == "librarian"
        assert log["status"] == "running"
        assert log["start_time"] == "2024-01-15T12:00:00+00:00"
        assert log["end_time"] is None
        assert log["duration_seconds"] is None
        assert log["output_summary"] is None

    def test_start_agent_sets_current(self):
        """start_agent should set current agent tracking."""
        logger = PipelineLogger()
        logger.start_agent("scholar")

        assert logger._current_agent == "scholar"
        assert logger._start_time is not None

    def test_multiple_start_agents(self):
        """Starting multiple agents should create multiple entries."""
        logger = PipelineLogger()
        logger.start_agent("librarian")
        logger.start_agent("scholar")

        assert len(logger.logs) == 2
        assert logger.logs[0]["agent_name"] == "librarian"
        assert logger.logs[1]["agent_name"] == "scholar"


class TestCompleteAgent:
    """Tests for complete_agent method."""

    @freeze_time("2024-01-15 12:00:00", tz_offset=0)
    def test_complete_agent_updates_status(self):
        """complete_agent should update status to completed."""
        logger = PipelineLogger()
        logger.start_agent("librarian")

        with freeze_time("2024-01-15 12:01:30", tz_offset=0):
            logger.complete_agent("Found 15 documents")

        log = logger.logs[0]
        assert log["status"] == "completed"
        assert log["end_time"] == "2024-01-15T12:01:30+00:00"
        assert log["duration_seconds"] == 90.0
        assert log["output_summary"] == "Found 15 documents"

    def test_complete_agent_clears_current(self):
        """complete_agent should clear current agent tracking."""
        logger = PipelineLogger()
        logger.start_agent("librarian")
        logger.complete_agent("Done")

        assert logger._current_agent is None
        assert logger._start_time is None

    def test_complete_without_start_does_nothing(self):
        """complete_agent without start should not create entry."""
        logger = PipelineLogger()
        logger.complete_agent("Done")

        assert len(logger.logs) == 0


class TestErrorAgent:
    """Tests for error_agent method."""

    @freeze_time("2024-01-15 12:00:00", tz_offset=0)
    def test_error_agent_marks_error(self):
        """error_agent should update status to error."""
        logger = PipelineLogger()
        logger.start_agent("illustrator")

        with freeze_time("2024-01-15 12:00:30", tz_offset=0):
            logger.error_agent("Image generation failed")

        log = logger.logs[0]
        assert log["status"] == "error"
        assert log["end_time"] == "2024-01-15T12:00:30+00:00"
        assert log["duration_seconds"] == 30.0
        assert log["output_summary"] == "ERROR: Image generation failed"

    def test_error_without_start_does_nothing(self):
        """error_agent without start should not create entry."""
        logger = PipelineLogger()
        logger.error_agent("Failed")

        assert len(logger.logs) == 0


class TestGetLogs:
    """Tests for get_logs method."""

    def test_get_logs_returns_all(self):
        """get_logs should return all log entries."""
        logger = PipelineLogger()
        logger.start_agent("librarian")
        logger.complete_agent("Done 1")
        logger.start_agent("scholar")
        logger.complete_agent("Done 2")

        logs = logger.get_logs()
        assert len(logs) == 2
        assert logs[0]["agent_name"] == "librarian"
        assert logs[1]["agent_name"] == "scholar"

    def test_get_logs_empty(self):
        """get_logs should return empty list when no agents run."""
        logger = PipelineLogger()
        assert logger.get_logs() == []


class TestTruncate:
    """Tests for _truncate static method."""

    def test_truncate_short_text(self):
        """Short text should not be truncated."""
        result = PipelineLogger._truncate("Short text", max_length=200)
        assert result == "Short text"

    def test_truncate_exact_length(self):
        """Text at exact max length should not be truncated."""
        text = "x" * 200
        result = PipelineLogger._truncate(text, max_length=200)
        assert result == text
        assert "..." not in result

    def test_truncate_long_text(self):
        """Long text should be truncated with ellipsis."""
        text = "x" * 250
        result = PipelineLogger._truncate(text, max_length=200)
        assert len(result) == 203  # 200 + "..."
        assert result.endswith("...")

    def test_truncate_default_max_length(self):
        """Default max length should be 200."""
        text = "x" * 250
        result = PipelineLogger._truncate(text)
        assert len(result) == 203


class TestAgentTransitions:
    """Tests for full agent lifecycle transitions."""

    @freeze_time("2024-01-15 12:00:00", tz_offset=0)
    def test_full_pipeline_lifecycle(self):
        """Test complete pipeline with multiple agents."""
        logger = PipelineLogger()

        # Agent 1: Librarian
        logger.start_agent("librarian")
        with freeze_time("2024-01-15 12:01:00", tz_offset=0):
            logger.complete_agent("Found 10 documents")

        # Agent 2: Scholar
        with freeze_time("2024-01-15 12:01:00", tz_offset=0):
            logger.start_agent("scholar")
        with freeze_time("2024-01-15 12:03:00", tz_offset=0):
            logger.complete_agent("Generated 2 mystery reports")

        # Agent 3: Storyteller (with error)
        with freeze_time("2024-01-15 12:03:00", tz_offset=0):
            logger.start_agent("storyteller")
        with freeze_time("2024-01-15 12:03:30", tz_offset=0):
            logger.error_agent("Content generation timeout")

        logs = logger.get_logs()
        assert len(logs) == 3

        # Librarian
        assert logs[0]["status"] == "completed"
        assert logs[0]["duration_seconds"] == 60.0

        # Scholar
        assert logs[1]["status"] == "completed"
        assert logs[1]["duration_seconds"] == 120.0

        # Storyteller
        assert logs[2]["status"] == "error"
        assert logs[2]["duration_seconds"] == 30.0
        assert "ERROR:" in logs[2]["output_summary"]

    def test_overlapping_agent_handling(self):
        """Starting new agent before completing previous should work."""
        logger = PipelineLogger()

        logger.start_agent("librarian")
        # Start new agent without completing previous
        logger.start_agent("scholar")

        # Complete scholar
        logger.complete_agent("Done")

        logs = logger.get_logs()
        assert len(logs) == 2
        # Librarian should still be running (not updated)
        assert logs[0]["status"] == "running"
        # Scholar should be completed
        assert logs[1]["status"] == "completed"
