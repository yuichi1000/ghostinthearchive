"""Unit tests for Publisher tools."""

import json
import logging
from pathlib import Path
from unittest.mock import MagicMock, patch


from mystery_agents.tools.image_upload import (
    _cleanup_temp_images,
    _upload_images_internal,
    upload_images,
)
from mystery_agents.tools.publisher_tools import publish_mystery


class TestUploadImagesContentType:
    """Tests for upload_images content_type detection."""

    @patch("mystery_agents.tools.image_upload.get_storage_bucket")
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
        # Local file is renamed to mystery_id-based name before upload
        renamed_path = str(tmp_path / "TEST-001_sm.webp")
        mock_blob.upload_from_filename.assert_called_once_with(
            renamed_path, content_type="image/webp"
        )

    @patch("mystery_agents.tools.image_upload.get_storage_bucket")
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
        # Local file is renamed to mystery_id-based name before upload
        renamed_path = str(tmp_path / "TEST-001.png")
        mock_blob.upload_from_filename.assert_called_once_with(
            renamed_path, content_type="image/png"
        )


class TestUploadImagesRenaming:
    """Tests for upload_images mystery_id-based renaming."""

    @patch("mystery_agents.tools.image_upload.get_storage_bucket")
    def test_upload_renames_to_mystery_id(self, mock_get_bucket, tmp_path):
        """Should rename original image to {mystery_id}.png on upload."""
        mock_bucket = MagicMock()
        mock_blob = MagicMock()
        mock_bucket.blob.return_value = mock_blob
        mock_bucket.name = "test-bucket"
        mock_get_bucket.return_value = mock_bucket

        png_file = tmp_path / "header_20260208_120530.png"
        png_file.write_bytes(b"fake png data")

        mystery_id = "OCC-US-BOS-20260208143025"
        result = upload_images(mystery_id, json.dumps([str(png_file)]))
        result_data = json.loads(result)

        assert result_data["status"] == "success"
        expected_blob = f"images/{mystery_id}/{mystery_id}.png"
        mock_bucket.blob.assert_called_once_with(expected_blob)

    @patch("mystery_agents.tools.image_upload.get_storage_bucket")
    def test_upload_renames_variant_to_mystery_id(self, mock_get_bucket, tmp_path):
        """Should rename variant image to {mystery_id}_sm.webp on upload."""
        mock_bucket = MagicMock()
        mock_blob = MagicMock()
        mock_bucket.blob.return_value = mock_blob
        mock_bucket.name = "test-bucket"
        mock_get_bucket.return_value = mock_bucket

        webp_file = tmp_path / "header_20260208_120530_sm.webp"
        webp_file.write_bytes(b"fake webp data")

        mystery_id = "OCC-US-BOS-20260208143025"
        result = upload_images(mystery_id, json.dumps([str(webp_file)]))
        result_data = json.loads(result)

        assert result_data["status"] == "success"
        expected_blob = f"images/{mystery_id}/{mystery_id}_sm.webp"
        mock_bucket.blob.assert_called_once_with(expected_blob)

    @patch("mystery_agents.tools.image_upload.get_storage_bucket")
    def test_upload_preserves_extension(self, mock_get_bucket, tmp_path):
        """Should preserve original file extension when renaming."""
        mock_bucket = MagicMock()
        mock_blob = MagicMock()
        mock_bucket.blob.return_value = mock_blob
        mock_bucket.name = "test-bucket"
        mock_get_bucket.return_value = mock_bucket

        jpg_file = tmp_path / "photo_20260208.jpg"
        jpg_file.write_bytes(b"fake jpg data")

        mystery_id = "HIS-US-JFK-20260208143025"
        result = upload_images(mystery_id, json.dumps([str(jpg_file)]))
        result_data = json.loads(result)

        assert result_data["status"] == "success"
        expected_blob = f"images/{mystery_id}/{mystery_id}.jpg"
        mock_bucket.blob.assert_called_once_with(expected_blob)


class TestUploadImagesLabel:
    """Tests for upload_images label field."""

    @patch("mystery_agents.tools.image_upload.get_storage_bucket")
    def test_upload_returns_label_for_original(self, mock_get_bucket, tmp_path):
        """Should return label 'original' for the original image."""
        mock_bucket = MagicMock()
        mock_blob = MagicMock()
        mock_bucket.blob.return_value = mock_blob
        mock_bucket.name = "test-bucket"
        mock_get_bucket.return_value = mock_bucket

        png_file = tmp_path / "header_20260208.png"
        png_file.write_bytes(b"fake png data")

        result = upload_images("TEST-001", json.dumps([str(png_file)]))
        result_data = json.loads(result)

        assert result_data["status"] == "success"
        assert result_data["uploaded"][0]["label"] == "original"

    @patch("mystery_agents.tools.image_upload.get_storage_bucket")
    def test_upload_returns_label_for_variant(self, mock_get_bucket, tmp_path):
        """Should return label 'sm' for a _sm variant image."""
        mock_bucket = MagicMock()
        mock_blob = MagicMock()
        mock_bucket.blob.return_value = mock_blob
        mock_bucket.name = "test-bucket"
        mock_get_bucket.return_value = mock_bucket

        webp_file = tmp_path / "header_20260208_sm.webp"
        webp_file.write_bytes(b"fake webp data")

        result = upload_images("TEST-001", json.dumps([str(webp_file)]))
        result_data = json.loads(result)

        assert result_data["status"] == "success"
        assert result_data["uploaded"][0]["label"] == "sm"


class TestUploadImagesStructured:
    """Tests for upload_images structured images object."""

    @patch("mystery_agents.tools.image_upload.get_storage_bucket")
    def test_upload_returns_structured_images(self, mock_get_bucket, tmp_path):
        """Should return structured images object with hero and variants."""
        mock_bucket = MagicMock()
        mock_blob = MagicMock()
        mock_bucket.blob.return_value = mock_blob
        mock_bucket.name = "test-bucket"
        mock_get_bucket.return_value = mock_bucket

        # Create original + all 4 variants
        files = [
            tmp_path / "header.png",
            tmp_path / "header_sm.webp",
            tmp_path / "header_md.webp",
            tmp_path / "header_lg.webp",
            tmp_path / "header_xl.webp",
        ]
        for f in files:
            f.write_bytes(b"fake data")

        mystery_id = "OCC-US-BOS-20260208143025"
        result = upload_images(mystery_id, json.dumps([str(f) for f in files]))
        result_data = json.loads(result)

        assert result_data["status"] == "success"
        images = result_data["images"]
        assert "hero" in images
        assert "variants" in images
        assert "sm" in images["variants"]
        assert "md" in images["variants"]
        assert "lg" in images["variants"]
        assert "xl" in images["variants"]

    @patch("mystery_agents.tools.image_upload.get_storage_bucket")
    def test_upload_images_hero_prefers_lg(self, mock_get_bucket, tmp_path):
        """Should use lg variant URL as hero when lg variant exists."""
        mock_bucket = MagicMock()
        mock_blob = MagicMock()
        mock_bucket.blob.return_value = mock_blob
        mock_bucket.name = "test-bucket"
        mock_get_bucket.return_value = mock_bucket

        # Create original + lg variant
        original = tmp_path / "header.png"
        original.write_bytes(b"fake png")
        lg_variant = tmp_path / "header_lg.webp"
        lg_variant.write_bytes(b"fake lg webp")

        mystery_id = "OCC-US-BOS-20260208143025"
        result = upload_images(mystery_id, json.dumps([str(original), str(lg_variant)]))
        result_data = json.loads(result)

        images = result_data["images"]
        # hero should be the lg variant URL, not the original
        lg_url = next(
            e["public_url"] for e in result_data["uploaded"]
            if e["label"] == "lg"
        )
        assert images["hero"] == lg_url


