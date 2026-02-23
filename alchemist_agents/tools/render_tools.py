"""レンダリングツール

AlchemistRenderer エージェントが使用するツール:
- generate_design_asset: Imagen 3 でデザインアセット画像を生成

mystery_agents/tools/illustrator_tools.py の generate_image() をラップ。
product_type から aspect_ratio を自動決定し、セッション状態に累積保存する。
生成後に Imagen Edit API + PIL クロマキーで背景を透過処理する。
"""

import json
import logging
import os
from typing import Optional

from google.adk.tools.tool_context import ToolContext

logger = logging.getLogger(__name__)

# product_type → aspect_ratio のマッピング
PRODUCT_ASPECT_RATIOS = {
    "tshirt": "1:1",
    "mug": "16:9",
}


def _remove_background(filepath: str) -> str:
    """Imagen Edit API でマゼンタ背景置換 → PIL クロマキーで透過 PNG に変換する。

    処理フロー:
    1. Imagen Edit API (MASK_MODE_BACKGROUND + EDIT_MODE_BGSWAP) で背景をマゼンタに置換
    2. PIL で マゼンタ (#FF00FF) ピクセルを透明化（閾値処理でアンチエイリアス保全）
    3. 透過 PNG を上書き保存

    エラー時は元の不透過画像パスをそのまま返す（フェイルオープン）。

    Args:
        filepath: 元画像の絶対パス。

    Returns:
        透過 PNG のパス（成功時は同じパス、失敗時も同じパス）。
    """
    try:
        from google import genai
        from google.genai import types
        from PIL import Image as PILImage
        import numpy as np

        # genai クライアント取得（illustrator_tools と同じロジック）
        if os.environ.get("GOOGLE_GENAI_USE_VERTEXAI", "").upper() == "TRUE":
            client = genai.Client(
                vertexai=True,
                project=os.environ.get("GOOGLE_CLOUD_PROJECT"),
                location=os.environ.get("GOOGLE_CLOUD_LOCATION", "asia-northeast1"),
            )
        else:
            client = genai.Client()

        # 元画像を読み込み
        with open(filepath, "rb") as f:
            image_bytes = f.read()

        raw_ref = types.RawReferenceImage(
            reference_image=types.Image(
                image_bytes=image_bytes,
                mime_type="image/png",
            ),
            reference_id=0,
        )

        mask_ref = types.MaskReferenceImage(
            reference_id=1,
            config=types.MaskReferenceConfig(
                mask_mode="MASK_MODE_BACKGROUND",
                mask_dilation=0.0,
            ),
        )

        # Imagen Edit API で背景をマゼンタに置換
        response = client.models.edit_image(
            model="imagen-3.0-capability-001",
            prompt="solid pure magenta #FF00FF background, uniform flat color",
            reference_images=[raw_ref, mask_ref],
            config=types.EditImageConfig(
                edit_mode="EDIT_MODE_BGSWAP",
            ),
        )

        if not response.generated_images:
            logger.warning("背景置換: 生成画像なし、元画像を維持: %s", filepath)
            return filepath

        # 生成画像を取得
        edited_bytes = response.generated_images[0].image.image_bytes

        # PIL でマゼンタ → 透明に変換
        import io
        img = PILImage.open(io.BytesIO(edited_bytes)).convert("RGBA")
        data = np.array(img)

        # マゼンタ (#FF00FF) の許容範囲検出（アンチエイリアス対応）
        r, g, b = data[:, :, 0], data[:, :, 1], data[:, :, 2]
        magenta_mask = (r > 200) & (g < 50) & (b > 200)

        # 透明化
        data[magenta_mask, 3] = 0
        result = PILImage.fromarray(data)
        result.save(filepath, "PNG")

        logger.info("背景透過完了: %s", filepath)
        return filepath

    except Exception as e:
        logger.warning("背景透過処理に失敗、元画像を維持: %s — %s", filepath, e)
        return filepath


def generate_design_asset(
    prompt: str,
    product_type: str,
    asset_layer: str = "background",
    style: str = "auto",
    region: str = "EU",
    negative_prompt: Optional[str] = None,
    tool_context: Optional[ToolContext] = None,
) -> str:
    """Imagen 3 でデザインアセット画像を生成する。

    mystery_agents/tools/illustrator_tools.py の generate_image() をラップし、
    product_type に基づいて aspect_ratio を自動決定する。
    生成結果を tool_context.state["design_assets"] に累積保存する。

    Args:
        prompt: 画像生成プロンプト（英語）。
        product_type: 製品タイプ — "tshirt" (1:1) / "mug" (16:9)。
        asset_layer: アセットレイヤー — "background" / "decorative"。
        style: 画像スタイル — "fact" / "folklore" / "auto"。
        region: ISO 3166-1 alpha-2 国コード（デフォルト: "EU"）。
        negative_prompt: 除外要素。
        tool_context: ADK ToolContext。

    Returns:
        JSON string with the file path and generation details.
    """
    # aspect_ratio を product_type から自動決定
    aspect_ratio = PRODUCT_ASPECT_RATIOS.get(product_type, "1:1")

    # デフォルト negative_prompt を設定
    if not negative_prompt:
        negative_prompt = "people, faces, text, letters, words, typography, watermark"

    # ファイル名ヒントを構成
    filename_hint = f"merch_{product_type}_{asset_layer}"

    # Illustrator の generate_image を呼び出し
    try:
        from mystery_agents.tools.illustrator_tools import generate_image

        result_json = generate_image(
            prompt=prompt,
            style=style,
            region=region,
            aspect_ratio=aspect_ratio,
            negative_prompt=negative_prompt,
            filename_hint=filename_hint,
            tool_context=None,  # image_metadata の上書きを防ぐ
        )
    except Exception as e:
        logger.error("generate_image failed: %s", e)
        return json.dumps({
            "status": "error",
            "error": f"Image generation failed: {e}",
            "product_type": product_type,
            "asset_layer": asset_layer,
        }, ensure_ascii=False)

    # 結果をパース
    try:
        result = json.loads(result_json)
    except json.JSONDecodeError:
        return result_json

    # メタデータを付加
    result["product_type"] = product_type
    result["asset_layer"] = asset_layer
    result["aspect_ratio"] = aspect_ratio

    # 背景透過処理（生成成功時のみ）
    if result.get("status") == "success" and result.get("filepath"):
        original_path = result["filepath"]
        result["filepath"] = _remove_background(original_path)
        result["transparent_background"] = True

    # セッション状態に累積保存
    if tool_context is not None:
        if "design_assets" not in tool_context.state:
            tool_context.state["design_assets"] = []

        asset_entry = {
            "filepath": result.get("filepath", ""),
            "product_type": product_type,
            "layer": asset_layer,
            "aspect_ratio": aspect_ratio,
            "status": result.get("status", "error"),
        }
        tool_context.state["design_assets"].append(asset_entry)

    logger.info(
        "Design asset generated: %s/%s (status=%s)",
        product_type, asset_layer, result.get("status", "unknown"),
    )

    return json.dumps(result, ensure_ascii=False)
