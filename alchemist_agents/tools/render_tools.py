"""レンダリングツール

AlchemistRenderer エージェントが使用するツール:
- generate_design_asset: Imagen 3 でデザインアセット画像を生成

mystery_agents/tools/illustrator_tools.py の generate_image() をラップ。
product_type から aspect_ratio を自動決定し、セッション状態に累積保存する。
生成後に rembg（U2-NET）でローカル背景透過処理する。
"""

import json
import logging
from typing import Optional

from google.adk.tools.tool_context import ToolContext

logger = logging.getLogger(__name__)

# product_type → aspect_ratio のマッピング
PRODUCT_ASPECT_RATIOS = {
    "tshirt": "1:1",
    "mug": "16:9",
}


def _remove_background(filepath: str) -> tuple[str, bool]:
    """rembg（U2-NET）でローカル背景透過処理する。

    処理フロー:
    1. rembg.remove() で前景セグメンテーション（U2-NET モデル）
    2. 透過 PNG を上書き保存
    3. 透過ピクセルが実際に存在するか検証

    エラー時は元の不透過画像パスをそのまま返す（フェイルオープン）。

    Args:
        filepath: 元画像の絶対パス。

    Returns:
        (パス, 透過成功フラグ) のタプル。成功時は (filepath, True)、失敗時は (filepath, False)。
    """
    try:
        from rembg import remove, new_session
        from PIL import Image as PILImage
        import numpy as np

        # 軽量モデル u2netp を使用（Docker ではプリダウンロード済み）
        session = new_session("u2netp")

        # 元画像を読み込み
        input_img = PILImage.open(filepath).convert("RGBA")

        # rembg で背景除去
        output_img = remove(input_img, session=session)

        # 透過 PNG を上書き保存
        output_img.save(filepath, "PNG")

        # 透過ピクセルが実際に存在するか検証
        data = np.array(output_img)
        transparent_count = int(np.sum(data[:, :, 3] == 0))
        if transparent_count == 0:
            logger.warning("背景透過: 透過ピクセルなし、背景除去は無効: %s", filepath)
            return filepath, False

        logger.info("背景透過完了: %s (透過ピクセル数: %d)", filepath, transparent_count)
        return filepath, True

    except Exception as e:
        logger.warning("背景透過処理に失敗、元画像を維持: %s — %s", filepath, e)
        return filepath, False


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
        result["filepath"], bg_removed = _remove_background(original_path)
        result["transparent_background"] = bg_removed

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
