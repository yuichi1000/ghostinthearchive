"""Integration tests for Publisher tools.

These tests require Firebase Emulator to be running:
    firebase emulators:start --only firestore,storage

Run with:
    pytest tests/integration/test_publisher_tools.py -v -m integration
"""

import json
import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


class TestPublishMystery:
    """Tests for publish_mystery function."""

    def test_publish_mystery_success(self, mock_firestore_client, sample_mystery_report_data):
        """publish_mystery should successfully save to Firestore."""
        with patch("archive_agents.tools.publisher_tools.get_firestore_client", return_value=mock_firestore_client):
            from archive_agents.tools.publisher_tools import publish_mystery

            mystery_json = json.dumps(sample_mystery_report_data)
            result = json.loads(publish_mystery(mystery_json))

            assert result["status"] == "success"
            assert result["mystery_id"] == "MYSTERY-1842-BOSTON-001"
            assert "mysteries/MYSTERY-1842-BOSTON-001" in result["firestore_path"]

            # Verify Firestore was called
            mock_firestore_client.collection.assert_called_with("mysteries")

    def test_publish_mystery_missing_id(self, mock_firestore_client):
        """publish_mystery should return error if mystery_id is missing."""
        with patch("archive_agents.tools.publisher_tools.get_firestore_client", return_value=mock_firestore_client):
            from archive_agents.tools.publisher_tools import publish_mystery

            mystery_json = json.dumps({"title": "Test", "summary": "Test"})
            result = json.loads(publish_mystery(mystery_json))

            assert result["status"] == "error"
            assert "mystery_id is required" in result["error"]

    def test_publish_mystery_sets_timestamps(self, mock_firestore_client, sample_mystery_report_data):
        """publish_mystery should automatically set timestamps."""
        captured_data = {}

        def capture_set(data):
            captured_data.update(data)

        mock_doc = MagicMock()
        mock_doc.set.side_effect = capture_set
        mock_firestore_client.collection.return_value.document.return_value = mock_doc

        with patch("archive_agents.tools.publisher_tools.get_firestore_client", return_value=mock_firestore_client):
            from archive_agents.tools.publisher_tools import publish_mystery

            mystery_json = json.dumps(sample_mystery_report_data)
            publish_mystery(mystery_json)

            assert "createdAt" in captured_data
            assert "updatedAt" in captured_data
            assert captured_data["status"] == "pending"

    def test_publish_mystery_published_status_sets_publishedAt(self, mock_firestore_client, sample_mystery_report_data):
        """publish_mystery should set publishedAt when status is published."""
        captured_data = {}

        def capture_set(data):
            captured_data.update(data)

        mock_doc = MagicMock()
        mock_doc.set.side_effect = capture_set
        mock_firestore_client.collection.return_value.document.return_value = mock_doc

        with patch("archive_agents.tools.publisher_tools.get_firestore_client", return_value=mock_firestore_client):
            from archive_agents.tools.publisher_tools import publish_mystery

            sample_mystery_report_data["status"] = "published"
            mystery_json = json.dumps(sample_mystery_report_data)
            publish_mystery(mystery_json)

            assert "publishedAt" in captured_data

    def test_publish_mystery_invalid_json(self, mock_firestore_client):
        """publish_mystery should handle invalid JSON gracefully."""
        with patch("archive_agents.tools.publisher_tools.get_firestore_client", return_value=mock_firestore_client):
            from archive_agents.tools.publisher_tools import publish_mystery

            result = json.loads(publish_mystery("invalid json {"))

            assert result["status"] == "error"
            assert "error" in result


