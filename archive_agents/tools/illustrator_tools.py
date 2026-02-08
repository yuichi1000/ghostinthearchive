"""LLM-facing tool functions for the Illustrator Agent.

Generates images using Imagen 3 and saves them to local storage.
"""

import json
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Optional

from google import genai
from google.genai import types

# Retry configuration
MAX_RETRIES = 3
RETRY_DELAY_SECONDS = 2

# Fallback image path
FALLBACK_IMAGE_PATH = Path(__file__).parent.parent / "assets" / "fallback_header.webp"

# Responsive image variant configuration
IMAGE_VARIANTS = [
    {"label": "sm", "width": 640},   # モバイル
    {"label": "md", "width": 828},   # タブレット
    {"label": "lg", "width": 1200},  # デスクトップ
    {"label": "xl", "width": 1920},  # 大画面/Retina
]
WEBP_QUALITY = 85

def resize_image_variants(source_path: str) -> str:
    """Generate multiple WebP variants from a source image.

    Creates responsive image variants at predefined widths for optimal
    delivery across different viewport sizes.

    Args:
        source_path: Absolute path to the source image file.

    Returns:
        JSON string with variant details (label, width, height, filepath, filename).
    """
    src = Path(source_path)
    if not src.exists():
        return json.dumps({
            "status": "error",
            "error": f"Source image not found: {source_path}",
            "variants": [],
        }, ensure_ascii=False)

    try:
        from PIL import Image as PILImage

        with PILImage.open(src) as img:
            orig_w, orig_h = img.size
            variants = []

            for spec in IMAGE_VARIANTS:
                target_w = spec["width"]

                # Skip upscaling
                if target_w >= orig_w:
                    target_w = orig_w

                # Calculate height maintaining aspect ratio
                ratio = target_w / orig_w
                target_h = round(orig_h * ratio)

                resized = img.resize((target_w, target_h), PILImage.LANCZOS)
                out_name = f"{src.stem}_{spec['label']}.webp"
                out_path = src.parent / out_name
                resized.save(str(out_path), "WEBP", quality=WEBP_QUALITY)

                variants.append({
                    "label": spec["label"],
                    "width": target_w,
                    "height": target_h,
                    "filepath": str(out_path),
                    "filename": out_name,
                })

            return json.dumps({
                "status": "success",
                "variants": variants,
            }, ensure_ascii=False)

    except Exception as e:
        return json.dumps({
            "status": "error",
            "error": str(e),
            "variants": [],
        }, ensure_ascii=False)


# Prompt sanitization mapping for safety filter avoidance
_SANITIZE_REPLACEMENTS = {
    "ghost": "ethereal figure",
    "ghostly": "mysterious",
    "ghosts": "ethereal figures",
    "haunted": "atmospheric",
    "haunting": "evocative",
    "spirit": "presence",
    "spirits": "presences",
    "supernatural": "extraordinary",
    "eerie": "atmospheric",
    "horror": "dramatic",
    "terrifying": "awe-inspiring",
    "demon": "shadowy figure",
    "demons": "shadowy figures",
    "corpse": "fallen figure",
    "dead body": "motionless figure",
    "blood": "dark stain",
    "bloody": "dark",
}


def _sanitize_prompt(prompt: str) -> str:
    """Sanitize prompt to avoid safety filter triggers.

    Replaces potentially problematic words with safer alternatives
    while preserving the artistic intent.

    Args:
        prompt: Original prompt text.

    Returns:
        Sanitized prompt with problematic words replaced.
    """
    result = prompt.lower()
    # Sort by length (longest first) to avoid partial replacements
    # e.g., "ghostly" should be replaced before "ghost"
    sorted_replacements = sorted(
        _SANITIZE_REPLACEMENTS.items(), key=lambda x: len(x[0]), reverse=True
    )
    for old, new in sorted_replacements:
        result = result.replace(old, new)
    return result


def _get_client() -> genai.Client:
    """Get a configured genai client."""
    if os.environ.get("GOOGLE_GENAI_USE_VERTEXAI", "").upper() == "TRUE":
        return genai.Client(
            vertexai=True,
            project=os.environ.get("GOOGLE_CLOUD_PROJECT"),
            location=os.environ.get("GOOGLE_CLOUD_LOCATION", "us-central1"),
        )
    return genai.Client()


def _get_variants(filepath: str) -> list:
    """Generate variants and return the list, or empty list on failure."""
    resize_result = json.loads(resize_image_variants(filepath))
    if resize_result.get("status") == "success":
        return resize_result["variants"]
    return []


