"""Unit tests for shared/pipeline_run.py."""

import logging

from unittest.mock import MagicMock, patch



class TestCreatePipelineRun:
    """Tests for create_pipeline_run function."""

    def test_create_blog_pipeline_run(self, mock_firestore_client):
        """Should create a blog pipeline run with query."""
        mock_doc_ref = MagicMock()
        mock_doc_ref.id = "auto-generated-id"
        mock_firestore_client.collection.return_value.add.return_value = (
            None,
            mock_doc_ref,
        )

        with patch(
            "shared.pipeline_run.get_firestore_client",
            return_value=mock_firestore_client,
        ):
            from shared.pipeline_run import create_pipeline_run

            run_id = create_pipeline_run("blog", query="Boston mysteries")

        assert run_id == "auto-generated-id"
        mock_firestore_client.collection.assert_called_with("pipeline_runs")

        call_args = mock_firestore_client.collection.return_value.add.call_args
        doc_data = call_args[0][0]
        assert doc_data["type"] == "blog"
        assert doc_data["status"] == "running"
        assert doc_data["query"] == "Boston mysteries"
        assert doc_data["mystery_id"] is None
        assert doc_data["current_agent"] is None
        assert doc_data["pipeline_log"] == []

    def test_create_translate_pipeline_run(self, mock_firestore_client):
        """Should create a translate pipeline run with mystery_id."""
        mock_doc_ref = MagicMock()
        mock_doc_ref.id = "translate-run-id"
        mock_firestore_client.collection.return_value.add.return_value = (
            None,
            mock_doc_ref,
        )

        with patch(
            "shared.pipeline_run.get_firestore_client",
            return_value=mock_firestore_client,
        ):
            from shared.pipeline_run import create_pipeline_run

            run_id = create_pipeline_run(
                "translate", mystery_id="OCC-MA-617-20260207143025"
            )

        assert run_id == "translate-run-id"
        call_args = mock_firestore_client.collection.return_value.add.call_args
        doc_data = call_args[0][0]
        assert doc_data["type"] == "translate"
        assert doc_data["mystery_id"] == "OCC-MA-617-20260207143025"
        assert doc_data["query"] is None

    def test_create_podcast_pipeline_run(self, mock_firestore_client):
        """Should create a podcast pipeline run."""
        mock_doc_ref = MagicMock()
        mock_doc_ref.id = "podcast-run-id"
        mock_firestore_client.collection.return_value.add.return_value = (
            None,
            mock_doc_ref,
        )

        with patch(
            "shared.pipeline_run.get_firestore_client",
            return_value=mock_firestore_client,
        ):
            from shared.pipeline_run import create_pipeline_run

            run_id = create_pipeline_run(
                "podcast", mystery_id="FLK-NY-212-20260207143025"
            )

        assert run_id == "podcast-run-id"

    def test_create_pipeline_run_firestore_error_returns_none(
        self, mock_firestore_client
    ):
        """Should return None if Firestore write fails."""
        mock_firestore_client.collection.return_value.add.side_effect = Exception(
            "Network error"
        )

        with patch(
            "shared.pipeline_run.get_firestore_client",
            return_value=mock_firestore_client,
        ):
            from shared.pipeline_run import create_pipeline_run

            run_id = create_pipeline_run("blog", query="test")

        assert run_id is None


class TestUpdateAgentStarted:
    """Tests for update_agent_started function."""

    def test_update_agent_started(self, mock_firestore_client):
        """Should update document with new agent and log entry."""
        mock_doc = MagicMock()
        mock_doc.exists = True
        mock_doc.to_dict.return_value = {
            "pipeline_log": [
                {"agent_name": "librarian", "status": "running"}
            ]
        }
        mock_doc_ref = MagicMock()
        mock_doc_ref.get.return_value = mock_doc
        mock_firestore_client.collection.return_value.document.return_value = (
            mock_doc_ref
        )

        log_entry = {
            "agent_name": "librarian",
            "status": "running",
            "start_time": "2024-01-15T12:00:00+00:00",
        }

        with patch(
            "shared.pipeline_run.get_firestore_client",
            return_value=mock_firestore_client,
        ):
            from shared.pipeline_run import update_agent_started

            index = update_agent_started("run-123", "librarian", log_entry)

        assert index == 0
        mock_doc_ref.update.assert_called_once()

    def test_update_agent_started_with_none_run_id(self):
        """Should return None when run_id is None."""
        from shared.pipeline_run import update_agent_started

        result = update_agent_started(None, "librarian", {})
        assert result is None

    def test_update_agent_started_firestore_error(self, mock_firestore_client):
        """Should return None on Firestore error."""
        mock_doc_ref = MagicMock()
        mock_doc_ref.update.side_effect = Exception("Write failed")
        mock_firestore_client.collection.return_value.document.return_value = (
            mock_doc_ref
        )

        with patch(
            "shared.pipeline_run.get_firestore_client",
            return_value=mock_firestore_client,
        ):
            from shared.pipeline_run import update_agent_started

            result = update_agent_started("run-123", "librarian", {})

        assert result is None