# =============================================================================
# Helper: minimal mystery JSON for publish_mystery tests
# =============================================================================

def _make_mystery_json(**overrides):
    """Build a minimal valid mystery JSON string for testing."""
    data = {
        "classification": "OCC",
        "country_code": "US",
        "region_code": "BOS",
        "title": "Test Mystery",
        "summary": "A test mystery summary.",
        "discrepancy_detected": "Test discrepancy",
        "discrepancy_type": "event_outcome",
        "evidence_a": {"source_type": "newspaper", "source_language": "en",
                       "source_title": "Test", "source_date": "1842-01-01",
                       "source_url": "https://example.com", "relevant_excerpt": "...",
                       "location_context": "Boston"},
        "evidence_b": {"source_type": "newspaper", "source_language": "es",
                       "source_title": "Test ES", "source_date": "1842-02-01",
                       "source_url": "https://example.com/es", "relevant_excerpt": "...",
                       "location_context": "Havana"},
        "hypothesis": "Test hypothesis",
        "alternative_hypotheses": [],
        "confidence_level": "medium",
        "historical_context": {"time_period": "19th Century",
                               "geographic_scope": ["Boston"],
                               "relevant_events": [], "key_figures": [],
                               "political_climate": "Stable"},
        "research_questions": [],
        "story_hooks": [],
        "narrative_content": "# Test Story\nOnce upon a time...",
    }
    data.update(overrides)
    return json.dumps(data, ensure_ascii=False)


def _make_visual_assets_json(tmp_path):
    """Build a visual_assets JSON matching generate_image output, with real temp files."""
    original = tmp_path / "header_20260208_143025.png"
    original.write_bytes(b"fake png data")

    variants = []
    for label, width, height in [("sm", 640, 360), ("md", 828, 466),
                                  ("lg", 1200, 675), ("xl", 1920, 1080)]:
        vpath = tmp_path / f"header_20260208_143025_{label}.webp"
        vpath.write_bytes(b"fake webp data")
        variants.append({
            "label": label, "width": width, "height": height,
            "filepath": str(vpath),
            "filename": f"header_20260208_143025_{label}.webp",
        })

    return json.dumps({
        "status": "success",
        "filepath": str(original),
        "filename": "header_20260208_143025.png",
        "variants": variants,
    }, ensure_ascii=False)


class TestPublishMysteryImageUpload:
    """Tests for publish_mystery with visual_assets_json integration."""

    @patch("mystery_agents.tools.image_upload.get_storage_bucket")
    @patch("mystery_agents.tools.publisher_tools.get_firestore_client")
    def test_images_hero_set_to_lg_variant(
        self, mock_get_db, mock_get_bucket, tmp_path
    ):
        """Should set images.hero to lg variant WebP URL in Firestore data."""
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db

        mock_bucket = MagicMock()
        mock_blob = MagicMock()
        mock_bucket.blob.return_value = mock_blob
        mock_bucket.name = "test-bucket"
        mock_get_bucket.return_value = mock_bucket

        mystery_json = _make_mystery_json()
        visual_assets_json = _make_visual_assets_json(tmp_path)

        result = publish_mystery(mystery_json, visual_assets_json)
        result_data = json.loads(result)

        assert result_data["status"] == "success"

        # Retrieve saved data from Firestore mock
        saved_data = mock_db.collection.return_value.document.return_value.set.call_args[0][0]
        assert "images" in saved_data
        assert "hero" in saved_data["images"]
        # hero should contain the mystery_id and _lg.webp
        assert "_lg.webp" in saved_data["images"]["hero"]

    @patch("mystery_agents.tools.image_upload.get_storage_bucket")
    @patch("mystery_agents.tools.publisher_tools.get_firestore_client")
    def test_images_variants_contain_all_sizes(
        self, mock_get_db, mock_get_bucket, tmp_path
    ):
        """Should include sm/md/lg/xl in images.variants."""
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db

        mock_bucket = MagicMock()
        mock_blob = MagicMock()
        mock_bucket.blob.return_value = mock_blob
        mock_bucket.name = "test-bucket"
        mock_get_bucket.return_value = mock_bucket

        mystery_json = _make_mystery_json()
        visual_assets_json = _make_visual_assets_json(tmp_path)

        result = publish_mystery(mystery_json, visual_assets_json)
        result_data = json.loads(result)

        assert result_data["status"] == "success"

        saved_data = mock_db.collection.return_value.document.return_value.set.call_args[0][0]
        variants = saved_data["images"]["variants"]
        assert "sm" in variants
        assert "md" in variants
        assert "lg" in variants
        assert "xl" in variants

    @patch("mystery_agents.tools.image_upload.get_storage_bucket")
    @patch("mystery_agents.tools.publisher_tools.get_firestore_client")
    def test_skip_image_processing_when_empty(
        self, mock_get_db, mock_get_bucket
    ):
        """Should skip image processing when visual_assets_json is empty."""
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db

        mock_bucket = MagicMock()
        mock_get_bucket.return_value = mock_bucket

        mystery_json = _make_mystery_json()

        result = publish_mystery(mystery_json, "")
        result_data = json.loads(result)

        assert result_data["status"] == "success"
        # upload should not have been called
        mock_bucket.blob.assert_not_called()

        # images field should not be in saved data
        saved_data = mock_db.collection.return_value.document.return_value.set.call_args[0][0]
        assert "images" not in saved_data

    @patch("mystery_agents.tools.image_upload.get_storage_bucket")
    @patch("mystery_agents.tools.publisher_tools.get_firestore_client")
    def test_mystery_id_matches_between_images_and_firestore(
        self, mock_get_db, mock_get_bucket, tmp_path
    ):
        """Should use the same mystery_id for both image paths and Firestore document."""
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db

        mock_bucket = MagicMock()
        mock_blob = MagicMock()
        mock_bucket.blob.return_value = mock_blob
        mock_bucket.name = "test-bucket"
        mock_get_bucket.return_value = mock_bucket

        mystery_json = _make_mystery_json()
        visual_assets_json = _make_visual_assets_json(tmp_path)

        result = publish_mystery(mystery_json, visual_assets_json)
        result_data = json.loads(result)

        mystery_id = result_data["mystery_id"]

        # Check that Firestore document ID matches
        doc_call = mock_db.collection.return_value.document
        doc_call.assert_called_with(mystery_id)

        # Check that all blob paths start with the correct mystery_id
        for blob_call in mock_bucket.blob.call_args_list:
            blob_name = blob_call[0][0]
            assert blob_name.startswith(f"images/{mystery_id}/")


