"""Unit tests for Illustrator tools."""

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from archive_agents.tools.illustrator_tools import (
    IMAGE_VARIANTS,
    MAX_RETRIES,
    FALLBACK_IMAGE_PATH,
    _sanitize_prompt,
    generate_image,
    resize_image_variants,
)


class TestSanitizePrompt:
    """Tests for _sanitize_prompt function."""

    def test_sanitize_ghost(self):
        """Should replace 'ghost' with 'ethereal figure'."""
        result = _sanitize_prompt("A ghost ship sailing")
        assert "ethereal figure" in result
        assert "ghost" not in result

    def test_sanitize_ghostly(self):
        """Should replace 'ghostly' with 'mysterious'."""
        result = _sanitize_prompt("A ghostly apparition")
        assert "mysterious" in result
        assert "ghostly" not in result

    def test_sanitize_haunted(self):
        """Should replace 'haunted' with 'atmospheric'."""
        result = _sanitize_prompt("A haunted house")
        assert "atmospheric" in result
        assert "haunted" not in result

    def test_sanitize_multiple_words(self):
        """Should replace multiple problematic words."""
        result = _sanitize_prompt("A ghost in a haunted, eerie forest")
        assert "ghost" not in result
        assert "haunted" not in result
        assert "eerie" not in result

    def test_sanitize_preserves_safe_words(self):
        """Should preserve words that don't need sanitization."""
        result = _sanitize_prompt("A ship sailing on calm waters")
        assert "ship" in result
        assert "sailing" in result
        assert "calm" in result
        assert "waters" in result

    def test_sanitize_case_insensitive(self):
        """Should handle uppercase text (converts to lowercase)."""
        result = _sanitize_prompt("A GHOST SHIP")
        assert "ghost" not in result.lower()


class TestGenerateImageRetry:
    """Tests for generate_image retry mechanism."""

    @patch("archive_agents.tools.illustrator_tools._get_client")
    def test_success_on_first_attempt(self, mock_get_client):
        """Should succeed on first attempt if API returns image."""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        mock_image = MagicMock()
        mock_response = MagicMock()
        mock_response.generated_images = [MagicMock(image=mock_image)]
        mock_client.models.generate_images.return_value = mock_response

        result = generate_image("A test image", style="auto")
        result_data = json.loads(result)

        assert result_data["status"] == "success"
        assert result_data["attempt"] == 1
        assert result_data["prompt_sanitized"] is False
        assert mock_client.models.generate_images.call_count == 1

    @patch("archive_agents.tools.illustrator_tools._get_client")
    def test_retry_on_safety_filter(self, mock_get_client):
        """Should retry with sanitized prompt when safety filter blocks."""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        mock_image = MagicMock()
        # First call returns empty (safety filter), second succeeds
        mock_client.models.generate_images.side_effect = [
            MagicMock(generated_images=[]),  # Safety filter blocked
            MagicMock(generated_images=[MagicMock(image=mock_image)]),  # Success
        ]

        result = generate_image("A ghost ship", style="folklore")
        result_data = json.loads(result)

        assert result_data["status"] == "success"
        assert result_data["prompt_sanitized"] is True
        assert mock_client.models.generate_images.call_count == 2

    @patch("archive_agents.tools.illustrator_tools._get_client")
    @patch("archive_agents.tools.illustrator_tools.time.sleep")
    def test_retry_on_rate_limit(self, mock_sleep, mock_get_client):
        """Should retry with backoff on rate limit errors."""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        mock_image = MagicMock()
        # First call raises rate limit, second succeeds
        mock_client.models.generate_images.side_effect = [
            Exception("Resource exhausted: quota exceeded"),
            MagicMock(generated_images=[MagicMock(image=mock_image)]),
        ]

        result = generate_image("A test image", style="auto")
        result_data = json.loads(result)

        assert result_data["status"] == "success"
        assert mock_sleep.called
        assert mock_client.models.generate_images.call_count == 2

    @patch("archive_agents.tools.illustrator_tools._get_client")
    @patch("archive_agents.tools.illustrator_tools.time.sleep")
    def test_retry_on_timeout(self, mock_sleep, mock_get_client):
        """Should retry on timeout errors."""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        mock_image = MagicMock()
        mock_client.models.generate_images.side_effect = [
            Exception("Deadline exceeded"),
            MagicMock(generated_images=[MagicMock(image=mock_image)]),
        ]

        result = generate_image("A test image", style="auto")
        result_data = json.loads(result)

        assert result_data["status"] == "success"
        assert mock_sleep.called

    @patch("archive_agents.tools.illustrator_tools._get_client")
    @patch("archive_agents.tools.illustrator_tools.time.sleep")
    def test_max_retries_exceeded(self, mock_sleep, mock_get_client):
        """Should fail after MAX_RETRIES attempts."""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        # All attempts fail with safety filter
        mock_client.models.generate_images.return_value = MagicMock(generated_images=[])

        # Mock fallback image doesn't exist
        with patch.object(Path, "exists", return_value=False):
            result = generate_image("A ghost ship", style="folklore")
            result_data = json.loads(result)

        assert result_data["status"] == "error"
        assert result_data["attempts"] == MAX_RETRIES
        assert "failed after" in result_data["error"]


