"""LLM-facing tool functions for the Illustrator Agent.

Generates images using Imagen 3 and saves them to local storage.
LLM ベースのプロンプト安全書き換えと画像-記事整合性検証を含む。
"""

import json
import logging
import os
import re
import shutil
import tempfile
import time
from datetime import datetime
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

from google import genai
from google.adk.tools.tool_context import ToolContext
from google.genai import types

from .image_processing import _generate_thumbnail, resize_image_variants
from .prompt_safety import (
    _build_contextual_safe_prompt,
    _get_style_description,
    _rewrite_safe_prompt,
)

# Retry configuration
MAX_RETRIES = 3
RETRY_DELAY_SECONDS = 2

# 画像検証の設定
VALIDATION_CONFIDENCE_THRESHOLD = 0.6
VALIDATION_MODEL = "gemini-2.5-flash"

# Fallback image path
ASSETS_DIR = Path(__file__).parent.parent / "assets"
FALLBACK_IMAGE_PATH = ASSETS_DIR / "fallback_header.webp"

# Pre-generated fallback variants (heights calculated from 2816x1536 original)
FALLBACK_VARIANTS = [
    {"label": "sm", "width": 640, "height": 349, "filepath": str(ASSETS_DIR / "fallback_header_sm.webp"), "filename": "fallback_header_sm.webp"},
    {"label": "md", "width": 828, "height": 452, "filepath": str(ASSETS_DIR / "fallback_header_md.webp"), "filename": "fallback_header_md.webp"},
    {"label": "lg", "width": 1200, "height": 655, "filepath": str(ASSETS_DIR / "fallback_header_lg.webp"), "filename": "fallback_header_lg.webp"},
    {"label": "xl", "width": 1920, "height": 1047, "filepath": str(ASSETS_DIR / "fallback_header_xl.webp"), "filename": "fallback_header_xl.webp"},
]


def _get_client() -> genai.Client:
    """Get a configured genai client."""
    if os.environ.get("GOOGLE_GENAI_USE_VERTEXAI", "").upper() == "TRUE":
        return genai.Client(
            vertexai=True,
            project=os.environ.get("GOOGLE_CLOUD_PROJECT"),
            location=os.environ.get("GOOGLE_CLOUD_LOCATION", "asia-northeast1"),
        )
    return genai.Client()


def _get_variants(filepath: str) -> tuple[list, str | None]:
    """Generate variants and return (variants, error_message).

    Returns:
        Tuple of (variants_list, error_string_or_None).
    """
    resize_result = json.loads(resize_image_variants(filepath))
    if resize_result.get("status") == "success":
        return resize_result["variants"], None
    error_msg = resize_result.get("error", "Unknown error")
    logger.error(
        "WebP variant generation FAILED for %s: %s",
        filepath, error_msg,
    )
    return [], error_msg


