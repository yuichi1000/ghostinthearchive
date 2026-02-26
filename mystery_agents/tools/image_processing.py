"""画像リサイズ・サムネイル生成モジュール。

レスポンシブ WebP バリアント生成とサムネイルクロップを担当する。
"""

import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

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


def _generate_thumbnail(source_path: str) -> dict | None:
    """16:9 画像から 400×400 の中央クロップサムネイルを生成する。

    Args:
        source_path: ソース画像のパス。

    Returns:
        サムネイルの情報 dict、または生成失敗時は None。
    """
    src = Path(source_path)
    if not src.exists():
        logger.warning("_generate_thumbnail: ソースが見つからない: %s", source_path)
        return None

    try:
        from PIL import Image as PILImage

        with PILImage.open(src) as img:
            w, h = img.size

            # 中央正方形クロップ
            side = min(w, h)
            left = (w - side) // 2
            top = (h - side) // 2
            cropped = img.crop((left, top, left + side, top + side))

            # 400×400 にリサイズ
            thumb = cropped.resize((400, 400), PILImage.LANCZOS)

            out_name = f"{src.stem}_thumb.webp"
            out_path = src.parent / out_name
            thumb.save(str(out_path), "WEBP", quality=WEBP_QUALITY)

            return {
                "filepath": str(out_path),
                "filename": out_name,
                "width": 400,
                "height": 400,
            }
    except Exception as e:
        logger.warning("_generate_thumbnail: サムネイル生成失敗: %s", e)
        return None
