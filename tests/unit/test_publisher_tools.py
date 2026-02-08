"""Unit tests for Publisher tools."""

import json
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