class TestUpdateAgentCompleted:
    """Tests for update_agent_completed function."""

    def test_update_agent_completed(self, mock_firestore_client):
        """Should update the log entry at given index."""
        existing_log = {
            "agent_name": "librarian",
            "status": "running",
            "start_time": "2024-01-15T12:00:00+00:00",
            "end_time": None,
        }
        updated_log = {
            "agent_name": "librarian",
            "status": "completed",
            "start_time": "2024-01-15T12:00:00+00:00",
            "end_time": "2024-01-15T12:01:00+00:00",
            "duration_seconds": 60.0,
            "output_summary": "Found 15 documents",
        }

        mock_doc = MagicMock()
        mock_doc.exists = True
        mock_doc.to_dict.return_value = {"pipeline_log": [existing_log]}
        mock_doc_ref = MagicMock()
        mock_doc_ref.get.return_value = mock_doc
        mock_firestore_client.collection.return_value.document.return_value = (
            mock_doc_ref
        )

        with patch(
            "shared.pipeline_run.get_firestore_client",
            return_value=mock_firestore_client,
        ):
            from shared.pipeline_run import update_agent_completed

            update_agent_completed("run-123", 0, updated_log)

        call_args = mock_doc_ref.update.call_args
        updated_data = call_args[0][0]
        assert updated_data["pipeline_log"][0]["status"] == "completed"
        assert updated_data["current_agent"] is None

    def test_update_agent_completed_with_none_run_id(self):
        """Should do nothing when run_id is None."""
        from shared.pipeline_run import update_agent_completed

        # Should not raise
        update_agent_completed(None, 0, {})

    def test_update_agent_completed_with_none_index(self):
        """Should do nothing when log_index is None."""
        from shared.pipeline_run import update_agent_completed

        # Should not raise
        update_agent_completed("run-123", None, {})

    def test_update_agent_completed_doc_not_found(self, mock_firestore_client):
        """Should do nothing when document does not exist."""
        mock_doc = MagicMock()
        mock_doc.exists = False
        mock_doc_ref = MagicMock()
        mock_doc_ref.get.return_value = mock_doc
        mock_firestore_client.collection.return_value.document.return_value = (
            mock_doc_ref
        )

        with patch(
            "shared.pipeline_run.get_firestore_client",
            return_value=mock_firestore_client,
        ):
            from shared.pipeline_run import update_agent_completed

            update_agent_completed("run-123", 0, {})

        mock_doc_ref.update.assert_not_called()


class TestCompletePipelineRun:
    """Tests for complete_pipeline_run function."""

    def test_complete_pipeline_run(self, mock_firestore_client):
        """Should mark pipeline run as completed."""
        mock_doc_ref = MagicMock()
        mock_firestore_client.collection.return_value.document.return_value = (
            mock_doc_ref
        )

        with patch(
            "shared.pipeline_run.get_firestore_client",
            return_value=mock_firestore_client,
        ):
            from shared.pipeline_run import complete_pipeline_run

            complete_pipeline_run("run-123", mystery_id="OCC-MA-617-20260207")

        call_args = mock_doc_ref.update.call_args
        update_data = call_args[0][0]
        assert update_data["status"] == "completed"
        assert update_data["mystery_id"] == "OCC-MA-617-20260207"
        assert update_data["current_agent"] is None
        assert "completed_at" in update_data

    def test_complete_pipeline_run_without_mystery_id(
        self, mock_firestore_client
    ):
        """Should complete without setting mystery_id."""
        mock_doc_ref = MagicMock()
        mock_firestore_client.collection.return_value.document.return_value = (
            mock_doc_ref
        )

        with patch(
            "shared.pipeline_run.get_firestore_client",
            return_value=mock_firestore_client,
        ):
            from shared.pipeline_run import complete_pipeline_run

            complete_pipeline_run("run-123")

        call_args = mock_doc_ref.update.call_args
        update_data = call_args[0][0]
        assert "mystery_id" not in update_data

    def test_complete_pipeline_run_with_none_run_id(self):
        """Should do nothing when run_id is None."""
        from shared.pipeline_run import complete_pipeline_run

        # Should not raise
        complete_pipeline_run(None)

    def test_complete_pipeline_run_firestore_error(
        self, mock_firestore_client
    ):
        """Should not raise when Firestore write fails."""
        mock_doc_ref = MagicMock()
        mock_doc_ref.update.side_effect = Exception("Write failed")
        mock_firestore_client.collection.return_value.document.return_value = (
            mock_doc_ref
        )

        with patch(
            "shared.pipeline_run.get_firestore_client",
            return_value=mock_firestore_client,
        ):
            from shared.pipeline_run import complete_pipeline_run

            # Should not raise
            complete_pipeline_run("run-123")