class TestUploadImages:
    """Tests for upload_images function."""

    def test_upload_images_success(self, mock_storage_bucket):
        """upload_images should successfully upload to Cloud Storage."""
        # Create a temporary test image
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
            f.write(b"fake png content")
            temp_path = f.name

        try:
            with patch("archive_agents.tools.publisher_tools.get_storage_bucket", return_value=mock_storage_bucket):
                from archive_agents.tools.publisher_tools import upload_images

                result = json.loads(upload_images(
                    "MYSTERY-1842-BOSTON-001",
                    json.dumps([temp_path])
                ))

                assert result["status"] == "success"
                assert result["mystery_id"] == "MYSTERY-1842-BOSTON-001"
                assert len(result["uploaded"]) == 1
                assert result["uploaded"][0]["status"] == "success"
                assert "public_url" in result["uploaded"][0]
        finally:
            os.unlink(temp_path)

    def test_upload_images_file_not_found(self, mock_storage_bucket):
        """upload_images should handle missing files gracefully."""
        with patch("archive_agents.tools.publisher_tools.get_storage_bucket", return_value=mock_storage_bucket):
            from archive_agents.tools.publisher_tools import upload_images

            result = json.loads(upload_images(
                "MYSTERY-TEST",
                json.dumps(["/nonexistent/path/image.png"])
            ))

            assert result["status"] == "success"
            assert len(result["uploaded"]) == 1
            assert result["uploaded"][0]["status"] == "error"
            assert "File not found" in result["uploaded"][0]["error"]

    def test_upload_images_emulator_url(self, mock_storage_bucket):
        """upload_images should construct emulator URL when emulator is running."""
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
            f.write(b"fake png content")
            temp_path = f.name

        try:
            mock_storage_bucket.name = "test-bucket"

            with patch("archive_agents.tools.publisher_tools.get_storage_bucket", return_value=mock_storage_bucket):
                with patch.dict(os.environ, {"STORAGE_EMULATOR_HOST": "http://localhost:9199"}):
                    from archive_agents.tools.publisher_tools import upload_images

                    # Need to reimport to pick up the patched environment
                    import importlib
                    import archive_agents.tools.publisher_tools as pt
                    importlib.reload(pt)

                    result = json.loads(pt.upload_images(
                        "MYSTERY-TEST",
                        json.dumps([temp_path])
                    ))

                    assert result["status"] == "success"
                    uploaded = result["uploaded"][0]
                    assert "localhost:9199" in uploaded["public_url"]
        finally:
            os.unlink(temp_path)

    def test_upload_images_string_path(self, mock_storage_bucket):
        """upload_images should handle single string path (not array)."""
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
            f.write(b"fake png content")
            temp_path = f.name

        try:
            with patch("archive_agents.tools.publisher_tools.get_storage_bucket", return_value=mock_storage_bucket):
                from archive_agents.tools.publisher_tools import upload_images

                # Pass string instead of array
                result = json.loads(upload_images(
                    "MYSTERY-TEST",
                    json.dumps(temp_path)
                ))

                assert result["status"] == "success"
                assert len(result["uploaded"]) == 1
        finally:
            os.unlink(temp_path)


@pytest.mark.integration
class TestPublisherToolsWithEmulator:
    """Integration tests requiring Firebase Emulator.

    Run these with: pytest -m integration
    """

    @pytest.fixture(autouse=True)
    def check_emulator(self):
        """Skip if emulator is not running."""
        if not os.environ.get("FIRESTORE_EMULATOR_HOST"):
            pytest.skip("Firebase Emulator not running (FIRESTORE_EMULATOR_HOST not set)")

    def test_publish_and_retrieve(self, sample_mystery_report_data):
        """Test full publish cycle with emulator."""
        from archive_agents.tools.publisher_tools import publish_mystery
        from shared.firestore import get_firestore_client

        # Publish
        mystery_json = json.dumps(sample_mystery_report_data)
        result = json.loads(publish_mystery(mystery_json))
        assert result["status"] == "success"

        # Retrieve
        db = get_firestore_client()
        doc = db.collection("mysteries").document(sample_mystery_report_data["mystery_id"]).get()
        assert doc.exists
        data = doc.to_dict()
        assert data["title"] == sample_mystery_report_data["title"]
