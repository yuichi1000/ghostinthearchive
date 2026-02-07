"""Unit tests for Illustrator tools."""

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from archive_agents.tools.illustrator_tools import (
    MAX_RETRIES,
    FALLBACK_IMAGE_PATH,
    _sanitize_prompt,
    generate_image,
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