class TestLocalFileCleanup:
    """Tests for local file cleanup after upload."""

    @patch("mystery_agents.tools.image_upload.get_storage_bucket")
    def test_local_file_deleted_after_upload(self, mock_get_bucket, tmp_path):
        """Should delete local file after successful upload."""
        mock_bucket = MagicMock()
        mock_blob = MagicMock()
        mock_bucket.blob.return_value = mock_blob
        mock_bucket.name = "test-bucket"
        mock_get_bucket.return_value = mock_bucket

        png_file = tmp_path / "header_20260208_145745.png"
        png_file.write_bytes(b"fake png data")

        mystery_id = "OCC-US-BOS-20260208143025"
        upload_images(mystery_id, json.dumps([str(png_file)]))

        # Both original and renamed file should no longer exist
        assert not png_file.exists()
        renamed_file = tmp_path / f"{mystery_id}.png"
        assert not renamed_file.exists()

    @patch("mystery_agents.tools.image_upload.get_storage_bucket")
    def test_local_variant_deleted_after_upload(self, mock_get_bucket, tmp_path):
        """Should delete local variant file after successful upload."""
        mock_bucket = MagicMock()
        mock_blob = MagicMock()
        mock_bucket.blob.return_value = mock_blob
        mock_bucket.name = "test-bucket"
        mock_get_bucket.return_value = mock_bucket

        webp_file = tmp_path / "header_20260208_145745_sm.webp"
        webp_file.write_bytes(b"fake webp data")

        mystery_id = "OCC-US-BOS-20260208143025"
        upload_images(mystery_id, json.dumps([str(webp_file)]))

        # Both original and renamed file should no longer exist
        assert not webp_file.exists()
        renamed_file = tmp_path / f"{mystery_id}_sm.webp"
        assert not renamed_file.exists()

    @patch("mystery_agents.tools.image_upload.get_storage_bucket")
    @patch("mystery_agents.tools.publisher_tools.get_firestore_client")
    def test_local_files_cleaned_up_via_publish_mystery(
        self, mock_get_db, mock_get_bucket, tmp_path
    ):
        """Should clean up all local files after upload through publish_mystery."""
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db

        mock_bucket = MagicMock()
        mock_blob = MagicMock()
        mock_bucket.blob.return_value = mock_blob
        mock_bucket.name = "test-bucket"
        mock_get_bucket.return_value = mock_bucket

        mystery_json = _make_mystery_json()
        visual_assets_json = _make_visual_assets_json(tmp_path)

        result = publish_mystery(mystery_json, visual_assets_json)
        result_data = json.loads(result)
        mystery_id = result_data["mystery_id"]

        # Original timestamp-based files should be gone
        assert not (tmp_path / "header_20260208_143025.png").exists()
        assert not (tmp_path / "header_20260208_143025_sm.webp").exists()

        # Renamed files should also be cleaned up
        assert not (tmp_path / f"{mystery_id}.png").exists()
        assert not (tmp_path / f"{mystery_id}_sm.webp").exists()
        assert not (tmp_path / f"{mystery_id}_md.webp").exists()
        assert not (tmp_path / f"{mystery_id}_lg.webp").exists()
        assert not (tmp_path / f"{mystery_id}_xl.webp").exists()


class TestUploadErrorHandling:
    """Tests for _upload_images_internal error handling and logging."""

    @patch("mystery_agents.tools.image_upload.get_storage_bucket")
    @patch("mystery_agents.tools.publisher_tools.get_firestore_client")
    def test_publish_mystery_saves_to_firestore_when_image_upload_fails(
        self, mock_get_db, mock_get_bucket, tmp_path
    ):
        """Should save to Firestore even when image upload fails completely."""
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db

        mock_bucket = MagicMock()
        mock_blob = MagicMock()
        mock_blob.upload_from_filename.side_effect = Exception("Storage unavailable")
        mock_bucket.blob.return_value = mock_blob
        mock_bucket.name = "test-bucket"
        mock_get_bucket.return_value = mock_bucket

        mystery_json = _make_mystery_json()
        visual_assets_json = _make_visual_assets_json(tmp_path)

        result = publish_mystery(mystery_json, visual_assets_json)
        result_data = json.loads(result)

        assert result_data["status"] == "success"
        # Firestore set() should still have been called
        mock_db.collection.return_value.document.return_value.set.assert_called_once()
        # images should not be in saved data since all uploads failed
        saved_data = mock_db.collection.return_value.document.return_value.set.call_args[0][0]
        assert "images" not in saved_data

    @patch("mystery_agents.tools.image_upload.get_storage_bucket")
    def test_upload_images_internal_logs_on_failure(self, mock_get_bucket, tmp_path, caplog):
        """Should log an error when upload_from_filename fails."""

        mock_bucket = MagicMock()
        mock_blob = MagicMock()
        mock_blob.upload_from_filename.side_effect = Exception("Network error")
        mock_bucket.blob.return_value = mock_blob
        mock_bucket.name = "test-bucket"
        mock_get_bucket.return_value = mock_bucket

        png_file = tmp_path / "header.png"
        png_file.write_bytes(b"fake png data")

        with caplog.at_level(logging.ERROR, logger="mystery_agents.tools.publisher_tools"):
            _upload_images_internal("TEST-001", [str(png_file)])

        assert any("Network error" in record.message for record in caplog.records)

    @patch("mystery_agents.tools.image_upload.get_storage_bucket")
    def test_partial_upload_failure_does_not_block_others(self, mock_get_bucket, tmp_path):
        """When one file fails to upload, other files should still succeed."""

        mock_bucket = MagicMock()

        call_count = 0

        def upload_side_effect(path, content_type=None):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise Exception("First file fails")

        mock_blob_fail = MagicMock()
        mock_blob_fail.upload_from_filename.side_effect = upload_side_effect
        mock_blob_success = MagicMock()
        mock_blob_success.exists.return_value = True

        # First call returns failing blob, second returns successful
        mock_bucket.blob.side_effect = [mock_blob_fail, mock_blob_success]
        mock_bucket.name = "test-bucket"
        mock_get_bucket.return_value = mock_bucket

        file1 = tmp_path / "header.png"
        file1.write_bytes(b"fake png data")
        file2 = tmp_path / "header_sm.webp"
        file2.write_bytes(b"fake webp data")

        result = _upload_images_internal("TEST-001", [str(file1), str(file2)])

        # Second file should have been uploaded successfully
        assert result != {}


