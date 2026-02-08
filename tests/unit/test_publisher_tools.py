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
