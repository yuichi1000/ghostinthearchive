"""プロダクトデザインツール

Alchemist エージェントが使用するツール:
- save_design_proposal: 構造化デザイン提案 JSON をセッション状態に保存

podcast_agents/tools/script_tools.py の save_script_outline パターンを踏襲。
"""

import json
import logging

from google.adk.tools.tool_context import ToolContext

logger = logging.getLogger(__name__)

VALID_PRODUCT_TYPES = {"tshirt", "mug"}
VALID_STYLE_REFERENCES = {"fact", "folklore"}


def save_design_proposal(
    proposal_json: str,
    tool_context: ToolContext,
) -> str:
    """構造化デザイン提案をセッション状態に保存する。

    Alchemist Agent がこのツールを呼び出し、T-シャツ・マグカップの
    デザイン提案 JSON をセッション状態に保存する。

    Args:
        proposal_json: JSON 文字列。必須フィールド:
            - products: 製品デザイン配列
              各製品: product_type ("tshirt"/"mug"), catchphrase_en, catchphrase_ja,
              color_palette, font_suggestion, composition, imagen_prompts, style_reference
        tool_context: ADK ToolContext（セッション状態アクセス用）

    Returns:
        保存結果の JSON 文字列
    """
    try:
        data = json.loads(proposal_json)
    except json.JSONDecodeError as e:
        return json.dumps(
            {"status": "error", "error": f"Invalid JSON: {e}"},
            ensure_ascii=False,
        )

    # バリデーション
    warnings: list[str] = []

    products = data.get("products")
    if not products or not isinstance(products, list):
        return json.dumps(
            {"status": "error", "error": "products array is required and must not be empty"},
            ensure_ascii=False,
        )

    for i, product in enumerate(products):
        if not isinstance(product, dict):
            warnings.append(f"products[{i}]: not a dict, skipping")
            continue

        # product_type チェック
        product_type = product.get("product_type", "")
        if product_type not in VALID_PRODUCT_TYPES:
            warnings.append(
                f"products[{i}]: invalid product_type '{product_type}', "
                f"expected one of {VALID_PRODUCT_TYPES}"
            )

        # キャッチフレーズチェック
        if not product.get("catchphrase_en", "").strip():
            warnings.append(f"products[{i}]: catchphrase_en is empty")
        if not product.get("catchphrase_ja", "").strip():
            warnings.append(f"products[{i}]: catchphrase_ja is empty")

        # color_palette チェック
        palette = product.get("color_palette")
        if not palette or not isinstance(palette, list) or len(palette) == 0:
            warnings.append(f"products[{i}]: color_palette is missing or empty")

        # imagen_prompts チェック
        imagen = product.get("imagen_prompts")
        if not imagen or not isinstance(imagen, dict):
            warnings.append(f"products[{i}]: imagen_prompts is missing or not a dict")
        elif not imagen.get("background", "").strip():
            warnings.append(f"products[{i}]: imagen_prompts.background is empty")

        # style_reference チェック
        style_ref = product.get("style_reference", "")
        if style_ref and style_ref not in VALID_STYLE_REFERENCES:
            warnings.append(
                f"products[{i}]: invalid style_reference '{style_ref}', "
                f"expected one of {VALID_STYLE_REFERENCES}"
            )

    # セッション状態に保存
    tool_context.state["structured_design_proposal"] = data

    logger.info(
        "Design proposal saved: %d products",
        len(products),
    )

    return json.dumps(
        {
            "status": "success",
            "message": "Design proposal saved to session state",
            "product_count": len(products),
            "product_types": [
                p.get("product_type", "unknown")
                for p in products
                if isinstance(p, dict)
            ],
            "warnings": warnings,
        },
        ensure_ascii=False,
    )