class TestCleanupTempImages:
    """Tests for _cleanup_temp_images helper."""

    def test_deletes_files(self, tmp_path):
        """Should delete all specified files."""
        f1 = tmp_path / "a.png"
        f2 = tmp_path / "b.webp"
        f1.write_bytes(b"data")
        f2.write_bytes(b"data")

        _cleanup_temp_images([f1, f2])

        assert not f1.exists()
        assert not f2.exists()

    def test_removes_empty_parent_directory(self, tmp_path):
        """Should remove parent directory when empty after file deletion."""
        subdir = tmp_path / "ghost_images_abc123"
        subdir.mkdir()
        f = subdir / "image.png"
        f.write_bytes(b"data")

        _cleanup_temp_images([f])

        assert not f.exists()
        assert not subdir.exists()

    def test_keeps_non_empty_parent_directory(self, tmp_path):
        """Should keep parent directory if other files remain."""
        subdir = tmp_path / "ghost_images_abc123"
        subdir.mkdir()
        f1 = subdir / "image.png"
        f2 = subdir / "other.txt"
        f1.write_bytes(b"data")
        f2.write_bytes(b"data")

        _cleanup_temp_images([f1])

        assert not f1.exists()
        assert subdir.exists()
        assert f2.exists()

    def test_ignores_missing_files(self, tmp_path):
        """Should not raise when files don't exist."""
        missing = tmp_path / "nonexistent.png"

        # Should not raise
        _cleanup_temp_images([missing])

    def test_logs_warning_on_delete_failure(self, tmp_path, caplog):
        """Should log warning when file deletion fails."""
        f = tmp_path / "image.png"
        f.write_bytes(b"data")

        with patch.object(Path, "unlink", side_effect=PermissionError("denied")):
            with caplog.at_level(logging.WARNING, logger="mystery_agents.tools.publisher_tools"):
                _cleanup_temp_images([f])

        assert "Failed to delete temp image" in caplog.text


class TestPublishMysterySchemaVersion:
    """Tests for schema_version field in publish_mystery()."""

    @patch("mystery_agents.tools.image_upload.get_storage_bucket")
    @patch("mystery_agents.tools.publisher_tools.get_firestore_client")
    def test_schema_version_set_to_2(self, mock_get_db, mock_get_bucket):
        """publish_mystery() は schema_version: 2 を設定する。"""
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        mock_bucket = MagicMock()
        mock_get_bucket.return_value = mock_bucket

        mystery_json = _make_mystery_json()

        result = publish_mystery(mystery_json, "")
        result_data = json.loads(result)

        assert result_data["status"] == "success"

        saved = mock_db.collection.return_value.document.return_value.set.call_args[0][0]
        assert saved["schema_version"] == 2


class TestPublishMysteryEvidenceFiltering:
    """Tests for evidence excerpt validation in publish_mystery()."""

    @patch("mystery_agents.tools.image_upload.get_storage_bucket")
    @patch("mystery_agents.tools.publisher_tools.get_firestore_client")
    def test_empty_excerpt_additional_evidence_filtered(
        self, mock_get_db, mock_get_bucket
    ):
        """additional_evidence の空 excerpt は除外される。"""
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        mock_bucket = MagicMock()
        mock_get_bucket.return_value = mock_bucket

        mystery_json = _make_mystery_json(
            additional_evidence=[
                {"source_url": "https://a.com", "relevant_excerpt": "Good"},
                {"source_url": "https://b.com", "relevant_excerpt": ""},
                {"source_url": "https://c.com", "relevant_excerpt": "Also good"},
            ]
        )

        result = publish_mystery(mystery_json, "")
        result_data = json.loads(result)
        assert result_data["status"] == "success"

        saved = mock_db.collection.return_value.document.return_value.set.call_args[0][0]
        assert len(saved["additional_evidence"]) == 2
        assert all(ev["relevant_excerpt"] for ev in saved["additional_evidence"])

    @patch("mystery_agents.tools.image_upload.get_storage_bucket")
    @patch("mystery_agents.tools.publisher_tools.get_firestore_client")
    def test_valid_additional_evidence_preserved(
        self, mock_get_db, mock_get_bucket
    ):
        """正常な additional_evidence はそのまま保持される。"""
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        mock_bucket = MagicMock()
        mock_get_bucket.return_value = mock_bucket

        mystery_json = _make_mystery_json(
            additional_evidence=[
                {"source_url": "https://a.com", "relevant_excerpt": "Excerpt 1"},
                {"source_url": "https://b.com", "relevant_excerpt": "Excerpt 2"},
            ]
        )

        result = publish_mystery(mystery_json, "")
        result_data = json.loads(result)
        assert result_data["status"] == "success"

        saved = mock_db.collection.return_value.document.return_value.set.call_args[0][0]
        assert len(saved["additional_evidence"]) == 2

    @patch("mystery_agents.tools.image_upload.get_storage_bucket")
    @patch("mystery_agents.tools.publisher_tools.get_firestore_client")
    def test_empty_excerpt_evidence_a_gets_fallback(
        self, mock_get_db, mock_get_bucket, caplog
    ):
        """evidence_a の excerpt が空 → フォールバック文が挿入されて保存される。"""
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        mock_bucket = MagicMock()
        mock_get_bucket.return_value = mock_bucket

        mystery_json = _make_mystery_json(
            evidence_a={
                "source_type": "newspaper",
                "source_language": "en",
                "source_title": "Test",
                "source_date": "1842-01-01",
                "source_url": "https://example.com",
                "relevant_excerpt": "",
                "location_context": "Boston",
            }
        )

        with caplog.at_level(logging.WARNING, logger="mystery_agents.tools.publisher_tools"):
            result = publish_mystery(mystery_json, "")

        result_data = json.loads(result)
        assert result_data["status"] == "success"

        saved = mock_db.collection.return_value.document.return_value.set.call_args[0][0]
        # フォールバック文が挿入されている
        assert saved["evidence_a"]["relevant_excerpt"] == "[See original source: Test]"
        # 警告ログが出力されている
        assert any("replaced with fallback" in r.message for r in caplog.records)