class TestGenerateImageFallback:
    """Tests for fallback image functionality."""

    @patch("archive_agents.tools.illustrator_tools._get_client")
    @patch("archive_agents.tools.illustrator_tools.time.sleep")
    def test_fallback_when_generation_fails(self, mock_sleep, mock_get_client):
        """Should return fallback image when all attempts fail."""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.models.generate_images.return_value = MagicMock(generated_images=[])

        # Mock fallback image exists
        with patch.object(Path, "exists", return_value=True):
            result = generate_image("A ghost ship", style="folklore")
            result_data = json.loads(result)

        assert result_data["status"] == "fallback"
        assert "fallback_header.webp" in result_data["filename"]
        assert result_data["note"] == "Using fallback image due to generation failure"

    @patch("archive_agents.tools.illustrator_tools._get_client")
    @patch("archive_agents.tools.illustrator_tools.time.sleep")
    def test_error_when_no_fallback(self, mock_sleep, mock_get_client):
        """Should return error when fallback doesn't exist."""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.models.generate_images.return_value = MagicMock(generated_images=[])

        with patch.object(Path, "exists", return_value=False):
            result = generate_image("A ghost ship", style="folklore")
            result_data = json.loads(result)

        assert result_data["status"] == "error"


class TestGenerateImageStyles:
    """Tests for style-specific prompt modifications."""

    @patch("archive_agents.tools.illustrator_tools._get_client")
    def test_fact_style_prefix(self, mock_get_client):
        """Should add monochrome prefix for fact style."""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        mock_image = MagicMock()
        mock_response = MagicMock()
        mock_response.generated_images = [MagicMock(image=mock_image)]
        mock_client.models.generate_images.return_value = mock_response

        result = generate_image("A ship's log", style="fact")
        result_data = json.loads(result)

        assert "Black and white" in result_data["prompt_used"]
        assert result_data["style"] == "fact"

    @patch("archive_agents.tools.illustrator_tools._get_client")
    def test_folklore_style_prefix(self, mock_get_client):
        """Should add woodcut prefix for folklore style."""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        mock_image = MagicMock()
        mock_response = MagicMock()
        mock_response.generated_images = [MagicMock(image=mock_image)]
        mock_client.models.generate_images.return_value = mock_response

        result = generate_image("A mysterious ship", style="folklore")
        result_data = json.loads(result)

        assert "woodcut" in result_data["prompt_used"]
        assert result_data["style"] == "folklore"

    @patch("archive_agents.tools.illustrator_tools._get_client")
    def test_auto_style_no_prefix(self, mock_get_client):
        """Should not add prefix for auto style."""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        mock_image = MagicMock()
        mock_response = MagicMock()
        mock_response.generated_images = [MagicMock(image=mock_image)]
        mock_client.models.generate_images.return_value = mock_response

        result = generate_image("A simple image", style="auto")
        result_data = json.loads(result)

        assert result_data["prompt_used"] == "A simple image"
        assert result_data["style"] == "auto"


class TestGenerateImageOutput:
    """Tests for generate_image output format."""

    @patch("archive_agents.tools.illustrator_tools._get_client")
    def test_success_response_format(self, mock_get_client):
        """Should return correctly formatted JSON on success."""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        mock_image = MagicMock()
        mock_response = MagicMock()
        mock_response.generated_images = [MagicMock(image=mock_image)]
        mock_client.models.generate_images.return_value = mock_response

        result = generate_image(
            "A test image",
            style="fact",
            aspect_ratio="16:9",
            filename_hint="test_image"
        )
        result_data = json.loads(result)

        assert result_data["status"] == "success"
        assert "filepath" in result_data
        assert "filename" in result_data
        assert "prompt_used" in result_data
        assert result_data["style"] == "fact"
        assert result_data["aspect_ratio"] == "16:9"
        assert result_data["attempt"] == 1

    @patch("archive_agents.tools.illustrator_tools._get_client")
    def test_filename_hint_sanitization(self, mock_get_client):
        """Should sanitize filename hint."""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        mock_image = MagicMock()
        mock_response = MagicMock()
        mock_response.generated_images = [MagicMock(image=mock_image)]
        mock_client.models.generate_images.return_value = mock_response

        result = generate_image(
            "A test image",
            filename_hint="test/image:with<special>chars"
        )
        result_data = json.loads(result)

        # Special characters should be replaced with underscores
        assert "/" not in result_data["filename"]
        assert ":" not in result_data["filename"]
        assert "<" not in result_data["filename"]
        assert ">" not in result_data["filename"]