def generate_image(
    prompt: str,
    style: str = "auto",
    aspect_ratio: str = "16:9",
    negative_prompt: Optional[str] = None,
    filename_hint: Optional[str] = None,
) -> str:
    """Generate an image using Imagen 3 and save it locally.

    Generates a single image based on the prompt and saves it to the
    data/images/ directory.

    The style parameter controls the visual approach:
    - "fact": Monochrome archival photograph style (for Fact-based articles)
    - "folklore": 19th century woodcut/engraving illustration style (for Folklore-based articles)
    - "auto": Let the prompt determine the style

    Args:
        prompt: Detailed English prompt describing the image to generate.
        style: Image style - "fact" (monochrome photo), "folklore" (woodcut illustration), or "auto".
        aspect_ratio: Aspect ratio - "16:9" (blog header), "1:1" (square), "9:16" (vertical).
        negative_prompt: Elements to exclude from the image.
        filename_hint: Optional hint for the filename (e.g., "boston_harbor").

    Returns:
        JSON string with the file path and generation details.
    """
    # Apply style-specific prompt modifications
    if style == "fact":
        style_prefix = (
            "Black and white archival photograph style, monochrome, "
            "high contrast, vintage silver gelatin print texture, "
            "documentary photography aesthetic. "
        )
        if not negative_prompt:
            negative_prompt = "color, modern elements, digital artifacts, cartoon, illustration"
    elif style == "folklore":
        style_prefix = (
            "19th century woodcut engraving illustration style, "
            "cross-hatching technique, sepia toned, aged paper texture, "
            "vintage newspaper illustration aesthetic. "
        )
        if not negative_prompt:
            negative_prompt = "photograph, modern elements, digital art, 3D render, color photography"
    else:
        style_prefix = ""

    full_prompt = f"{style_prefix}{prompt}"
    current_prompt = full_prompt

    # Prepare output directory
    images_dir = Path(__file__).parent.parent / "data" / "images"
    images_dir.mkdir(parents=True, exist_ok=True)

    # Generate filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    if filename_hint:
        safe_hint = "".join(c if c.isalnum() or c in "_-" else "_" for c in filename_hint[:30])
    else:
        safe_hint = "image"
    filename = f"{safe_hint}_{timestamp}.png"
    filepath = images_dir / filename

    client = _get_client()
    last_error = None
    prompt_sanitized = False

    for attempt in range(MAX_RETRIES):
        try:
            config = types.GenerateImagesConfig(
                number_of_images=1,
                aspect_ratio=aspect_ratio,
                output_mime_type="image/png",
                person_generation="DONT_ALLOW",
                safety_filter_level="BLOCK_MEDIUM_AND_ABOVE",
            )
            if negative_prompt:
                config.negative_prompt = negative_prompt

            response = client.models.generate_images(
                model="imagen-3.0-generate-002",
                prompt=current_prompt,
                config=config,
            )

            if response.generated_images:
                # Success - save image
                image = response.generated_images[0].image
                image.save(str(filepath))

                # Generate responsive variants
                variants = _get_variants(str(filepath))

                return json.dumps({
                    "status": "success",
                    "filepath": str(filepath),
                    "filename": filename,
                    "prompt_used": current_prompt,
                    "original_prompt": full_prompt,
                    "style": style,
                    "aspect_ratio": aspect_ratio,
                    "attempt": attempt + 1,
                    "prompt_sanitized": prompt_sanitized,
                    "variants": variants,
                }, ensure_ascii=False)

            # No images generated - likely safety filter
            last_error = "No images generated (filtered by safety checks)"

            # On first failure, try sanitizing the prompt
            if not prompt_sanitized:
                current_prompt = _sanitize_prompt(current_prompt)
                prompt_sanitized = True
                continue

            # Already sanitized, wait and retry
            time.sleep(RETRY_DELAY_SECONDS * (attempt + 1))

        except Exception as e:
            error_str = str(e).lower()
            last_error = str(e)

            # Check for rate limit errors
            if "resource exhausted" in error_str or "429" in error_str or "quota" in error_str:
                # Rate limit - exponential backoff
                time.sleep(RETRY_DELAY_SECONDS * (attempt + 1) * 2)
                continue

            # Check for timeout errors
            if "timeout" in error_str or "deadline" in error_str:
                # Timeout - simple retry
                time.sleep(RETRY_DELAY_SECONDS)
                continue

            # Other errors - try sanitizing prompt on first attempt
            if not prompt_sanitized:
                current_prompt = _sanitize_prompt(current_prompt)
                prompt_sanitized = True
                continue

            # Fatal error after sanitization attempt
            break

    # All retries failed - try fallback image
    if FALLBACK_IMAGE_PATH.exists():
        # Generate responsive variants from fallback
        variants = _get_variants(str(FALLBACK_IMAGE_PATH))

        return json.dumps({
            "status": "fallback",
            "filepath": str(FALLBACK_IMAGE_PATH),
            "filename": FALLBACK_IMAGE_PATH.name,
            "note": "Using fallback image due to generation failure",
            "original_prompt": full_prompt,
            "last_error": last_error,
            "attempts": MAX_RETRIES,
            "variants": variants,
        }, ensure_ascii=False)

    # No fallback available
    return json.dumps({
        "status": "error",
        "error": f"Image generation failed after {MAX_RETRIES} attempts: {last_error}",
        "prompt_used": current_prompt,
        "original_prompt": full_prompt,
        "attempts": MAX_RETRIES,
    }, ensure_ascii=False)
