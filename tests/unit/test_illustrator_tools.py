"""Unit tests for Illustrator tools."""

import json
import logging
from pathlib import Path
from unittest.mock import MagicMock, patch


from mystery_agents.tools.illustrator_tools import (
    IMAGE_VARIANTS,
    MAX_RETRIES,
    FALLBACK_VARIANTS,
    _build_contextual_safe_prompt,
    _build_safe_fallback_prompt,
    _get_variants,
    _rewrite_safe_prompt,
    _sanitize_prompt,
    generate_image,
    resize_image_variants,
    validate_image,
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

    def test_sanitize_vampire(self):
        """Should replace 'vampire' with 'ancient figure'."""
        result = _sanitize_prompt("A vampire lurking in the shadows")
        assert "ancient figure" in result
        assert "vampire" not in result

    def test_sanitize_cannibal(self):
        """Should replace 'cannibal' with 'forbidden practitioner'."""
        result = _sanitize_prompt("A cannibal in the wilderness")
        assert "forbidden practitioner" in result
        assert "cannibal" not in result

    def test_sanitize_occult_words(self):
        """Should replace curse, witch, ritual with safe alternatives."""
        result = _sanitize_prompt("A curse placed by a witch during a ritual")
        assert "curse" not in result
        assert "witch" not in result
        assert "ritual" not in result
        assert "legacy" in result
        assert "wise woman" in result
        assert "ceremony" in result

    def test_sanitize_violence_words(self):
        """Should replace murder, skull, grave with safe alternatives."""
        result = _sanitize_prompt("A murder near the skull on the grave")
        assert "murder" not in result
        assert "skull" not in result
        assert "grave" not in result
        assert "dark incident" in result
        assert "relic" in result
        assert "resting place" in result


class TestGenerateImageRetry:
    """Tests for generate_image retry mechanism."""

    @patch("mystery_agents.tools.illustrator_tools._get_client")
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

    @patch("mystery_agents.tools.illustrator_tools._rewrite_safe_prompt")
    @patch("mystery_agents.tools.illustrator_tools._get_client")
    def test_retry_on_safety_filter(self, mock_get_client, mock_rewrite):
        """Should retry with rewritten prompt when safety filter blocks."""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_rewrite.return_value = "safe rewritten prompt"

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

    @patch("mystery_agents.tools.illustrator_tools._get_client")
    @patch("mystery_agents.tools.illustrator_tools.time.sleep")
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

    @patch("mystery_agents.tools.illustrator_tools._get_client")
    @patch("mystery_agents.tools.illustrator_tools.time.sleep")
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

    @patch("mystery_agents.tools.illustrator_tools._get_client")
    @patch("mystery_agents.tools.illustrator_tools.time.sleep")
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

    @patch("mystery_agents.tools.illustrator_tools._get_client")
    @patch("mystery_agents.tools.illustrator_tools.time.sleep")
    @patch("mystery_agents.tools.illustrator_tools.shutil.copy2")
    @patch("mystery_agents.tools.illustrator_tools.tempfile.mkdtemp")
    def test_fallback_when_generation_fails(self, mock_mkdtemp, mock_copy2, mock_sleep, mock_get_client):
        """Should return fallback image when all attempts fail."""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.models.generate_images.return_value = MagicMock(generated_images=[])
        mock_mkdtemp.return_value = "/tmp/ghost_images_fallback"

        # Mock fallback image exists
        with patch.object(Path, "exists", return_value=True):
            result = generate_image("A ghost ship", style="folklore")
            result_data = json.loads(result)

        assert result_data["status"] == "fallback"
        assert "fallback_header.webp" in result_data["filename"]
        # フォールバック画像は temp にコピーされる
        assert "/tmp/ghost_images_fallback/" in result_data["filepath"]
        assert result_data["note"] == "Using fallback image due to generation failure"
        assert "retry_suggestion" in result_data

    @patch("mystery_agents.tools.illustrator_tools._get_client")
    @patch("mystery_agents.tools.illustrator_tools.time.sleep")
    @patch("mystery_agents.tools.illustrator_tools.shutil.copy2")
    @patch("mystery_agents.tools.illustrator_tools.tempfile.mkdtemp")
    def test_fallback_copies_to_temp_preserving_originals(self, mock_mkdtemp, mock_copy2, mock_sleep, mock_get_client):
        """静的アセットを temp にコピーし、元ファイルを保全すること。"""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.models.generate_images.return_value = MagicMock(generated_images=[])
        mock_mkdtemp.return_value = "/tmp/ghost_images_fallback"

        with patch.object(Path, "exists", return_value=True):
            generate_image("A ghost ship", style="folklore")

        # shutil.copy2 がメイン画像 + 4バリアントの計5回呼ばれること
        assert mock_copy2.call_count == 5
        # メイン画像のコピー元が静的アセットディレクトリであること
        main_copy_src = mock_copy2.call_args_list[0][0][0]
        assert "assets/fallback_header.webp" in str(main_copy_src)

    @patch("mystery_agents.tools.illustrator_tools._get_client")
    @patch("mystery_agents.tools.illustrator_tools.time.sleep")
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

    @patch("mystery_agents.tools.illustrator_tools._get_client")
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

    @patch("mystery_agents.tools.illustrator_tools._get_client")
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

    @patch("mystery_agents.tools.illustrator_tools._get_client")
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

    @patch("mystery_agents.tools.illustrator_tools._get_client")
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

    @patch("mystery_agents.tools.illustrator_tools._get_client")
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

    @patch("mystery_agents.tools.illustrator_tools.resize_image_variants")
    @patch("mystery_agents.tools.illustrator_tools._get_client")
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
        assert result_data["variant_error"] is None
        mock_resize.assert_called_once()

    @patch("mystery_agents.tools.illustrator_tools.resize_image_variants")
    @patch("mystery_agents.tools.illustrator_tools._get_client")
    def test_resize_failure_returns_empty_variants(self, mock_get_client, mock_resize):
        """Should return empty variants with variant_error when resize fails."""
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
        assert result_data["variant_error"] == "Pillow not installed"

    @patch("mystery_agents.tools.illustrator_tools._get_client")
    @patch("mystery_agents.tools.illustrator_tools.time.sleep")
    @patch("mystery_agents.tools.illustrator_tools.shutil.copy2")
    @patch("mystery_agents.tools.illustrator_tools.tempfile.mkdtemp")
    def test_fallback_includes_pregenerated_variants(self, mock_mkdtemp, mock_copy2, mock_sleep, mock_get_client):
        """Should include pre-generated static variants in fallback response (copied to temp)."""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.models.generate_images.return_value = MagicMock(generated_images=[])
        mock_mkdtemp.return_value = "/tmp/ghost_images_fallback"

        with patch.object(Path, "exists", return_value=True):
            result = generate_image("A ghost ship", style="folklore")
            result_data = json.loads(result)

        assert result_data["status"] == "fallback"
        assert len(result_data["variants"]) == 4
        labels = {v["label"] for v in result_data["variants"]}
        assert labels == {"sm", "md", "lg", "xl"}
        # バリアントのパスが temp ディレクトリを指すこと
        for v in result_data["variants"]:
            assert v["filepath"].startswith("/tmp/ghost_images_fallback/")


class TestGetVariantsLogging:
    """Tests for _get_variants error log on failure."""

    @patch("mystery_agents.tools.illustrator_tools.resize_image_variants")
    def test_get_variants_logs_error_on_failure(self, mock_resize, caplog):
        """Should log an ERROR when variant generation fails."""
        mock_resize.return_value = json.dumps({
            "status": "error",
            "error": "Pillow not installed",
            "variants": [],
        })

        import logging
        with caplog.at_level(logging.ERROR, logger="mystery_agents.tools.illustrator_tools"):
            variants, error_msg = _get_variants("/tmp/test.png")

        assert variants == []
        assert error_msg == "Pillow not installed"
        assert "WebP variant generation FAILED" in caplog.text
        assert "Pillow not installed" in caplog.text

    @patch("mystery_agents.tools.illustrator_tools.resize_image_variants")
    def test_get_variants_returns_none_error_on_success(self, mock_resize):
        """Should return None as error_msg on success."""
        mock_resize.return_value = json.dumps({
            "status": "success",
            "variants": [
                {"label": "sm", "width": 640, "height": 360, "filepath": "/tmp/sm.webp", "filename": "sm.webp"},
            ],
        })

        variants, error_msg = _get_variants("/tmp/test.png")

        assert len(variants) == 1
        assert error_msg is None


class TestBuildSafeFallbackPrompt:
    """Tests for _build_safe_fallback_prompt function."""

    def test_fact_style_returns_archival_prompt(self):
        """Should return a monochrome archival-style prompt for fact style."""
        result = _build_safe_fallback_prompt("fact")
        assert "black and white" in result.lower() or "monochrome" in result.lower()

    def test_folklore_style_returns_woodcut_prompt(self):
        """Should return a woodcut/engraving-style prompt for folklore style."""
        result = _build_safe_fallback_prompt("folklore")
        assert "woodcut" in result.lower() or "engraving" in result.lower()

    def test_auto_style_returns_prompt(self):
        """Should return a valid prompt for auto style."""
        result = _build_safe_fallback_prompt("auto")
        assert len(result) > 20

    def test_no_forbidden_words(self):
        """Should not contain any words from the sanitization dictionary."""
        from mystery_agents.tools.illustrator_tools import _SANITIZE_REPLACEMENTS

        for style in ("fact", "folklore", "auto"):
            result = _build_safe_fallback_prompt(style).lower()
            for word in _SANITIZE_REPLACEMENTS:
                assert word not in result, f"Forbidden word '{word}' found in {style} prompt"

    def test_no_person_references(self):
        """Should not contain person/people/human references."""
        for style in ("fact", "folklore", "auto"):
            result = _build_safe_fallback_prompt(style).lower()
            for word in ("person", "people", "human", "man", "woman", "child", "figure"):
                assert word not in result, f"Person reference '{word}' found in {style} prompt"


class TestGenerateImageProgressiveRetry:
    """Tests for LLM-based progressive retry strategy (3 stages)."""

    @patch("mystery_agents.tools.illustrator_tools._build_contextual_safe_prompt")
    @patch("mystery_agents.tools.illustrator_tools._rewrite_safe_prompt")
    @patch("mystery_agents.tools.illustrator_tools._get_client")
    @patch("mystery_agents.tools.illustrator_tools.time.sleep")
    @patch("mystery_agents.tools.illustrator_tools.shutil.copy2")
    @patch("mystery_agents.tools.illustrator_tools.tempfile.mkdtemp", return_value="/tmp/ghost_images_fb")
    def test_retry_calls_rewrite_then_contextual(
        self, mock_mkdtemp, mock_copy2, mock_sleep, mock_get_client, mock_rewrite, mock_contextual,
    ):
        """Should call _rewrite_safe_prompt on attempt 1, _build_contextual_safe_prompt on attempt 2."""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        mock_rewrite.return_value = "rewritten safe prompt"
        mock_contextual.return_value = "contextual safe prompt"

        prompts_used = []

        def capture_prompt(**kwargs):
            prompts_used.append(kwargs.get("prompt", ""))
            return MagicMock(generated_images=[])

        mock_client.models.generate_images.side_effect = capture_prompt

        with patch.object(Path, "exists", return_value=True):
            generate_image("A ghost ship in haunted waters", style="folklore")

        assert len(prompts_used) == 3
        # Attempt 0: original prompt (with style prefix)
        assert "ghost" in prompts_used[0].lower()
        # Attempt 1: LLM rewrite が呼ばれる
        mock_rewrite.assert_called_once()
        assert prompts_used[1] == "rewritten safe prompt"
        # Attempt 2: contextual safe prompt が呼ばれる
        mock_contextual.assert_called_once()
        assert prompts_used[2] == "contextual safe prompt"

    @patch("mystery_agents.tools.illustrator_tools._rewrite_safe_prompt")
    @patch("mystery_agents.tools.illustrator_tools._get_client")
    @patch("mystery_agents.tools.illustrator_tools.time.sleep")
    def test_success_on_second_attempt_with_rewritten_prompt(
        self, mock_sleep, mock_get_client, mock_rewrite,
    ):
        """Should succeed on second attempt using LLM-rewritten prompt."""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_rewrite.return_value = "safe rewritten prompt"

        mock_image = MagicMock()
        mock_client.models.generate_images.side_effect = [
            MagicMock(generated_images=[]),  # Attempt 0: safety filter
            MagicMock(generated_images=[MagicMock(image=mock_image)]),  # Attempt 1: rewritten succeeds
        ]

        result = generate_image("A ghost ship", style="folklore")
        result_data = json.loads(result)

        assert result_data["status"] == "success"
        assert result_data["attempt"] == 2
        assert result_data["prompt_sanitized"] is True
        mock_rewrite.assert_called_once()

    @patch("mystery_agents.tools.illustrator_tools._build_contextual_safe_prompt")
    @patch("mystery_agents.tools.illustrator_tools._rewrite_safe_prompt")
    @patch("mystery_agents.tools.illustrator_tools._get_client")
    @patch("mystery_agents.tools.illustrator_tools.time.sleep")
    def test_success_on_third_attempt_with_contextual_prompt(
        self, mock_sleep, mock_get_client, mock_rewrite, mock_contextual,
    ):
        """Should succeed on third attempt using contextual safe prompt."""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_rewrite.return_value = "rewritten but still blocked"
        mock_contextual.return_value = "contextual safe prompt"

        mock_image = MagicMock()
        mock_client.models.generate_images.side_effect = [
            MagicMock(generated_images=[]),  # Attempt 0: safety filter
            MagicMock(generated_images=[]),  # Attempt 1: rewritten still blocked
            MagicMock(generated_images=[MagicMock(image=mock_image)]),  # Attempt 2: contextual succeeds
        ]

        result = generate_image("A ghost ship", style="folklore")
        result_data = json.loads(result)

        assert result_data["status"] == "success"
        assert result_data["attempt"] == 3
        assert mock_client.models.generate_images.call_count == 3


class TestGenerateImageSafetyConfig:
    """Tests for safety_filter_level configuration."""

    @patch("mystery_agents.tools.illustrator_tools._get_client")
    @patch("mystery_agents.tools.illustrator_tools.types.GenerateImagesConfig")
    def test_uses_block_only_high(self, mock_config_cls, mock_get_client):
        """Should use BLOCK_ONLY_HIGH safety filter level."""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        mock_image = MagicMock()
        mock_response = MagicMock()
        mock_response.generated_images = [MagicMock(image=mock_image)]
        mock_client.models.generate_images.return_value = mock_response

        generate_image("A test image", style="auto")

        mock_config_cls.assert_called_once()
        call_kwargs = mock_config_cls.call_args.kwargs
        assert call_kwargs["safety_filter_level"] == "BLOCK_ONLY_HIGH"


class TestGenerateImageLogging:
    """Tests for error logging in generate_image."""

    @patch("mystery_agents.tools.illustrator_tools._get_client")
    @patch("mystery_agents.tools.illustrator_tools.time.sleep")
    @patch("mystery_agents.tools.illustrator_tools.shutil.copy2")
    @patch("mystery_agents.tools.illustrator_tools.tempfile.mkdtemp", return_value="/tmp/ghost_images_fb")
    def test_logs_safety_filter_warning(self, mock_mkdtemp, mock_copy2, mock_sleep, mock_get_client, caplog):
        """Should log warning when safety filter blocks generation."""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.models.generate_images.return_value = MagicMock(generated_images=[])

        with caplog.at_level(logging.WARNING, logger="mystery_agents.tools.illustrator_tools"):
            with patch.object(Path, "exists", return_value=True):
                generate_image("A ghost ship", style="folklore")

        assert "Safety filter" in caplog.text

    @patch("mystery_agents.tools.illustrator_tools._get_client")
    @patch("mystery_agents.tools.illustrator_tools.time.sleep")
    @patch("mystery_agents.tools.illustrator_tools.shutil.copy2")
    @patch("mystery_agents.tools.illustrator_tools.tempfile.mkdtemp", return_value="/tmp/ghost_images_fb")
    def test_logs_rate_limit_warning(self, mock_mkdtemp, mock_copy2, mock_sleep, mock_get_client, caplog):
        """Should log warning on rate limit errors."""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.models.generate_images.side_effect = Exception("Resource exhausted: quota exceeded")

        with caplog.at_level(logging.WARNING, logger="mystery_agents.tools.illustrator_tools"):
            with patch.object(Path, "exists", return_value=True):
                generate_image("A test image", style="auto")

        assert "Rate limit" in caplog.text

    @patch("mystery_agents.tools.illustrator_tools._get_client")
    @patch("mystery_agents.tools.illustrator_tools.time.sleep")
    @patch("mystery_agents.tools.illustrator_tools.shutil.copy2")
    @patch("mystery_agents.tools.illustrator_tools.tempfile.mkdtemp", return_value="/tmp/ghost_images_fb")
    def test_logs_fallback_error(self, mock_mkdtemp, mock_copy2, mock_sleep, mock_get_client, caplog):
        """Should log error when falling back to default image."""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.models.generate_images.return_value = MagicMock(generated_images=[])

        with caplog.at_level(logging.ERROR, logger="mystery_agents.tools.illustrator_tools"):
            with patch.object(Path, "exists", return_value=True):
                generate_image("A ghost ship", style="folklore")

        assert "All" in caplog.text and "attempts failed" in caplog.text

    @patch("mystery_agents.tools.illustrator_tools._get_client")
    @patch("mystery_agents.tools.illustrator_tools.time.sleep")
    def test_logs_no_fallback_error(self, mock_sleep, mock_get_client, caplog):
        """Should log error when no fallback image is available."""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.models.generate_images.return_value = MagicMock(generated_images=[])

        with caplog.at_level(logging.ERROR, logger="mystery_agents.tools.illustrator_tools"):
            with patch.object(Path, "exists", return_value=False):
                generate_image("A ghost ship", style="folklore")

        assert "no fallback" in caplog.text.lower()

    @patch("mystery_agents.tools.illustrator_tools._get_client")
    @patch("mystery_agents.tools.illustrator_tools.time.sleep")
    def test_logs_timeout_warning(self, mock_sleep, mock_get_client, caplog):
        """Should log warning on timeout errors."""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        mock_image = MagicMock()
        mock_client.models.generate_images.side_effect = [
            Exception("Deadline exceeded"),
            MagicMock(generated_images=[MagicMock(image=mock_image)]),
        ]

        with caplog.at_level(logging.WARNING, logger="mystery_agents.tools.illustrator_tools"):
            generate_image("A test image", style="auto")

        assert "Timeout" in caplog.text


class TestGenerateImageRetrySuggestion:
    """Tests for retry_suggestion field in fallback response."""

    @patch("mystery_agents.tools.illustrator_tools._get_client")
    @patch("mystery_agents.tools.illustrator_tools.time.sleep")
    @patch("mystery_agents.tools.illustrator_tools.shutil.copy2")
    @patch("mystery_agents.tools.illustrator_tools.tempfile.mkdtemp", return_value="/tmp/ghost_images_fb")
    def test_fallback_includes_retry_suggestion(self, mock_mkdtemp, mock_copy2, mock_sleep, mock_get_client):
        """Should include retry_suggestion field in fallback response."""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.models.generate_images.return_value = MagicMock(generated_images=[])

        with patch.object(Path, "exists", return_value=True):
            result = generate_image("A ghost ship", style="folklore")
            result_data = json.loads(result)

        assert result_data["status"] == "fallback"
        assert "retry_suggestion" in result_data
        assert len(result_data["retry_suggestion"]) > 0


class TestRewriteSafePrompt:
    """Tests for _rewrite_safe_prompt (LLM-based prompt rewriting)."""

    @patch("mystery_agents.tools.illustrator_tools._get_client")
    def test_rewrite_returns_safe_prompt(self, mock_get_client):
        """Flash 呼び出し成功でプロンプトが返る。"""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        mock_response = MagicMock()
        mock_response.text = "An empty 1890s Salem courtroom at dusk"
        mock_client.models.generate_content.return_value = mock_response

        result = _rewrite_safe_prompt("A ghostly figure haunting Salem", "fact")

        assert result == "An empty 1890s Salem courtroom at dusk"
        mock_client.models.generate_content.assert_called_once()

    @patch("mystery_agents.tools.illustrator_tools._get_client")
    def test_rewrite_falls_back_to_sanitize(self, mock_get_client):
        """Flash 例外時に _sanitize_prompt() にフォールバック。"""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.models.generate_content.side_effect = Exception("API error")

        result = _rewrite_safe_prompt("A ghost ship sailing", "folklore")

        # _sanitize_prompt が適用される（"ghost" → "ethereal figure"）
        assert "ghost" not in result
        assert "ethereal figure" in result

    @patch("mystery_agents.tools.illustrator_tools._get_client")
    def test_rewrite_preserves_style(self, mock_get_client):
        """スタイル情報がプロンプトに含まれる。"""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        mock_response = MagicMock()
        mock_response.text = "Safe prompt"
        mock_client.models.generate_content.return_value = mock_response

        _rewrite_safe_prompt("A ghost ship", "folklore")

        call_args = mock_client.models.generate_content.call_args
        # contents 引数にプロンプトが含まれる
        prompt_text = call_args.kwargs.get("contents", "")
        assert "ghost ship" in prompt_text.lower()

    @patch("mystery_agents.tools.illustrator_tools._get_client")
    def test_rewrite_empty_response_falls_back(self, mock_get_client):
        """Flash が空レスポンスを返した場合 _sanitize_prompt にフォールバック。"""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        mock_response = MagicMock()
        mock_response.text = "   "
        mock_client.models.generate_content.return_value = mock_response

        result = _rewrite_safe_prompt("A ghost ship", "auto")

        # 空文字列なので _sanitize_prompt にフォールバック
        assert "ghost" not in result


class TestBuildContextualSafePrompt:
    """Tests for _build_contextual_safe_prompt (article-based safe prompt)."""

    @patch("mystery_agents.tools.illustrator_tools._get_client")
    def test_contextual_uses_article_content(self, mock_get_client):
        """creative_content から状況依存プロンプトを生成。"""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        mock_response = MagicMock()
        mock_response.text = "A weathered farmhouse in 1817 Tennessee at twilight"
        mock_client.models.generate_content.return_value = mock_response

        mock_ctx = MagicMock()
        mock_ctx.state = {"creative_content": "The Bell Witch legend of Tennessee..."}

        result = _build_contextual_safe_prompt("folklore", mock_ctx)

        assert result == "A weathered farmhouse in 1817 Tennessee at twilight"
        mock_client.models.generate_content.assert_called_once()

    @patch("mystery_agents.tools.illustrator_tools._get_client")
    def test_contextual_falls_back_to_generic(self, mock_get_client):
        """Flash 例外時に _build_safe_fallback_prompt() にフォールバック。"""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.models.generate_content.side_effect = Exception("API timeout")

        mock_ctx = MagicMock()
        mock_ctx.state = {"creative_content": "Some article content..."}

        result = _build_contextual_safe_prompt("fact", mock_ctx)

        # _build_safe_fallback_prompt("fact") の結果が返る
        assert "black and white" in result.lower() or "monochrome" in result.lower()

    def test_contextual_no_creative_content(self):
        """creative_content なしで汎用フォールバック。"""
        mock_ctx = MagicMock()
        mock_ctx.state = {}

        result = _build_contextual_safe_prompt("folklore", mock_ctx)

        # _build_safe_fallback_prompt("folklore") の結果が返る
        assert "woodcut" in result.lower() or "engraving" in result.lower()

    def test_contextual_no_tool_context(self):
        """tool_context が None で汎用フォールバック。"""
        result = _build_contextual_safe_prompt("auto", None)

        # _build_safe_fallback_prompt("auto") の結果が返る
        assert len(result) > 20

    def test_contextual_no_content_marker(self):
        """creative_content に NO_CONTENT が含まれる場合は汎用フォールバック。"""
        mock_ctx = MagicMock()
        mock_ctx.state = {"creative_content": "NO_CONTENT"}

        result = _build_contextual_safe_prompt("fact", mock_ctx)

        assert "black and white" in result.lower() or "monochrome" in result.lower()


class TestValidateImage:
    """Tests for validate_image function."""

    @patch("mystery_agents.tools.illustrator_tools._get_client")
    def test_validate_pass(self, mock_get_client, tmp_path):
        """confidence ≥ 0.6 で "pass"。"""
        from PIL import Image as PILImage

        img_path = tmp_path / "test.png"
        PILImage.new("RGB", (100, 100), "red").save(str(img_path))

        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        mock_response = MagicMock()
        mock_response.text = json.dumps({
            "verdict": "pass",
            "confidence": 0.85,
            "feedback": "Image matches the article theme well",
            "suggested_focus": "",
        })
        mock_client.models.generate_content.return_value = mock_response

        result = json.loads(validate_image(str(img_path), "Bell Witch legend", "folklore"))

        assert result["verdict"] == "pass"
        assert result["confidence"] == 0.85

    @patch("mystery_agents.tools.illustrator_tools._get_client")
    def test_validate_fail_with_feedback(self, mock_get_client, tmp_path):
        """confidence < 0.6 で "fail" + feedback。"""
        from PIL import Image as PILImage

        img_path = tmp_path / "test.png"
        PILImage.new("RGB", (100, 100), "blue").save(str(img_path))

        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        mock_response = MagicMock()
        mock_response.text = json.dumps({
            "verdict": "fail",
            "confidence": 0.3,
            "feedback": "Image shows modern cityscape, not historical",
            "suggested_focus": "Focus on 19th century rural Tennessee landscape",
        })
        mock_client.models.generate_content.return_value = mock_response

        result = json.loads(validate_image(str(img_path), "Bell Witch legend", "folklore"))

        assert result["verdict"] == "fail"
        assert "suggested_focus" in result

    def test_validate_image_not_found(self):
        """存在しないパスで "error"。"""
        result = json.loads(validate_image("/nonexistent/image.png", "test theme"))

        assert result["status"] == "error"
        assert "not found" in result["error"].lower()

    @patch("mystery_agents.tools.illustrator_tools._get_client")
    @patch("mystery_agents.tools.illustrator_tools.time.sleep")
    def test_validate_api_error_returns_error(self, mock_sleep, mock_get_client, tmp_path):
        """Gemini 例外時 "error"（フェイルオープン）。"""
        from PIL import Image as PILImage

        img_path = tmp_path / "test.png"
        PILImage.new("RGB", (100, 100), "green").save(str(img_path))

        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.models.generate_content.side_effect = Exception("API timeout")

        result = json.loads(validate_image(str(img_path), "test theme"))

        assert result["status"] == "error"
        assert "API" in result["error"] or "error" in result["error"].lower()

    @patch("mystery_agents.tools.illustrator_tools._get_client")
    @patch("mystery_agents.tools.illustrator_tools.time.sleep")
    def test_validate_retry_on_first_failure(self, mock_sleep, mock_get_client, tmp_path):
        """1回目失敗 → 2回目成功。"""
        from PIL import Image as PILImage

        img_path = tmp_path / "test.png"
        PILImage.new("RGB", (100, 100), "red").save(str(img_path))

        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        mock_response_ok = MagicMock()
        mock_response_ok.text = json.dumps({
            "verdict": "pass", "confidence": 0.9,
            "feedback": "Good", "suggested_focus": "",
        })
        mock_client.models.generate_content.side_effect = [
            Exception("Temporary error"),
            mock_response_ok,
        ]

        result = json.loads(validate_image(str(img_path), "test theme"))

        assert result["verdict"] == "pass"
        assert mock_client.models.generate_content.call_count == 2
        mock_sleep.assert_called_once_with(2)

    @patch("mystery_agents.tools.illustrator_tools._get_client")
    def test_validate_unparseable_response(self, mock_get_client, tmp_path):
        """非JSON でも正規表現で verdict を抽出。"""
        from PIL import Image as PILImage

        img_path = tmp_path / "test.png"
        PILImage.new("RGB", (100, 100), "red").save(str(img_path))

        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        mock_response = MagicMock()
        mock_response.text = 'Here is my evaluation: "verdict": "pass", "confidence": 0.8 ...'
        mock_client.models.generate_content.return_value = mock_response

        result = json.loads(validate_image(str(img_path), "test theme"))

        assert result["verdict"] == "pass"
        assert result["confidence"] == 0.8

    @patch("mystery_agents.tools.illustrator_tools._get_client")
    def test_validate_saves_to_session_state(self, mock_get_client, tmp_path):
        """state["image_validation"] に保存。"""
        from PIL import Image as PILImage

        img_path = tmp_path / "test.png"
        PILImage.new("RGB", (100, 100), "red").save(str(img_path))

        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        mock_response = MagicMock()
        mock_response.text = json.dumps({
            "verdict": "pass", "confidence": 0.9,
            "feedback": "Good", "suggested_focus": "",
        })
        mock_client.models.generate_content.return_value = mock_response

        mock_ctx = MagicMock()
        mock_ctx.state = {}

        validate_image(str(img_path), "test theme", tool_context=mock_ctx)

        assert "image_validation" in mock_ctx.state
        assert mock_ctx.state["image_validation"]["verdict"] == "pass"

    @patch("mystery_agents.tools.illustrator_tools._get_client")
    def test_validate_low_confidence_overrides_pass(self, mock_get_client, tmp_path):
        """verdict="pass" でも confidence < threshold なら "fail" に上書き。"""
        from PIL import Image as PILImage

        img_path = tmp_path / "test.png"
        PILImage.new("RGB", (100, 100), "red").save(str(img_path))

        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        mock_response = MagicMock()
        mock_response.text = json.dumps({
            "verdict": "pass",
            "confidence": 0.4,  # 閾値 0.6 未満
            "feedback": "Marginal match",
            "suggested_focus": "Better alignment needed",
        })
        mock_client.models.generate_content.return_value = mock_response

        result = json.loads(validate_image(str(img_path), "test theme"))

        assert result["verdict"] == "fail"
        assert "below threshold" in result["feedback"]

    def test_validate_corrupt_image(self, tmp_path):
        """破損画像ファイルで "error"。"""
        img_path = tmp_path / "corrupt.png"
        img_path.write_bytes(b"not a real image")

        result = json.loads(validate_image(str(img_path), "test theme"))

        assert result["status"] == "error"
        assert "load" in result["error"].lower() or "image" in result["error"].lower()