class TestPublishMysteryStateWriteback:
    """publish_mystery が tool_context.state に published_mystery_id を書き込むテスト"""

    @patch("mystery_agents.tools.image_upload.get_storage_bucket")
    @patch("mystery_agents.tools.publisher_tools.get_firestore_client")
    def test_sets_published_mystery_id_in_state(self, mock_get_db, mock_get_bucket):
        """成功時に tool_context.state["published_mystery_id"] が設定される。"""
        mock_get_db.return_value = MagicMock()
        mock_get_bucket.return_value = MagicMock()

        state = {}
        tool_context = MagicMock()
        tool_context.state = state

        result = publish_mystery(_make_mystery_json(), "", tool_context)
        result_data = json.loads(result)

        assert result_data["status"] == "success"
        assert "published_mystery_id" in state
        assert state["published_mystery_id"] == result_data["mystery_id"]
        # mystery_id 形式チェック
        assert state["published_mystery_id"].startswith("OCC-US-BOS-")

    @patch("mystery_agents.tools.image_upload.get_storage_bucket")
    @patch("mystery_agents.tools.publisher_tools.get_firestore_client")
    def test_no_state_write_without_tool_context(self, mock_get_db, mock_get_bucket):
        """tool_context が None の場合でもエラーにならない。"""
        mock_get_db.return_value = MagicMock()
        mock_get_bucket.return_value = MagicMock()

        result = publish_mystery(_make_mystery_json(), "", None)
        result_data = json.loads(result)

        assert result_data["status"] == "success"


class TestPublishMysteryStateDirectRead:
    """publish_mystery が creative_content / collected_documents_en を state から直接読み取るテスト"""

    @patch("mystery_agents.tools.image_upload.get_storage_bucket")
    @patch("mystery_agents.tools.publisher_tools.get_firestore_client")
    def test_narrative_content_from_state(self, mock_get_db, mock_get_bucket):
        """state の creative_content が narrative_content として保存される。"""
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        mock_get_bucket.return_value = MagicMock()

        state = {"creative_content": "# The Haunting of Salem\n\nA long blog article..."}
        tool_context = MagicMock()
        tool_context.state = state

        result = publish_mystery(_make_mystery_json(), "", tool_context)
        assert json.loads(result)["status"] == "success"

        saved = mock_db.collection.return_value.document.return_value.set.call_args[0][0]
        assert saved["narrative_content"] == "# The Haunting of Salem\n\nA long blog article..."

    @patch("mystery_agents.tools.image_upload.get_storage_bucket")
    @patch("mystery_agents.tools.publisher_tools.get_firestore_client")
    def test_raw_data_from_state(self, mock_get_db, mock_get_bucket):
        """state の collected_documents_en が raw_data として保存される。"""
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        mock_get_bucket.return_value = MagicMock()

        state = {"collected_documents_en": "Search results from LOC and DPLA..."}
        tool_context = MagicMock()
        tool_context.state = state

        result = publish_mystery(_make_mystery_json(), "", tool_context)
        assert json.loads(result)["status"] == "success"

        saved = mock_db.collection.return_value.document.return_value.set.call_args[0][0]
        assert saved["raw_data"] == "Search results from LOC and DPLA..."

    @patch("mystery_agents.tools.image_upload.get_storage_bucket")
    @patch("mystery_agents.tools.publisher_tools.get_firestore_client")
    def test_state_overrides_llm_json(self, mock_get_db, mock_get_bucket):
        """state 値が mystery_json の値より優先される。"""
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        mock_get_bucket.return_value = MagicMock()

        state = {
            "creative_content": "Full article from state",
            "collected_documents_en": "Full raw data from state",
        }
        tool_context = MagicMock()
        tool_context.state = state

        # mystery_json にも narrative_content と raw_data を含める
        mystery_json = _make_mystery_json(
            narrative_content="Truncated by LLM",
            raw_data="Truncated raw data",
        )
        result = publish_mystery(mystery_json, "", tool_context)
        assert json.loads(result)["status"] == "success"

        saved = mock_db.collection.return_value.document.return_value.set.call_args[0][0]
        assert saved["narrative_content"] == "Full article from state"
        assert saved["raw_data"] == "Full raw data from state"

    @patch("mystery_agents.tools.image_upload.get_storage_bucket")
    @patch("mystery_agents.tools.publisher_tools.get_firestore_client")
    def test_skips_failure_marker(self, mock_get_db, mock_get_bucket):
        """NO_CONTENT の creative_content は state から注入しない。"""
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        mock_get_bucket.return_value = MagicMock()

        state = {"creative_content": "NO_CONTENT: Pipeline failed at Storyteller"}
        tool_context = MagicMock()
        tool_context.state = state

        # mystery_json の narrative_content がフォールバックとして残る
        mystery_json = _make_mystery_json(narrative_content="LLM fallback content")
        result = publish_mystery(mystery_json, "", tool_context)
        assert json.loads(result)["status"] == "success"

        saved = mock_db.collection.return_value.document.return_value.set.call_args[0][0]
        assert saved["narrative_content"] == "LLM fallback content"

    @patch("mystery_agents.tools.image_upload.get_storage_bucket")
    @patch("mystery_agents.tools.publisher_tools.get_firestore_client")
    def test_empty_json_with_full_state(self, mock_get_db, mock_get_bucket):
        """空 JSON + structured_report + state で全フィールドが揃う。"""
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        mock_get_bucket.return_value = MagicMock()

        state = {
            "structured_report": {
                "classification": "FLK",
                "country_code": "US",
                "region_code": "MSY",
                "title": "Voodoo Queen",
                "summary": "A mystery about voodoo.",
                "discrepancy_detected": "Date mismatch",
                "discrepancy_type": "date_mismatch",
                "evidence_a": {"source_type": "newspaper", "source_language": "en",
                               "source_title": "Times", "source_date": "1850-01-01",
                               "source_url": "https://example.com", "relevant_excerpt": "...",
                               "location_context": "New Orleans"},
                "evidence_b": {"source_type": "newspaper", "source_language": "fr",
                               "source_title": "Le Monde", "source_date": "1850-06-01",
                               "source_url": "https://example.fr", "relevant_excerpt": "...",
                               "location_context": "Paris"},
                "hypothesis": "Test hypothesis",
                "alternative_hypotheses": [],
                "confidence_level": "medium",
                "historical_context": {"time_period": "19th Century",
                                       "geographic_scope": ["New Orleans"],
                                       "relevant_events": [], "key_figures": [],
                                       "political_climate": "Antebellum"},
                "research_questions": [],
                "story_hooks": [],
            },
            "creative_content": "# Voodoo Queen\n\nThe full blog article...",
            "collected_documents_en": "LOC search results...",
        }
        tool_context = MagicMock()
        tool_context.state = state

        # 最小限の JSON（classification/country_code/region_code のみ）
        minimal_json = json.dumps({
            "classification": "FLK", "country_code": "US", "region_code": "MSY",
        })
        result = publish_mystery(minimal_json, "", tool_context)
        result_data = json.loads(result)
        assert result_data["status"] == "success"
        assert result_data["mystery_id"].startswith("FLK-US-MSY-")

        saved = mock_db.collection.return_value.document.return_value.set.call_args[0][0]
        assert saved["title"] == "Voodoo Queen"
        assert saved["narrative_content"] == "# Voodoo Queen\n\nThe full blog article..."
        assert saved["raw_data"] == "LOC search results..."
        assert saved["hypothesis"] == "Test hypothesis"

    @patch("mystery_agents.tools.image_upload.get_storage_bucket")
    @patch("mystery_agents.tools.publisher_tools.get_firestore_client")
    def test_no_tool_context_fallback(self, mock_get_db, mock_get_bucket):
        """tool_context=None では LLM の mystery_json がそのまま使われる。"""
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        mock_get_bucket.return_value = MagicMock()

        mystery_json = _make_mystery_json(
            narrative_content="LLM provided content",
            raw_data="LLM provided raw data",
        )
        result = publish_mystery(mystery_json, "", None)
        assert json.loads(result)["status"] == "success"

        saved = mock_db.collection.return_value.document.return_value.set.call_args[0][0]
        assert saved["narrative_content"] == "LLM provided content"
        assert saved["raw_data"] == "LLM provided raw data"

    @patch("mystery_agents.tools.image_upload.get_storage_bucket")
    @patch("mystery_agents.tools.publisher_tools.get_firestore_client")
    def test_mystery_report_saved_to_firestore(self, mock_get_db, mock_get_bucket):
        """state の mystery_report が Firestore に保存される。"""
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        mock_get_bucket.return_value = MagicMock()

        report_text = "# Integrated Analysis Report\n\nA very long Polymath report..."
        state = {"mystery_report": report_text}
        tool_context = MagicMock()
        tool_context.state = state

        result = publish_mystery(_make_mystery_json(), "", tool_context)
        assert json.loads(result)["status"] == "success"

        saved = mock_db.collection.return_value.document.return_value.set.call_args[0][0]
        assert saved["mystery_report"] == report_text

    @patch("mystery_agents.tools.image_upload.get_storage_bucket")
    @patch("mystery_agents.tools.publisher_tools.get_firestore_client")
    def test_mystery_report_skips_insufficient_data(self, mock_get_db, mock_get_bucket):
        """INSUFFICIENT_DATA の mystery_report は保存しない。"""
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        mock_get_bucket.return_value = MagicMock()

        state = {"mystery_report": "INSUFFICIENT_DATA: No scholars produced analysis"}
        tool_context = MagicMock()
        tool_context.state = state

        result = publish_mystery(_make_mystery_json(), "", tool_context)
        assert json.loads(result)["status"] == "success"

        saved = mock_db.collection.return_value.document.return_value.set.call_args[0][0]
        assert "mystery_report" not in saved


