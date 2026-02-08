"""Unit tests for Publisher tools."""

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from archive_agents.tools.publisher_tools import upload_images


class TestUploadImagesContentType:
    """Tests for upload_images content_type detection."""

    @patch("archive_agents.tools.publisher_tools.get_storage_bucket")
    def test_webp_content_type(self, mock_get_bucket, tmp_path):
        """Should set content_type to image/webp for .webp files."""
        mock_bucket = MagicMock()
        mock_blob = MagicMock()
        mock_bucket.blob.return_value = mock_blob
        mock_bucket.name = "test-bucket"
        mock_get_bucket.return_value = mock_bucket

        webp_file = tmp_path / "header_sm.webp"
        webp_file.write_bytes(b"fake webp data")

        result = upload_images("TEST-001", json.dumps([str(webp_file)]))
        result_data = json.loads(result)

        assert result_data["status"] == "success"
        mock_blob.upload_from_filename.assert_called_once_with(
            str(webp_file), content_type="image/webp"
        )

    @patch("archive_agents.tools.publisher_tools.get_storage_bucket")
    def test_png_content_type(self, mock_get_bucket, tmp_path):
        """Should set content_type to image/png for .png files."""
        mock_bucket = MagicMock()
        mock_blob = MagicMock()
        mock_bucket.blob.return_value = mock_blob
        mock_bucket.name = "test-bucket"
        mock_get_bucket.return_value = mock_bucket

        png_file = tmp_path / "header.png"
        png_file.write_bytes(b"fake png data")

        result = upload_images("TEST-001", json.dumps([str(png_file)]))
        result_data = json.loads(result)

        assert result_data["status"] == "success"
        mock_blob.upload_from_filename.assert_called_once_with(
            str(png_file), content_type="image/png"
        )


class TestUploadImagesRenaming:
    """Tests for upload_images mystery_id-based renaming."""

    @patch("archive_agents.tools.publisher_tools.get_storage_bucket")
    def test_upload_renames_to_mystery_id(self, mock_get_bucket, tmp_path):
        """Should rename original image to {mystery_id}.png on upload."""
        mock_bucket = MagicMock()
        mock_blob = MagicMock()
        mock_bucket.blob.return_value = mock_blob
        mock_bucket.name = "test-bucket"
        mock_get_bucket.return_value = mock_bucket

        png_file = tmp_path / "header_20260208_120530.png"
        png_file.write_bytes(b"fake png data")

        mystery_id = "OCC-MA-617-20260208143025"
        result = upload_images(mystery_id, json.dumps([str(png_file)]))
        result_data = json.loads(result)

        assert result_data["status"] == "success"
        expected_blob = f"images/{mystery_id}/{mystery_id}.png"
        mock_bucket.blob.assert_called_once_with(expected_blob)

    @patch("archive_agents.tools.publisher_tools.get_storage_bucket")
    def test_upload_renames_variant_to_mystery_id(self, mock_get_bucket, tmp_path):
        """Should rename variant image to {mystery_id}_sm.webp on upload."""
        mock_bucket = MagicMock()
        mock_blob = MagicMock()
        mock_bucket.blob.return_value = mock_blob
        mock_bucket.name = "test-bucket"
        mock_get_bucket.return_value = mock_bucket

        webp_file = tmp_path / "header_20260208_120530_sm.webp"
        webp_file.write_bytes(b"fake webp data")

        mystery_id = "OCC-MA-617-20260208143025"
        result = upload_images(mystery_id, json.dumps([str(webp_file)]))
        result_data = json.loads(result)

        assert result_data["status"] == "success"
        expected_blob = f"images/{mystery_id}/{mystery_id}_sm.webp"
        mock_bucket.blob.assert_called_once_with(expected_blob)

    @patch("archive_agents.tools.publisher_tools.get_storage_bucket")
    def test_upload_preserves_extension(self, mock_get_bucket, tmp_path):
        """Should preserve original file extension when renaming."""
        mock_bucket = MagicMock()
        mock_blob = MagicMock()
        mock_bucket.blob.return_value = mock_blob
        mock_bucket.name = "test-bucket"
        mock_get_bucket.return_value = mock_bucket

        jpg_file = tmp_path / "photo_20260208.jpg"
        jpg_file.write_bytes(b"fake jpg data")

        mystery_id = "HIS-NY-212-20260208143025"
        result = upload_images(mystery_id, json.dumps([str(jpg_file)]))
        result_data = json.loads(result)

        assert result_data["status"] == "success"
        expected_blob = f"images/{mystery_id}/{mystery_id}.jpg"
        mock_bucket.blob.assert_called_once_with(expected_blob)