class TestErrorPipelineRun:
    """Tests for error_pipeline_run function."""

    def test_error_pipeline_run(self, mock_firestore_client):
        """Should mark pipeline run as error with message."""
        mock_doc_ref = MagicMock()
        mock_firestore_client.collection.return_value.document.return_value = (
            mock_doc_ref
        )

        with patch(
            "shared.pipeline_run.get_firestore_client",
            return_value=mock_firestore_client,
        ):
            from shared.pipeline_run import error_pipeline_run

            error_pipeline_run("run-123", "Translation failed: timeout")

        call_args = mock_doc_ref.update.call_args
        update_data = call_args[0][0]
        assert update_data["status"] == "error"
        assert update_data["error_message"] == "Translation failed: timeout"
        assert update_data["current_agent"] is None

    def test_error_pipeline_run_truncates_long_message(
        self, mock_firestore_client
    ):
        """Should truncate error message to 500 characters."""
        mock_doc_ref = MagicMock()
        mock_firestore_client.collection.return_value.document.return_value = (
            mock_doc_ref
        )

        long_message = "x" * 1000

        with patch(
            "shared.pipeline_run.get_firestore_client",
            return_value=mock_firestore_client,
        ):
            from shared.pipeline_run import error_pipeline_run

            error_pipeline_run("run-123", long_message)

        call_args = mock_doc_ref.update.call_args
        update_data = call_args[0][0]
        assert len(update_data["error_message"]) == 500

    def test_error_pipeline_run_with_none_run_id(self):
        """Should do nothing when run_id is None."""
        from shared.pipeline_run import error_pipeline_run

        # Should not raise
        error_pipeline_run(None, "some error")

    def test_error_pipeline_run_with_detail(self, mock_firestore_client):
        """error_detail が Firestore に保存される。"""
        mock_doc_ref = MagicMock()
        mock_firestore_client.collection.return_value.document.return_value = (
            mock_doc_ref
        )

        detail = {
            "error_type": "gate_failure",
            "failed_stage": "publisher",
            "session_state_summary": {"mystery_report": "present (500 chars)"},
        }

        with patch(
            "shared.pipeline_run.get_firestore_client",
            return_value=mock_firestore_client,
        ):
            from shared.pipeline_run import error_pipeline_run

            error_pipeline_run("run-123", "公開処理で問題が発生", error_detail=detail)

        call_args = mock_doc_ref.update.call_args
        update_data = call_args[0][0]
        assert update_data["status"] == "error"
        assert update_data["error_detail"] == detail
        assert update_data["error_detail"]["error_type"] == "gate_failure"

    def test_error_pipeline_run_without_detail(self, mock_firestore_client):
        """error_detail なしでも従来通り動作する。"""
        mock_doc_ref = MagicMock()
        mock_firestore_client.collection.return_value.document.return_value = (
            mock_doc_ref
        )

        with patch(
            "shared.pipeline_run.get_firestore_client",
            return_value=mock_firestore_client,
        ):
            from shared.pipeline_run import error_pipeline_run

            error_pipeline_run("run-123", "some error")

        call_args = mock_doc_ref.update.call_args
        update_data = call_args[0][0]
        assert update_data["status"] == "error"
        assert "error_detail" not in update_data

    def test_error_pipeline_run_firestore_error(self, mock_firestore_client):
        """Should not raise when Firestore write fails."""
        mock_doc_ref = MagicMock()
        mock_doc_ref.update.side_effect = Exception("Network error")
        mock_firestore_client.collection.return_value.document.return_value = (
            mock_doc_ref
        )

        with patch(
            "shared.pipeline_run.get_firestore_client",
            return_value=mock_firestore_client,
        ):
            from shared.pipeline_run import error_pipeline_run

            # Should not raise
            error_pipeline_run("run-123", "some error")

    def test_error_pipeline_run_logs_at_error_level(
        self, mock_firestore_client, caplog
    ):
        """error_pipeline_run が ERROR レベルでログ出力する。"""
        mock_doc_ref = MagicMock()
        mock_firestore_client.collection.return_value.document.return_value = (
            mock_doc_ref
        )

        with patch(
            "shared.pipeline_run.get_firestore_client",
            return_value=mock_firestore_client,
        ):
            from shared.pipeline_run import error_pipeline_run

            with caplog.at_level(logging.ERROR, logger="shared.pipeline_run"):
                error_pipeline_run("run-err-001", "記事の生成に失敗しました")

        # ERROR レベルでエラーメッセージが含まれる
        error_records = [
            r for r in caplog.records
            if r.levelno == logging.ERROR and "Pipeline run errored" in r.message
        ]
        assert len(error_records) == 1
        assert "run-err-001" in error_records[0].message
        assert "記事の生成に失敗しました" in error_records[0].message