def generate_image(
    prompt: str,
    style: str = "auto",
    region: str = "EU",
    aspect_ratio: str = "16:9",
    negative_prompt: Optional[str] = None,
    filename_hint: Optional[str] = None,
    tool_context: Optional[ToolContext] = None,
) -> str:
    """Generate an image using Imagen 3 and save it locally.

    Generates a single image based on the prompt and saves it to a
    temporary directory. The Publisher agent will clean up the files
    after uploading to Cloud Storage.

    The style parameter controls the visual approach:
    - "fact": Region-specific archival style (for Fact-based articles)
    - "folklore": Region-specific artistic style (for Folklore-based articles)
    - "auto": Let the prompt determine the style

    The region parameter selects a culture-specific art style from the style registry.
    Supported regions: US, JP, GB, NL, AU, NZ, DE, FR, ES, PT. Unknown regions fall back to EU.

    Args:
        prompt: Detailed English prompt describing the image to generate.
        style: Image style - "fact", "folklore", or "auto".
        region: ISO 3166-1 alpha-2 country code for region-specific art style (default: "EU").
        aspect_ratio: Aspect ratio - "16:9" (blog header), "1:1" (square), "9:16" (vertical).
        negative_prompt: Elements to exclude from the image.
        filename_hint: Optional hint for the filename (e.g., "boston_harbor").

    Returns:
        JSON string with the file path and generation details.
    """
    # Apply style-specific prompt modifications via style registry
    if style in ("fact", "folklore"):
        from .style_registry import get_art_style

        art_style = get_art_style(region, style)
        style_prefix = art_style.style_prefix
        if not negative_prompt:
            negative_prompt = art_style.negative_prompt
    else:
        style_prefix = ""

    full_prompt = f"{style_prefix}{prompt}"
    current_prompt = full_prompt

    # Prepare output directory (temporary; cleaned up by Publisher after upload)
    images_dir = Path(tempfile.mkdtemp(prefix="ghost_images_"))

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
    _imagen_start = time.monotonic()

    for attempt in range(MAX_RETRIES):
        try:
            config = types.GenerateImagesConfig(
                number_of_images=1,
                aspect_ratio=aspect_ratio,
                output_mime_type="image/png",
                person_generation="DONT_ALLOW",
                safety_filter_level="BLOCK_ONLY_HIGH",
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
                latency_ms = round((time.monotonic() - _imagen_start) * 1000)
                image = response.generated_images[0].image
                image.save(str(filepath))
                logger.info(
                    "画像生成成功: attempt=%d, %dms, prompt_len=%d",
                    attempt + 1, latency_ms, len(current_prompt),
                    extra={
                        "api_name": "imagen", "status": "success",
                        "attempt": attempt + 1, "latency_ms": latency_ms,
                        "prompt_length": len(current_prompt),
                        "prompt_sanitized": prompt_sanitized,
                    },
                )

                # Generate responsive variants
                variants, variant_error = _get_variants(str(filepath))

                # Generate thumbnail (400×400 center crop)
                thumbnail = _generate_thumbnail(str(filepath))

                result = {
                    "status": "success",
                    "filepath": str(filepath),
                    "filename": filename,
                    "prompt_used": current_prompt,
                    "original_prompt": full_prompt,
                    "style": style,
                    "region": region,
                    "aspect_ratio": aspect_ratio,
                    "attempt": attempt + 1,
                    "prompt_sanitized": prompt_sanitized,
                    "variants": variants,
                    "variant_error": variant_error,
                    "thumbnail": thumbnail,
                }

                # Save image metadata to session state for Publisher
                if tool_context is not None:
                    tool_context.state["image_metadata"] = result

                return json.dumps(result, ensure_ascii=False)

            # No images generated - likely safety filter
            last_error = "No images generated (filtered by safety checks)"
            logger.warning(
                "Safety filter blocked image generation (attempt %d/%d). prompt=%s",
                attempt + 1, MAX_RETRIES, current_prompt[:100],
                extra={"api_name": "imagen", "attempt": attempt + 1, "reason": "safety_filter"},
            )

            # LLM ベースのプログレッシブ・リトライ戦略:
            # attempt 0 失敗 → LLM で知的書き換え（attempt 1 用）
            # attempt 1 失敗 → 記事から安全な新コンセプト生成（attempt 2 用）
            if attempt == 0:
                current_prompt = _rewrite_safe_prompt(current_prompt, style, region)
                prompt_sanitized = True
            elif attempt == 1:
                current_prompt = _build_contextual_safe_prompt(style, region, tool_context)
                prompt_sanitized = True
            continue

        except Exception as e:
            error_str = str(e).lower()
            last_error = str(e)

            # Check for rate limit errors
            if "resource exhausted" in error_str or "429" in error_str or "quota" in error_str:
                logger.warning(
                    "Rate limit hit (attempt %d/%d): %s",
                    attempt + 1, MAX_RETRIES, last_error,
                    extra={"api_name": "imagen", "attempt": attempt + 1, "reason": "rate_limit"},
                )
                time.sleep(RETRY_DELAY_SECONDS * (attempt + 1) * 2)
                continue

            # Check for timeout errors
            if "timeout" in error_str or "deadline" in error_str:
                logger.warning(
                    "Timeout (attempt %d/%d): %s",
                    attempt + 1, MAX_RETRIES, last_error,
                )
                time.sleep(RETRY_DELAY_SECONDS)
                continue

            # Other errors
            logger.error(
                "Unexpected error (attempt %d/%d): %s",
                attempt + 1, MAX_RETRIES, last_error,
            )

            # LLM ベースのプログレッシブ・リトライ（その他エラー時も同様）
            if attempt == 0:
                current_prompt = _rewrite_safe_prompt(current_prompt, style, region)
                prompt_sanitized = True
                continue
            elif attempt == 1:
                current_prompt = _build_contextual_safe_prompt(style, region, tool_context)
                prompt_sanitized = True
                continue

            # Fatal error on last attempt
            break

    # All retries failed - try fallback image
    if FALLBACK_IMAGE_PATH.exists():
        logger.error(
            "All %d attempts failed, using fallback image. last_error=%s, original_prompt=%s",
            MAX_RETRIES, last_error, full_prompt[:200],
        )

        # 静的アセットを temp にコピーしてから返す
        # （Publisher の _upload_images_internal がリネーム＋削除するため、
        #   元の静的ファイルを保全する）
        temp_dir = Path(tempfile.mkdtemp(prefix="ghost_images_"))
        fallback_copy = temp_dir / FALLBACK_IMAGE_PATH.name
        shutil.copy2(FALLBACK_IMAGE_PATH, fallback_copy)

        variant_copies = []
        for v in FALLBACK_VARIANTS:
            src = Path(v["filepath"])
            if src.exists():
                dst = temp_dir / src.name
                shutil.copy2(src, dst)
                variant_copies.append({**v, "filepath": str(dst), "filename": src.name})
            else:
                logger.warning("Fallback variant not found: %s", src)

        # サムネイル生成（フォールバック画像から）
        fallback_thumbnail = _generate_thumbnail(str(fallback_copy))

        fallback_result = {
            "status": "fallback",
            "filepath": str(fallback_copy),
            "filename": FALLBACK_IMAGE_PATH.name,
            "note": "Using fallback image due to generation failure",
            "original_prompt": full_prompt,
            "last_error": last_error,
            "attempts": MAX_RETRIES,
            "variants": variant_copies,
            "thumbnail": fallback_thumbnail,
            "retry_suggestion": (
                "Try generating with a completely different visual concept. "
                "Focus on locations, architecture, or symbolic objects instead of the original subject. "
                "Avoid any references to people, creatures, or supernatural elements."
            ),
        }

        # Save fallback image metadata to session state for Publisher
        if tool_context is not None:
            tool_context.state["image_metadata"] = fallback_result

        return json.dumps(fallback_result, ensure_ascii=False)

    # No fallback available
    logger.error(
        "All %d attempts failed, no fallback available. last_error=%s",
        MAX_RETRIES, last_error,
    )
    return json.dumps({
        "status": "error",
        "error": f"Image generation failed after {MAX_RETRIES} attempts: {last_error}",
        "prompt_used": current_prompt,
        "original_prompt": full_prompt,
        "attempts": MAX_RETRIES,
    }, ensure_ascii=False)


def validate_image(
    image_filepath: str,
    expected_theme: str,
    style: str = "auto",
    region: str = "EU",
    tool_context: Optional[ToolContext] = None,
) -> str:
    """生成画像と記事内容の整合性を Gemini Flash で検証する。

    生成された画像が記事テーマと一致するか、時代錯誤がないか、
    スタイルが適切かをマルチモーダル LLM で評価する。
    フェイルオープン: 検証自体が失敗した場合は現画像を使用する。

    Args:
        image_filepath: 生成画像のファイルパス。
        expected_theme: 記事テーマの要約（2-5文、Illustrator LLM が作成）。
        style: 使用したスタイル — "fact" / "folklore" / "auto"。
        region: ISO 3166-1 alpha-2 国コード（地域スタイル検証用）。
        tool_context: ADK ToolContext（セッション状態への保存用）。

    Returns:
        JSON string: {"verdict": "pass"/"fail", "confidence": 0.0-1.0,
                       "feedback": "...", "suggested_focus": "..."}
                      または {"status": "error", "error": "..."} — フェイルオープン。
    """
    filepath = Path(image_filepath)
    if not filepath.exists():
        logger.warning("validate_image: ファイルが存在しない: %s", image_filepath)
        return json.dumps({
            "status": "error",
            "error": f"Image file not found: {image_filepath}",
        }, ensure_ascii=False)

    # 画像を読み込む
    try:
        from PIL import Image as PILImage
        img = PILImage.open(filepath)
        img.load()  # 画像データの検証
    except Exception as e:
        logger.warning("validate_image: 画像読み込み失敗: %s", e)
        return json.dumps({
            "status": "error",
            "error": f"Failed to load image: {e}",
        }, ensure_ascii=False)

    style_desc = _get_style_description(style, region)

    validation_prompt = f"""Evaluate whether this image is appropriate as a hero image for the following article.

Article summary: {expected_theme}
Intended style: {style_desc}
Region: {region}

Criteria:
1. THEME MATCH: Does the image relate to the article's subject (location, era, objects, atmosphere)?
2. ERA CONSISTENCY: No anachronisms (modern elements in historical setting)?
3. STYLE ADHERENCE: Does the image match the intended regional art style described above?
4. QUALITY: No obvious AI artifacts or distorted objects?
5. CULTURAL APPROPRIATENESS: Is the image culturally appropriate for the region?

Respond in JSON only: {{"verdict":"pass" or "fail", "confidence":0.0 to 1.0, "feedback":"one sentence", "suggested_focus":"if fail, what to focus on instead"}}"""

    # 最大2回試行（1回目失敗時に1回リトライ）
    max_attempts = 2
    for attempt in range(max_attempts):
        try:
            client = _get_client()
            # 画像バイトを読み込んで送信
            image_bytes = filepath.read_bytes()
            image_part = types.Part.from_bytes(
                data=image_bytes,
                mime_type=f"image/{filepath.suffix.lstrip('.').replace('jpg', 'jpeg')}",
            )
            response = client.models.generate_content(
                model=VALIDATION_MODEL,
                contents=[image_part, validation_prompt],
            )
            raw_text = response.text.strip()

            # JSON パース試行
            try:
                result = json.loads(raw_text)
            except json.JSONDecodeError:
                # 正規表現で verdict と confidence を抽出
                verdict_match = re.search(r'"verdict"\s*:\s*"(pass|fail)"', raw_text)
                confidence_match = re.search(r'"confidence"\s*:\s*([\d.]+)', raw_text)
                if verdict_match:
                    result = {
                        "verdict": verdict_match.group(1),
                        "confidence": float(confidence_match.group(1)) if confidence_match else 0.5,
                        "feedback": raw_text[:200],
                        "suggested_focus": "",
                    }
                else:
                    logger.warning(
                        "validate_image: レスポンスのパースに失敗: %s", raw_text[:200],
                    )
                    return json.dumps({
                        "status": "error",
                        "error": f"Unparseable response: {raw_text[:200]}",
                    }, ensure_ascii=False)

            # confidence が閾値未満なら verdict を fail に上書き
            confidence = float(result.get("confidence", 0))
            if confidence < VALIDATION_CONFIDENCE_THRESHOLD:
                result["verdict"] = "fail"
                if "below threshold" not in result.get("feedback", ""):
                    result["feedback"] = (
                        f"Confidence {confidence:.2f} below threshold "
                        f"{VALIDATION_CONFIDENCE_THRESHOLD}. "
                        + result.get("feedback", "")
                    )

            logger.info(
                "validate_image: verdict=%s, confidence=%.2f, feedback=%s",
                result.get("verdict"), confidence, result.get("feedback", "")[:80],
            )

            # セッション状態に保存
            if tool_context is not None:
                tool_context.state["image_validation"] = result

            return json.dumps(result, ensure_ascii=False)

        except Exception as e:
            logger.warning(
                "validate_image: API エラー (attempt %d/%d): %s",
                attempt + 1, max_attempts, e,
            )
            if attempt < max_attempts - 1:
                time.sleep(2)
                continue
            return json.dumps({
                "status": "error",
                "error": f"Validation API error: {e}",
            }, ensure_ascii=False)
