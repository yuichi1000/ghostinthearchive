"""Unit tests for podcast_agents/tools/firestore_tools.py - Podcast Firestore ツール."""

from unittest.mock import MagicMock, patch

import pytest

from podcast_agents.tools.firestore_tools import (
    load_mystery,
    create_podcast,
    get_podcast,
    save_script_result,
    save_audio_result,
    set_podcast_status,
)


@pytest.fixture
def mock_db():
    """Mock Firestore client."""
    with patch("podcast_agents.tools.firestore_tools.get_firestore_client") as mock:
        client = MagicMock()
        mock.return_value = client
        yield client


class TestLoadMystery:
    """Tests for load_mystery()."""

    def test_returns_mystery_data(self, mock_db):
        """存在するドキュメントのデータを返す。"""
        mock_doc = MagicMock()
        mock_doc.exists = True
        mock_doc.to_dict.return_value = {"title": "Test Mystery", "narrative_content": "..."}
        mock_db.collection.return_value.document.return_value.get.return_value = mock_doc

        result = load_mystery("OCC-MA-617-20260207143025")

        assert result["title"] == "Test Mystery"
        mock_db.collection.assert_called_with("mysteries")

    def test_returns_none_for_missing(self, mock_db):
        """存在しないドキュメントは None を返す。"""
        mock_doc = MagicMock()
        mock_doc.exists = False
        mock_db.collection.return_value.document.return_value.get.return_value = mock_doc

        result = load_mystery("NONEXISTENT")
        assert result is None


class TestCreatePodcast:
    """Tests for create_podcast()."""

    def test_creates_document_with_correct_fields(self, mock_db):
        """正しいフィールドでドキュメントを作成する。"""
        # load_mystery のモック
        mock_mystery_doc = MagicMock()
        mock_mystery_doc.exists = True
        mock_mystery_doc.to_dict.return_value = {"title": "The Vanishing Ship"}

        mock_doc_ref = MagicMock()
        mock_doc_ref.id = "generated-podcast-id"
        mock_db.collection.return_value.document.return_value.get.return_value = mock_mystery_doc
        mock_db.collection.return_value.add.return_value = (None, mock_doc_ref)

        result = create_podcast("OCC-MA-617-20260207143025", "ジョーク多めで")

        assert result == "generated-podcast-id"

        # add() に渡されたデータを検証
        call_args = mock_db.collection.return_value.add.call_args[0][0]
        assert call_args["mystery_id"] == "OCC-MA-617-20260207143025"
        assert call_args["mystery_title"] == "The Vanishing Ship"
        assert call_args["status"] == "script_generating"
        assert call_args["custom_instructions"] == "ジョーク多めで"
        assert call_args["script"] is None
        assert call_args["audio"] is None
        assert call_args["pipeline_run_id"] is None

    def test_creates_document_with_pipeline_run_id(self, mock_db):
        """pipeline_run_id を指定した場合、即座に紐付けされる。"""
        mock_mystery_doc = MagicMock()
        mock_mystery_doc.exists = True
        mock_mystery_doc.to_dict.return_value = {"title": "The Vanishing Ship"}

        mock_doc_ref = MagicMock()
        mock_doc_ref.id = "generated-podcast-id"
        mock_db.collection.return_value.document.return_value.get.return_value = mock_mystery_doc
        mock_db.collection.return_value.add.return_value = (None, mock_doc_ref)

        result = create_podcast(
            "OCC-MA-617-20260207143025", pipeline_run_id="run-123"
        )

        assert result == "generated-podcast-id"
        call_args = mock_db.collection.return_value.add.call_args[0][0]
        assert call_args["pipeline_run_id"] == "run-123"

    def test_uses_mystery_id_as_title_when_mystery_not_found(self, mock_db):
        """mystery が見つからない場合は ID をタイトルとして使用する。"""
        mock_mystery_doc = MagicMock()
        mock_mystery_doc.exists = False

        mock_doc_ref = MagicMock()
        mock_doc_ref.id = "podcast-id"
        mock_db.collection.return_value.document.return_value.get.return_value = mock_mystery_doc
        mock_db.collection.return_value.add.return_value = (None, mock_doc_ref)

        result = create_podcast("MISSING-ID")
        assert result == "podcast-id"


class TestGetPodcast:
    """Tests for get_podcast()."""

    def test_returns_podcast_with_id(self, mock_db):
        """ドキュメントデータに podcast_id を付与して返す。"""
        mock_doc = MagicMock()
        mock_doc.exists = True
        mock_doc.id = "podcast-123"
        mock_doc.to_dict.return_value = {
            "mystery_id": "OCC-MA-617-20260207143025",
            "status": "script_ready",
        }
        mock_db.collection.return_value.document.return_value.get.return_value = mock_doc

        result = get_podcast("podcast-123")

        assert result["podcast_id"] == "podcast-123"
        assert result["status"] == "script_ready"
        mock_db.collection.assert_called_with("podcasts")

    def test_returns_none_for_missing(self, mock_db):
        """存在しない場合は None を返す。"""
        mock_doc = MagicMock()
        mock_doc.exists = False
        mock_db.collection.return_value.document.return_value.get.return_value = mock_doc

        result = get_podcast("nonexistent")
        assert result is None


class TestSaveScriptResult:
    """Tests for save_script_result()."""

    def test_updates_document_with_script(self, mock_db):
        """脚本データとステータスを更新する。"""
        script = {
            "episode_title": "Test Episode",
            "segments": [{"type": "intro", "label": "Intro", "text": "Hello"}],
        }

        save_script_result("podcast-123", script, "テスト日本語訳")

        mock_db.collection.assert_called_with("podcasts")
        update_call = mock_db.collection.return_value.document.return_value.update
        update_call.assert_called_once()

        update_data = update_call.call_args[0][0]
        assert update_data["script"] == script
        assert update_data["script_ja"] == "テスト日本語訳"
        assert update_data["status"] == "script_ready"
        assert update_data["error_message"] is None


class TestSaveAudioResult:
    """Tests for save_audio_result()."""

    def test_updates_document_with_audio_metadata(self, mock_db):
        """音声メタデータとステータスを更新する。"""
        audio = {
            "gcs_path": "gs://bucket/podcasts/id/episode.mp3",
            "public_url": "https://example.com/episode.mp3",
            "duration_seconds": 1200.5,
            "voice_name": "en-US-Studio-O",
            "format": "mp3",
        }

        save_audio_result("podcast-123", audio)

        update_data = mock_db.collection.return_value.document.return_value.update.call_args[0][0]
        assert update_data["audio"] == audio
        assert update_data["status"] == "audio_ready"


class TestSetPodcastStatus:
    """Tests for set_podcast_status()."""

    def test_updates_status(self, mock_db):
        """ステータスを更新する。"""
        set_podcast_status("podcast-123", "audio_generating")

        update_data = mock_db.collection.return_value.document.return_value.update.call_args[0][0]
        assert update_data["status"] == "audio_generating"

    def test_includes_error_message(self, mock_db):
        """エラーメッセージを含めて更新する。"""
        set_podcast_status("podcast-123", "error", "TTS failed")

        update_data = mock_db.collection.return_value.document.return_value.update.call_args[0][0]
        assert update_data["status"] == "error"
        assert update_data["error_message"] == "TTS failed"

    def test_truncates_long_error_message(self, mock_db):
        """長いエラーメッセージを500文字に切り詰める。"""
        long_error = "E" * 1000
        set_podcast_status("podcast-123", "error", long_error)

        update_data = mock_db.collection.return_value.document.return_value.update.call_args[0][0]
        assert len(update_data["error_message"]) == 500
