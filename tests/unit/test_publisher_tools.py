"""Unit tests for Publisher tools."""

import json
import logging
from pathlib import Path
from unittest.mock import MagicMock, call, patch

import pytest

from archive_agents.tools.publisher_tools import publish_mystery, upload_images


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
        # Local file is renamed to mystery_id-based name before upload
        renamed_path = str(tmp_path / "TEST-001_sm.webp")
        mock_blob.upload_from_filename.assert_called_once_with(
            renamed_path, content_type="image/webp"
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
        # Local file is renamed to mystery_id-based name before upload
        renamed_path = str(tmp_path / "TEST-001.png")
        mock_blob.upload_from_filename.assert_called_once_with(
            renamed_path, content_type="image/png"
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


class TestUploadImagesLabel:
    """Tests for upload_images label field."""

    @patch("archive_agents.tools.publisher_tools.get_storage_bucket")
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

    @patch("archive_agents.tools.publisher_tools.get_storage_bucket")
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

    @patch("archive_agents.tools.publisher_tools.get_storage_bucket")
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

        mystery_id = "OCC-MA-617-20260208143025"
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

    @patch("archive_agents.tools.publisher_tools.get_storage_bucket")
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

        mystery_id = "OCC-MA-617-20260208143025"
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
        "state_code": "MA",
        "area_code": "617",
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

    @patch("archive_agents.tools.publisher_tools.get_storage_bucket")
    @patch("archive_agents.tools.publisher_tools.get_firestore_client")
    def test_upload_images_called_internally(
        self, mock_get_db, mock_get_bucket, tmp_path
    ):
        """Should call upload_images internally when visual_assets_json is provided."""
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
        # 5 files should have been uploaded (1 original + 4 variants)
        assert mock_blob.upload_from_filename.call_count == 5

    @patch("archive_agents.tools.publisher_tools.get_storage_bucket")
    @patch("archive_agents.tools.publisher_tools.get_firestore_client")
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

    @patch("archive_agents.tools.publisher_tools.get_storage_bucket")
    @patch("archive_agents.tools.publisher_tools.get_firestore_client")
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

    @patch("archive_agents.tools.publisher_tools.get_storage_bucket")
    @patch("archive_agents.tools.publisher_tools.get_firestore_client")
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

    @patch("archive_agents.tools.publisher_tools.get_storage_bucket")
    @patch("archive_agents.tools.publisher_tools.get_firestore_client")
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


class TestPublishMysteryFallbackImages:
    """Tests for publish_mystery with fallback image variants."""

    @patch("archive_agents.tools.publisher_tools.get_storage_bucket")
    @patch("archive_agents.tools.publisher_tools.get_firestore_client")
    def test_fallback_variants_uploaded(
        self, mock_get_db, mock_get_bucket, tmp_path
    ):
        """Should upload fallback image variants correctly."""
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db

        mock_bucket = MagicMock()
        mock_blob = MagicMock()
        mock_bucket.blob.return_value = mock_blob
        mock_bucket.name = "test-bucket"
        mock_get_bucket.return_value = mock_bucket

        # Simulate fallback output from generate_image
        fallback_image = tmp_path / "fallback_header.webp"
        fallback_image.write_bytes(b"fake fallback webp")

        variants = []
        for label in ("sm", "md", "lg", "xl"):
            vpath = tmp_path / f"fallback_header_{label}.webp"
            vpath.write_bytes(b"fake fallback variant")
            variants.append({
                "label": label, "width": 640, "height": 360,
                "filepath": str(vpath),
                "filename": f"fallback_header_{label}.webp",
            })

        visual_assets_json = json.dumps({
            "status": "fallback",
            "filepath": str(fallback_image),
            "filename": "fallback_header.webp",
            "variants": variants,
        })

        mystery_json = _make_mystery_json()
        result = publish_mystery(mystery_json, visual_assets_json)
        result_data = json.loads(result)

        assert result_data["status"] == "success"
        # 5 files: 1 fallback original + 4 fallback variants
        assert mock_blob.upload_from_filename.call_count == 5

        saved_data = mock_db.collection.return_value.document.return_value.set.call_args[0][0]
        assert "images" in saved_data
        assert "variants" in saved_data["images"]


class TestLocalFileRename:
    """Tests for local file renaming to mystery_id-based names."""

    @patch("archive_agents.tools.publisher_tools.get_storage_bucket")
    def test_local_file_renamed_to_mystery_id(self, mock_get_bucket, tmp_path):
        """Should rename local original file to {mystery_id}.png after upload."""
        mock_bucket = MagicMock()
        mock_blob = MagicMock()
        mock_bucket.blob.return_value = mock_blob
        mock_bucket.name = "test-bucket"
        mock_get_bucket.return_value = mock_bucket

        png_file = tmp_path / "header_20260208_145745.png"
        png_file.write_bytes(b"fake png data")

        mystery_id = "OCC-MA-617-20260208143025"
        upload_images(mystery_id, json.dumps([str(png_file)]))

        # Original file should no longer exist
        assert not png_file.exists()
        # Renamed file should exist
        renamed_file = tmp_path / f"{mystery_id}.png"
        assert renamed_file.exists()

    @patch("archive_agents.tools.publisher_tools.get_storage_bucket")
    def test_local_variant_renamed_to_mystery_id(self, mock_get_bucket, tmp_path):
        """Should rename local WebP variant to {mystery_id}_sm.webp after upload."""
        mock_bucket = MagicMock()
        mock_blob = MagicMock()
        mock_bucket.blob.return_value = mock_blob
        mock_bucket.name = "test-bucket"
        mock_get_bucket.return_value = mock_bucket

        webp_file = tmp_path / "header_20260208_145745_sm.webp"
        webp_file.write_bytes(b"fake webp data")

        mystery_id = "OCC-MA-617-20260208143025"
        upload_images(mystery_id, json.dumps([str(webp_file)]))

        # Original file should no longer exist
        assert not webp_file.exists()
        # Renamed file should exist
        renamed_file = tmp_path / f"{mystery_id}_sm.webp"
        assert renamed_file.exists()

    @patch("archive_agents.tools.publisher_tools.get_storage_bucket")
    @patch("archive_agents.tools.publisher_tools.get_firestore_client")
    def test_local_files_renamed_via_publish_mystery(
        self, mock_get_db, mock_get_bucket, tmp_path
    ):
        """Should rename local files when called through publish_mystery."""
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

        # mystery_id-based files should exist
        assert (tmp_path / f"{mystery_id}.png").exists()
        assert (tmp_path / f"{mystery_id}_sm.webp").exists()
        assert (tmp_path / f"{mystery_id}_md.webp").exists()
        assert (tmp_path / f"{mystery_id}_lg.webp").exists()
        assert (tmp_path / f"{mystery_id}_xl.webp").exists()


class TestUploadErrorHandling:
    """Tests for _upload_images_internal error handling and logging."""

    @patch("archive_agents.tools.publisher_tools.get_storage_bucket")
    @patch("archive_agents.tools.publisher_tools.get_firestore_client")
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

    @patch("archive_agents.tools.publisher_tools.get_storage_bucket")
    def test_upload_images_internal_logs_on_failure(self, mock_get_bucket, tmp_path, caplog):
        """Should log an error when upload_from_filename fails."""
        from archive_agents.tools.publisher_tools import _upload_images_internal

        mock_bucket = MagicMock()
        mock_blob = MagicMock()
        mock_blob.upload_from_filename.side_effect = Exception("Network error")
        mock_bucket.blob.return_value = mock_blob
        mock_bucket.name = "test-bucket"
        mock_get_bucket.return_value = mock_bucket

        png_file = tmp_path / "header.png"
        png_file.write_bytes(b"fake png data")

        with caplog.at_level(logging.ERROR, logger="archive_agents.tools.publisher_tools"):
            _upload_images_internal("TEST-001", [str(png_file)])

        assert any("Network error" in record.message for record in caplog.records)

    @patch("archive_agents.tools.publisher_tools.get_storage_bucket")
    def test_upload_images_internal_logs_success(self, mock_get_bucket, tmp_path, caplog):
        """Should log INFO on successful upload."""
        from archive_agents.tools.publisher_tools import _upload_images_internal

        mock_bucket = MagicMock()
        mock_blob = MagicMock()
        mock_blob.exists.return_value = True
        mock_bucket.blob.return_value = mock_blob
        mock_bucket.name = "test-bucket"
        mock_get_bucket.return_value = mock_bucket

        png_file = tmp_path / "header.png"
        png_file.write_bytes(b"fake png data")

        with caplog.at_level(logging.INFO, logger="archive_agents.tools.publisher_tools"):
            _upload_images_internal("TEST-001", [str(png_file)])

        assert any("uploaded successfully" in record.message.lower() for record in caplog.records)

    @patch("archive_agents.tools.publisher_tools.get_storage_bucket")
    def test_upload_verifies_blob_exists(self, mock_get_bucket, tmp_path):
        """Should call blob.exists() after upload to verify."""
        from archive_agents.tools.publisher_tools import _upload_images_internal

        mock_bucket = MagicMock()
        mock_blob = MagicMock()
        mock_blob.exists.return_value = True
        mock_bucket.blob.return_value = mock_blob
        mock_bucket.name = "test-bucket"
        mock_get_bucket.return_value = mock_bucket

        png_file = tmp_path / "header.png"
        png_file.write_bytes(b"fake png data")

        _upload_images_internal("TEST-001", [str(png_file)])

        mock_blob.exists.assert_called_once()

    @patch("archive_agents.tools.publisher_tools.get_storage_bucket")
    def test_upload_logs_warning_when_blob_not_found_after_upload(
        self, mock_get_bucket, tmp_path, caplog
    ):
        """Should log a warning when blob.exists() returns False after upload."""
        from archive_agents.tools.publisher_tools import _upload_images_internal

        mock_bucket = MagicMock()
        mock_blob = MagicMock()
        mock_blob.exists.return_value = False
        mock_bucket.blob.return_value = mock_blob
        mock_bucket.name = "test-bucket"
        mock_get_bucket.return_value = mock_bucket

        png_file = tmp_path / "header.png"
        png_file.write_bytes(b"fake png data")

        with caplog.at_level(logging.WARNING, logger="archive_agents.tools.publisher_tools"):
            result = _upload_images_internal("TEST-001", [str(png_file)])

        assert any("verification failed" in record.message.lower() for record in caplog.records)
        # Should not include the file in results since verification failed
        assert result == {}

    @patch("archive_agents.tools.publisher_tools.get_storage_bucket")
    def test_partial_upload_failure_does_not_block_others(self, mock_get_bucket, tmp_path):
        """When one file fails to upload, other files should still succeed."""
        from archive_agents.tools.publisher_tools import _upload_images_internal

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

    @patch("archive_agents.tools.publisher_tools.get_storage_bucket")
    def test_upload_summary_log(self, mock_get_bucket, tmp_path, caplog):
        """Should log a summary with count of successful uploads."""
        from archive_agents.tools.publisher_tools import _upload_images_internal

        mock_bucket = MagicMock()
        mock_blob = MagicMock()
        mock_blob.exists.return_value = True
        mock_bucket.blob.return_value = mock_blob
        mock_bucket.name = "test-bucket"
        mock_get_bucket.return_value = mock_bucket

        files = []
        for name in ("header.png", "header_sm.webp", "header_md.webp"):
            f = tmp_path / name
            f.write_bytes(b"fake data")
            files.append(str(f))

        with caplog.at_level(logging.INFO, logger="archive_agents.tools.publisher_tools"):
            _upload_images_internal("TEST-001", files)

        assert any("3/3" in record.message for record in caplog.records)
