"""Tests for pipeline failure logging to Firestore."""

from unittest.mock import MagicMock, patch

from shared.pipeline_failure import get_recent_failures, log_pipeline_failure


class TestLogPipelineFailure:
    """log_pipeline_failure のテスト。"""

    def test_logs_failure_to_firestore(self, mock_firestore_client):
        """Firestore の pipeline_failures コレクションに書き込む。"""
        with patch("shared.firestore.get_firestore_client", return_value=mock_firestore_client):
            log_pipeline_failure(
                theme="Bell Witch of Tennessee",
                stage="librarian",
                reason="NO_DOCUMENTS_FOUND: All Librarians returned no documents.",
            )

        mock_firestore_client.collection.assert_called_with("pipeline_failures")
        mock_firestore_client.collection().document().set.assert_called_once()

        # 書き込まれたデータを検証
        call_args = mock_firestore_client.collection().document().set.call_args
        data = call_args[0][0]
        assert data["theme"] == "Bell Witch of Tennessee"
        assert data["stage"] == "librarian"
        assert "NO_DOCUMENTS_FOUND" in data["reason"]
        assert "timestamp" in data

    def test_does_not_raise_on_firestore_error(self):
        """Firestore エラー時に例外を投げない（非ブロッキング）。"""
        mock_client = MagicMock()
        mock_client.collection.side_effect = Exception("Firestore unavailable")

        with patch("shared.firestore.get_firestore_client", return_value=mock_client):
            # 例外が発生しないことを確認
            log_pipeline_failure(
                theme="Test theme",
                stage="librarian",
                reason="Test error",
            )

    def test_includes_run_id_when_provided(self, mock_firestore_client):
        """run_id が指定されている場合、書き込みデータに含める。"""
        with patch("shared.firestore.get_firestore_client", return_value=mock_firestore_client):
            log_pipeline_failure(
                theme="Test theme",
                stage="scholar",
                reason="INSUFFICIENT_DATA",
                run_id="run-123",
            )

        call_args = mock_firestore_client.collection().document().set.call_args
        data = call_args[0][0]
        assert data["run_id"] == "run-123"


class TestGetRecentFailures:
    """get_recent_failures のテスト。"""

    def test_returns_recent_failure_themes(self):
        """最近失敗したテーマのリストを返す。"""
        mock_client = MagicMock()

        # Firestore クエリ結果をモック
        mock_doc1 = MagicMock()
        mock_doc1.to_dict.return_value = {"theme": "Bell Witch of Tennessee", "stage": "librarian"}
        mock_doc2 = MagicMock()
        mock_doc2.to_dict.return_value = {"theme": "Roanoke Colony", "stage": "scholar"}

        mock_query = MagicMock()
        mock_query.order_by.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.stream.return_value = [mock_doc1, mock_doc2]
        mock_client.collection.return_value = mock_query

        with patch("shared.firestore.get_firestore_client", return_value=mock_client):
            result = get_recent_failures(limit=10)

        assert len(result) == 2
        assert result[0]["theme"] == "Bell Witch of Tennessee"
        assert result[1]["theme"] == "Roanoke Colony"

    def test_returns_empty_on_error(self):
        """Firestore エラー時に空リストを返す。"""
        mock_client = MagicMock()
        mock_client.collection.side_effect = Exception("Connection error")

        with patch("shared.firestore.get_firestore_client", return_value=mock_client):
            result = get_recent_failures()

        assert result == []