class TestThumbnailUpload:
    """サムネイルアップロードのテスト。"""

    @patch("mystery_agents.tools.image_upload.get_storage_bucket")
    def test_thumb_suffix_stored_as_thumbnail(self, mock_get_bucket, tmp_path):
        """_thumb サフィックスが images["thumbnail"] に格納される。"""
        mock_bucket = MagicMock()
        mock_blob = MagicMock()
        mock_bucket.blob.return_value = mock_blob
        mock_bucket.name = "test-bucket"
        mock_get_bucket.return_value = mock_bucket

        thumb_file = tmp_path / "header_thumb.webp"
        thumb_file.write_bytes(b"fake thumb data")

        result = upload_images("TEST-001", json.dumps([str(thumb_file)]))
        result_data = json.loads(result)

        assert result_data["status"] == "success"
        assert "thumbnail" in result_data["images"]
        assert result_data["images"]["thumbnail"].endswith("alt=media")

    @patch("mystery_agents.tools.image_upload.get_storage_bucket")
    def test_thumb_and_variants_together(self, mock_get_bucket, tmp_path):
        """サムネイルとバリアントが同時にアップロードされる。"""
        mock_bucket = MagicMock()
        mock_blob = MagicMock()
        mock_bucket.blob.return_value = mock_blob
        mock_bucket.name = "test-bucket"
        mock_get_bucket.return_value = mock_bucket

        # メイン画像 + サムネイル + sm バリアント
        for name in ("header.png", "header_thumb.webp", "header_sm.webp"):
            f = tmp_path / name
            f.write_bytes(b"fake data")

        paths = [str(tmp_path / n) for n in ("header.png", "header_thumb.webp", "header_sm.webp")]
        result = upload_images("TEST-001", json.dumps(paths))
        result_data = json.loads(result)

        assert result_data["status"] == "success"
        assert "thumbnail" in result_data["images"]
        assert "hero" in result_data["images"]

    @patch("mystery_agents.tools.image_upload.get_storage_bucket")
    def test_internal_upload_thumb_suffix(self, mock_get_bucket, tmp_path):
        """_upload_images_internal が _thumb を images["thumbnail"] に格納する。"""
        mock_bucket = MagicMock()
        mock_blob = MagicMock()
        mock_bucket.blob.return_value = mock_blob
        mock_bucket.name = "test-bucket"
        mock_get_bucket.return_value = mock_bucket

        thumb_file = tmp_path / "header_thumb.webp"
        thumb_file.write_bytes(b"fake thumb data")

        images = _upload_images_internal("TEST-001", [str(thumb_file)])

        assert "thumbnail" in images
        assert "hero" not in images  # サムネイルだけなら hero は設定されない


class TestPublishMysteryStructuredDataExtension:
    """source_coverage / confidence_rationale の Firestore 保存テスト。"""

    @patch("mystery_agents.tools.image_upload.get_storage_bucket")
    @patch("mystery_agents.tools.publisher_tools.get_firestore_client")
    def test_source_coverage_from_structured_report(self, mock_get_db, mock_get_bucket):
        """structured_report の source_coverage が Firestore に保存される。"""
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        mock_get_bucket.return_value = MagicMock()

        state = {
            "structured_report": {
                "classification": "OCC",
                "country_code": "US",
                "region_code": "BOS",
                "title": "Test",
                "summary": "Test summary",
                "source_coverage": {
                    "apis_searched": ["chronicling_america", "loc"],
                    "apis_with_results": ["chronicling_america"],
                    "apis_without_results": ["loc"],
                    "known_undigitized_sources": ["Parish registers"],
                    "coverage_assessment": "Limited coverage",
                },
            }
        }
        tool_context = MagicMock()
        tool_context.state = state

        result = publish_mystery(_make_mystery_json(), "", tool_context)
        assert json.loads(result)["status"] == "success"

        saved = mock_db.collection.return_value.document.return_value.set.call_args[0][0]
        assert "source_coverage" in saved
        assert saved["source_coverage"]["apis_searched"] == ["chronicling_america", "loc"]
        assert saved["source_coverage"]["coverage_assessment"] == "Limited coverage"

    @patch("mystery_agents.tools.image_upload.get_storage_bucket")
    @patch("mystery_agents.tools.publisher_tools.get_firestore_client")
    def test_confidence_rationale_from_structured_report(self, mock_get_db, mock_get_bucket):
        """structured_report の confidence_rationale が Firestore に保存される。"""
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        mock_get_bucket.return_value = MagicMock()

        state = {
            "structured_report": {
                "classification": "HIS",
                "country_code": "GB",
                "region_code": "LHR",
                "title": "Test",
                "summary": "Test summary",
                "confidence_rationale": "Rated MEDIUM because two sources conflict but DPLA was unavailable.",
            }
        }
        tool_context = MagicMock()
        tool_context.state = state

        result = publish_mystery(_make_mystery_json(), "", tool_context)
        assert json.loads(result)["status"] == "success"

        saved = mock_db.collection.return_value.document.return_value.set.call_args[0][0]
        assert saved["confidence_rationale"] == "Rated MEDIUM because two sources conflict but DPLA was unavailable."

    @patch("mystery_agents.tools.image_upload.get_storage_bucket")
    @patch("mystery_agents.tools.publisher_tools.get_firestore_client")
    def test_missing_new_fields_does_not_break(self, mock_get_db, mock_get_bucket):
        """source_coverage / confidence_rationale がなくても後方互換で動作する。"""
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        mock_get_bucket.return_value = MagicMock()

        state = {
            "structured_report": {
                "classification": "OCC",
                "country_code": "US",
                "region_code": "BOS",
                "title": "Legacy Report",
                "summary": "No new fields",
            }
        }
        tool_context = MagicMock()
        tool_context.state = state

        result = publish_mystery(_make_mystery_json(), "", tool_context)
        assert json.loads(result)["status"] == "success"

        saved = mock_db.collection.return_value.document.return_value.set.call_args[0][0]
        # source_coverage は raw_search_results もないため設定されない
        assert "source_coverage" not in saved
        assert "confidence_rationale" not in saved