class TestResizeImageVariants:
    """Tests for resize_image_variants function."""

    def test_creates_four_variants(self, tmp_path):
        """Should create 4 WebP variant files from a source image."""
        # Create a real PNG test image using Pillow
        from PIL import Image as PILImage

        src = tmp_path / "header.png"
        img = PILImage.new("RGB", (1920, 1080), color="red")
        img.save(str(src))

        result = json.loads(resize_image_variants(str(src)))

        assert result["status"] == "success"
        assert len(result["variants"]) == 4
        for v in result["variants"]:
            assert Path(v["filepath"]).exists()
            assert v["filename"].endswith(".webp")

    def test_no_upscaling(self, tmp_path):
        """Should not upscale when source is smaller than variant width."""
        from PIL import Image as PILImage

        src = tmp_path / "small.png"
        img = PILImage.new("RGB", (600, 338), color="blue")
        img.save(str(src))

        result = json.loads(resize_image_variants(str(src)))

        assert result["status"] == "success"
        for v in result["variants"]:
            assert v["width"] <= 600

    def test_maintains_aspect_ratio(self, tmp_path):
        """Should maintain the original 16:9 aspect ratio."""
        from PIL import Image as PILImage

        src = tmp_path / "wide.png"
        img = PILImage.new("RGB", (1920, 1080), color="green")
        img.save(str(src))

        result = json.loads(resize_image_variants(str(src)))

        for v in result["variants"]:
            ratio = v["width"] / v["height"]
            assert abs(ratio - 16 / 9) < 0.02

    def test_variant_filenames(self, tmp_path):
        """Should follow {stem}_{label}.webp naming pattern."""
        from PIL import Image as PILImage

        src = tmp_path / "header_20260208.png"
        img = PILImage.new("RGB", (1920, 1080), color="white")
        img.save(str(src))

        result = json.loads(resize_image_variants(str(src)))

        expected_labels = {v["label"] for v in IMAGE_VARIANTS}
        actual_labels = {v["label"] for v in result["variants"]}
        assert actual_labels == expected_labels

        for v in result["variants"]:
            assert v["filename"] == f"header_20260208_{v['label']}.webp"

    def test_nonexistent_source_returns_error(self):
        """Should return error JSON when source file doesn't exist."""
        result = json.loads(resize_image_variants("/nonexistent/image.png"))

        assert result["status"] == "error"
        assert "not found" in result["error"].lower() or "not exist" in result["error"].lower()

    def test_output_json_structure(self, tmp_path):
        """Should return JSON with correct structure for each variant."""
        from PIL import Image as PILImage

        src = tmp_path / "test.png"
        img = PILImage.new("RGB", (1920, 1080), color="black")
        img.save(str(src))

        result = json.loads(resize_image_variants(str(src)))

        assert result["status"] == "success"
        for v in result["variants"]:
            assert "label" in v
            assert "width" in v
            assert "height" in v
            assert "filepath" in v
            assert "filename" in v
            assert isinstance(v["width"], int)
            assert isinstance(v["height"], int)


class TestGenerateImageWithVariants:
    """Tests for generate_image including variants."""

    @patch("archive_agents.tools.illustrator_tools.resize_image_variants")
    @patch("archive_agents.tools.illustrator_tools._get_client")
    def test_success_includes_variants(self, mock_get_client, mock_resize):
        """Should include variants in success response."""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        mock_image = MagicMock()
        mock_response = MagicMock()
        mock_response.generated_images = [MagicMock(image=mock_image)]
        mock_client.models.generate_images.return_value = mock_response

        mock_resize.return_value = json.dumps({
            "status": "success",
            "variants": [
                {"label": "sm", "width": 640, "height": 360, "filepath": "/tmp/sm.webp", "filename": "sm.webp"},
            ],
        })

        result = generate_image("A test image", style="auto")
        result_data = json.loads(result)

        assert result_data["status"] == "success"
        assert "variants" in result_data
        assert len(result_data["variants"]) == 1
        mock_resize.assert_called_once()

    @patch("archive_agents.tools.illustrator_tools.resize_image_variants")
    @patch("archive_agents.tools.illustrator_tools._get_client")
    def test_resize_failure_returns_empty_variants(self, mock_get_client, mock_resize):
        """Should return empty variants when resize fails (graceful degradation)."""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        mock_image = MagicMock()
        mock_response = MagicMock()
        mock_response.generated_images = [MagicMock(image=mock_image)]
        mock_client.models.generate_images.return_value = mock_response

        mock_resize.return_value = json.dumps({
            "status": "error",
            "error": "Pillow not installed",
            "variants": [],
        })

        result = generate_image("A test image", style="auto")
        result_data = json.loads(result)

        assert result_data["status"] == "success"
        assert result_data["variants"] == []

    @patch("archive_agents.tools.illustrator_tools.resize_image_variants")
    @patch("archive_agents.tools.illustrator_tools._get_client")
    @patch("archive_agents.tools.illustrator_tools.time.sleep")
    def test_fallback_includes_variants(self, mock_sleep, mock_get_client, mock_resize):
        """Should include variants in fallback response."""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.models.generate_images.return_value = MagicMock(generated_images=[])

        mock_resize.return_value = json.dumps({
            "status": "success",
            "variants": [
                {"label": "sm", "width": 640, "height": 360, "filepath": "/tmp/sm.webp", "filename": "sm.webp"},
            ],
        })

        with patch.object(Path, "exists", return_value=True):
            result = generate_image("A ghost ship", style="folklore")
            result_data = json.loads(result)

        assert result_data["status"] == "fallback"
        assert "variants" in result_data
        mock_resize.assert_called_once()
