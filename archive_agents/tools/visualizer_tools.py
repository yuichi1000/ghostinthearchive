"""LLM-facing tool functions for the Visualizer Agent.

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


def _get_client() -> genai.Client:
    """Get a configured genai client."""
    if os.environ.get("GOOGLE_GENAI_USE_VERTEXAI", "").upper() == "TRUE":
        return genai.Client(
            vertexai=True,
            project=os.environ.get("GOOGLE_CLOUD_PROJECT"),
            location=os.environ.get("GOOGLE_CLOUD_LOCATION", "us-central1"),
        )
    return genai.Client()


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

    try:
        client = _get_client()

        config = types.GenerateImagesConfig(
            number_of_images=1,
            aspect_ratio=aspect_ratio,
            output_mime_type="image/png",
            person_generation="DONT_ALLOW",
            safety_filter_level="BLOCK_LOW_AND_ABOVE",
        )
        if negative_prompt:
            config.negative_prompt = negative_prompt

        response = client.models.generate_images(
            model="imagen-3.0-generate-002",
            prompt=full_prompt,
            config=config,
        )

        if not response.generated_images:
            return json.dumps({
                "status": "error",
                "error": "No images generated (may have been filtered by safety checks)",
                "prompt_used": full_prompt,
            }, ensure_ascii=False)

        # Save image
        image = response.generated_images[0].image
        image.save(str(filepath))

        return json.dumps({
            "status": "success",
            "filepath": str(filepath),
            "filename": filename,
            "prompt_used": full_prompt,
            "style": style,
            "aspect_ratio": aspect_ratio,
        }, ensure_ascii=False)

    except Exception as e:
        return json.dumps({
            "status": "error",
            "error": str(e),
            "prompt_used": full_prompt,
        }, ensure_ascii=False)