class TestPublishMysteryStorytellerMetadata:
    """storyteller_llm_metadata の Firestore 保存テスト。"""

    @patch("mystery_agents.tools.image_upload.get_storage_bucket")
    @patch("mystery_agents.tools.publisher_tools.get_firestore_client")
    def test_saves_storyteller_llm_metadata(self, mock_get_db, mock_get_bucket):
        """state の storyteller_llm_metadata が Firestore に保存される。"""
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        mock_get_bucket.return_value = MagicMock()

        llm_meta = {
            "storyteller": "claude",
            "display_name": "Claude Sonnet 4.5",
            "model_id": "claude-sonnet-4-5-20250929",
            "actual_model": "claude-sonnet-4-5-20250929",
            "prompt_tokens": 8000,
            "output_tokens": 3000,
        }
        state = {"storyteller_llm_metadata": llm_meta}
        tool_context = MagicMock()
        tool_context.state = state

        result = publish_mystery(_make_mystery_json(), "", tool_context)
        assert json.loads(result)["status"] == "success"

        saved = mock_db.collection.return_value.document.return_value.set.call_args[0][0]
        assert saved["storyteller_llm_metadata"] == llm_meta

    @patch("mystery_agents.tools.image_upload.get_storage_bucket")
    @patch("mystery_agents.tools.publisher_tools.get_firestore_client")
    def test_no_metadata_when_absent(self, mock_get_db, mock_get_bucket):
        """storyteller_llm_metadata がない場合はフィールドが設定されない。"""
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        mock_get_bucket.return_value = MagicMock()

        state = {}
        tool_context = MagicMock()
        tool_context.state = state

        result = publish_mystery(_make_mystery_json(), "", tool_context)
        assert json.loads(result)["status"] == "success"

        saved = mock_db.collection.return_value.document.return_value.set.call_args[0][0]
        assert "storyteller_llm_metadata" not in saved

    @patch("mystery_agents.tools.image_upload.get_storage_bucket")
    @patch("mystery_agents.tools.publisher_tools.get_firestore_client")
    def test_ignores_non_dict_metadata(self, mock_get_db, mock_get_bucket):
        """storyteller_llm_metadata が dict でない場合は無視される。"""
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        mock_get_bucket.return_value = MagicMock()

        state = {"storyteller_llm_metadata": "not a dict"}
        tool_context = MagicMock()
        tool_context.state = state

        result = publish_mystery(_make_mystery_json(), "", tool_context)
        assert json.loads(result)["status"] == "success"

        saved = mock_db.collection.return_value.document.return_value.set.call_args[0][0]
        assert "storyteller_llm_metadata" not in saved


class TestSourceCoverageProgrammaticOverwrite:
    """source_coverage の API フィールドが raw_search_results から programmatic に上書きされるテスト。"""

    @patch("mystery_agents.tools.image_upload.get_storage_bucket")
    @patch("mystery_agents.tools.publisher_tools.get_firestore_client")
    def test_overwrites_apis_from_raw_search_results(self, mock_get_db, mock_get_bucket):
        """raw_search_results がある場合、source_coverage の API フィールドが上書きされる。"""
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        mock_get_bucket.return_value = MagicMock()

        state = {
            "structured_report": {
                "classification": "OCC",
                "country_code": "US",
                "region_code": "BOS",
                "title": "Test",
                "summary": "Test summary",
                "source_coverage": {
                    "apis_searched": ["llm_hallucinated_api"],
                    "apis_with_results": ["llm_hallucinated_api"],
                    "apis_without_results": [],
                    "known_undigitized_sources": ["Parish registers"],
                    "coverage_assessment": "Limited coverage",
                },
            },
            # raw_search_results から正確なメタデータが生成される
            "raw_search_results_en": [
                {"source": "chronicling_america", "total_hits": 50, "documents_returned": 10},
                {"source": "loc_digital", "total_hits": 0, "documents_returned": 0},
            ],
        }
        tool_context = MagicMock()
        tool_context.state = state

        result = publish_mystery(_make_mystery_json(), "", tool_context)
        assert json.loads(result)["status"] == "success"

        saved = mock_db.collection.return_value.document.return_value.set.call_args[0][0]
        sc = saved["source_coverage"]
        # API フィールドは raw_search_results から上書きされている
        assert "chronicling_america" in sc["apis_searched"]
        assert "loc_digital" in sc["apis_searched"]
        assert "llm_hallucinated_api" not in sc["apis_searched"]
        assert sc["apis_with_results"] == ["chronicling_america"]
        assert sc["apis_without_results"] == ["loc_digital"]
        # LLM が生成した人間的判断フィールドは保持される
        assert sc["known_undigitized_sources"] == ["Parish registers"]
        assert sc["coverage_assessment"] == "Limited coverage"

    @patch("mystery_agents.tools.image_upload.get_storage_bucket")
    @patch("mystery_agents.tools.publisher_tools.get_firestore_client")
    def test_creates_source_coverage_when_missing(self, mock_get_db, mock_get_bucket):
        """structured_report に source_coverage がなくても raw_search_results から生成される。"""
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        mock_get_bucket.return_value = MagicMock()

        state = {
            "structured_report": {
                "classification": "HIS",
                "country_code": "GB",
                "region_code": "LHR",
                "title": "Test",
                "summary": "Test summary",
                # source_coverage なし
            },
            "raw_search_results_en": [
                {"source": "europeana", "total_hits": 20, "documents_returned": 5},
            ],
        }
        tool_context = MagicMock()
        tool_context.state = state

        result = publish_mystery(_make_mystery_json(), "", tool_context)
        assert json.loads(result)["status"] == "success"

        saved = mock_db.collection.return_value.document.return_value.set.call_args[0][0]
        sc = saved["source_coverage"]
        assert sc["apis_searched"] == ["europeana"]
        assert sc["apis_with_results"] == ["europeana"]
        assert sc["apis_without_results"] == []

    @patch("mystery_agents.tools.image_upload.get_storage_bucket")
    @patch("mystery_agents.tools.publisher_tools.get_firestore_client")
    def test_no_overwrite_without_raw_search_results(self, mock_get_db, mock_get_bucket):
        """raw_search_results がない場合、LLM 生成の source_coverage がそのまま使われる。"""
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        mock_get_bucket.return_value = MagicMock()

        state = {
            "structured_report": {
                "classification": "OCC",
                "country_code": "US",
                "region_code": "BOS",
                "title": "Test",
                "summary": "Test summary",
                "source_coverage": {
                    "apis_searched": ["chronicling_america"],
                    "apis_with_results": ["chronicling_america"],
                    "apis_without_results": [],
                },
            },
            # raw_search_results なし
        }
        tool_context = MagicMock()
        tool_context.state = state

        result = publish_mystery(_make_mystery_json(), "", tool_context)
        assert json.loads(result)["status"] == "success"

        saved = mock_db.collection.return_value.document.return_value.set.call_args[0][0]
        sc = saved["source_coverage"]
        # LLM 生成値がそのまま残る
        assert sc["apis_searched"] == ["chronicling_america"]

    @patch("mystery_agents.tools.image_upload.get_storage_bucket")
    @patch("mystery_agents.tools.publisher_tools.get_firestore_client")
    def test_api_errors_saved_to_source_coverage(self, mock_get_db, mock_get_bucket):
        """API エラーがある場合、source_coverage.api_errors に保存される。"""
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        mock_get_bucket.return_value = MagicMock()

        state = {
            "structured_report": {
                "classification": "OCC",
                "country_code": "US",
                "region_code": "BOS",
                "title": "Test",
                "summary": "Test summary",
                "source_coverage": {
                    "apis_searched": ["llm_value"],
                    "apis_with_results": [],
                    "apis_without_results": ["llm_value"],
                    "coverage_assessment": "Limited coverage",
                },
            },
            "raw_search_results_en": [
                {"source": "chronicling_america", "total_hits": 0, "documents_returned": 0,
                 "error": "Chronicling America API error: 503 Server Error"},
                {"source": "europeana", "total_hits": 10, "documents_returned": 5},
            ],
        }
        tool_context = MagicMock()
        tool_context.state = state

        result = publish_mystery(_make_mystery_json(), "", tool_context)
        assert json.loads(result)["status"] == "success"

        saved = mock_db.collection.return_value.document.return_value.set.call_args[0][0]
        sc = saved["source_coverage"]
        assert "api_errors" in sc
        assert "chronicling_america" in sc["api_errors"]
        assert "503" in sc["api_errors"]["chronicling_america"]
        # エラーのない europeana は api_errors に含まれない
        assert "europeana" not in sc["api_errors"]

    @patch("mystery_agents.tools.image_upload.get_storage_bucket")
    @patch("mystery_agents.tools.publisher_tools.get_firestore_client")
    def test_no_api_errors_field_when_no_errors(self, mock_get_db, mock_get_bucket):
        """API エラーがない場合、api_errors フィールドは存在しない。"""
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        mock_get_bucket.return_value = MagicMock()

        state = {
            "structured_report": {
                "classification": "OCC",
                "country_code": "US",
                "region_code": "BOS",
                "title": "Test",
                "summary": "Test summary",
            },
            "raw_search_results_en": [
                {"source": "europeana", "total_hits": 20, "documents_returned": 5},
                {"source": "loc_digital", "total_hits": 0, "documents_returned": 0},
            ],
        }
        tool_context = MagicMock()
        tool_context.state = state

        result = publish_mystery(_make_mystery_json(), "", tool_context)
        assert json.loads(result)["status"] == "success"

        saved = mock_db.collection.return_value.document.return_value.set.call_args[0][0]
        sc = saved["source_coverage"]
        assert "api_errors" not in sc


class TestPublishMysterySearchLog:
    """search_log の Firestore 永続化テスト。"""

    @patch("mystery_agents.tools.image_upload.get_storage_bucket")
    @patch("mystery_agents.tools.publisher_tools.get_firestore_client")
    def test_search_log_persisted_to_firestore(self, mock_get_db, mock_get_bucket):
        """state の search_log が Firestore ドキュメントに含まれる。"""
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        mock_get_bucket.return_value = MagicMock()

        search_log = [
            {
                "timestamp": "2026-02-28T12:00:00",
                "tool": "search_archives",
                "reference_keywords": ["Bell", "Tennessee"],
                "exploratory_keywords": ["poltergeist", "haunting"],
                "language": "en",
                "sources_searched": {"loc": {"total_hits": 15, "documents_returned": 8}},
                "total_documents": 8,
                "link_validation": {"total_checked": 8, "reachable": 7, "unreachable": 1, "removed_count": 1},
                "fallback_used": False,
            },
            {
                "timestamp": "2026-02-28T12:00:05",
                "tool": "search_newspapers",
                "reference_keywords": ["Bell"],
                "exploratory_keywords": ["ghost"],
                "language": "en",
                "sources_searched": {"chronicling_america": {"total_hits": 3, "documents_returned": 3}},
                "total_documents": 3,
                "link_validation": {"total_checked": 3, "reachable": 3, "unreachable": 0, "removed_count": 0},
                "fallback_used": False,
            },
        ]
        state = {"search_log": search_log}
        tool_context = MagicMock()
        tool_context.state = state

        result = publish_mystery(_make_mystery_json(), "", tool_context)
        assert json.loads(result)["status"] == "success"

        saved = mock_db.collection.return_value.document.return_value.set.call_args[0][0]
        assert "search_log" in saved
        assert len(saved["search_log"]) == 2
        assert saved["search_log"][0]["tool"] == "search_archives"
        assert saved["search_log"][0]["reference_keywords"] == ["Bell", "Tennessee"]
        assert saved["search_log"][1]["tool"] == "search_newspapers"

    @patch("mystery_agents.tools.image_upload.get_storage_bucket")
    @patch("mystery_agents.tools.publisher_tools.get_firestore_client")
    def test_no_search_log_when_absent(self, mock_get_db, mock_get_bucket):
        """search_log がない場合はフィールドが設定されない。"""
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        mock_get_bucket.return_value = MagicMock()

        state = {}
        tool_context = MagicMock()
        tool_context.state = state

        result = publish_mystery(_make_mystery_json(), "", tool_context)
        assert json.loads(result)["status"] == "success"

        saved = mock_db.collection.return_value.document.return_value.set.call_args[0][0]
        assert "search_log" not in saved

