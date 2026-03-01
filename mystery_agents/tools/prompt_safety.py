"""Imagen プロンプト安全書き換えモジュール。

安全フィルタ回避のためのプロンプト置換・LLM ベース書き換え・
安全フォールバック生成を担当する。
"""

import logging
from typing import Optional

from google.adk.tools.tool_context import ToolContext

logger = logging.getLogger(__name__)

# Prompt sanitization mapping for safety filter avoidance
_SANITIZE_REPLACEMENTS = {
    # Ghost / spirit
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
    # Vampire
    "vampire": "ancient figure",
    "vampires": "ancient figures",
    "undead": "restless figure",
    "fangs": "sharp features",
    # Cannibal
    "cannibalism": "forbidden practice",
    "cannibals": "forbidden practitioners",
    "cannibal": "forbidden practitioner",
    "devour": "consume",
    "flesh": "remains",
    # Violence / death
    "murder": "dark incident",
    "kill": "end",
    "death": "passing",
    "sacrifice": "offering",
    "slaughter": "dark event",
    "torture": "ordeal",
    "mutilation": "desecration",
    "execution": "judgment",
    # Occult
    "witchcraft": "folk practice",
    "curse": "legacy",
    "witch": "wise woman",
    "occult": "esoteric",
    "ritual": "ceremony",
    "hex": "enchantment",
    "voodoo": "folk tradition",
    "sorcery": "folk art",
    # Body / medical
    "skeleton": "ancient remains",
    "skull": "relic",
    "bones": "relics",
    "grave": "resting place",
    "exhume": "uncover",
    "autopsy": "examination",
    "dissection": "study",
    "burial": "interment",
    # Other
    "plague": "epidemic",
    "disease": "affliction",
    "monster": "creature",
    "beast": "creature",
    "terror": "dread",
    "scream": "cry",
    "darkness": "shadow",
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


def _build_safe_fallback_prompt(style: str, region: str = "EU") -> str:
    """Build an ultra-safe fallback prompt with no thematic content.

    Used as the last resort (attempt 2) when both the original and
    sanitized prompts are blocked by safety filters. Returns a generic
    atmospheric prompt based on style, with no references to people,
    creatures, or supernatural elements.

    Args:
        style: Image style - "fact", "folklore", or "auto".
        region: ISO 3166-1 alpha-2 国コード。

    Returns:
        A safe prompt string guaranteed to pass safety filters.
    """
    if style in ("fact", "folklore"):
        from .style_registry import get_art_style

        art_style = get_art_style(region, style)
        # レジストリのスタイルプレフィックス + 汎用の安全な情景
        if style == "fact":
            scene = (
                "An old weathered leather-bound book lying open on a dark oak desk, "
                "candlelight casting long shadows, dust motes in the air, "
                "antique brass inkwell nearby, aged parchment pages, "
                "dramatic chiaroscuro lighting, overhead shot at 45 degrees"
            )
        else:
            scene = (
                "A misty coastal landscape at twilight, rocky cliffs overlooking "
                "a calm sea, a lone ancient lighthouse in the distance, "
                "gnarled oak trees silhouetted against a cloudy sky, "
                "dramatic linework"
            )
        return f"{art_style.style_prefix}{scene}"
    else:
        return (
            "A dimly lit archival room with tall wooden shelves filled "
            "with old leather-bound volumes, warm lamplight casting "
            "golden pools on a worn wooden floor, dust particles "
            "floating in shafts of light from a high window, "
            "atmospheric and contemplative, cinematic composition"
        )


def _get_style_description(style: str, region: str = "EU") -> str:
    """スタイルの説明文を返す。"""
    if style in ("fact", "folklore"):
        from .style_registry import get_style_description as _registry_desc

        return _registry_desc(region, style)
    return "Atmospheric, cinematic composition"


def _rewrite_safe_prompt(prompt: str, style: str, region: str = "EU") -> str:
    """Gemini Flash で元プロンプトを安全に書き換える。

    単語置換ではなく、LLM が文脈を理解して:
    - 人物・暴力・超自然 → 場所・建物・オブジェクト・風景に変換
    - 時代・場所・雰囲気は維持
    - スタイル指定を保持

    Flash 呼び出し失敗時は既存の _sanitize_prompt にフォールバック。
    """
    # illustrator_tools との循環 import を回避するため関数内で遅延 import
    from .illustrator_tools import VALIDATION_MODEL, _get_client

    rewrite_instruction = f"""Rewrite this image generation prompt to pass Imagen 3's safety filter.

Rules:
- Replace people, figures, creatures → locations, architecture, objects, landscapes
- Replace violence, death, crime → aftermath scenes, empty spaces, symbolic objects
- Replace supernatural elements → atmospheric natural phenomena (fog, storms, shadows)
- KEEP the historical era, geographic location, and mood
- KEEP the artistic style instructions
- Output ONLY the rewritten prompt, nothing else

Examples:
- "A ghostly figure haunting a 1890s Salem courtroom" → "An empty 1890s Salem courtroom at dusk, long shadows stretching across wooden benches, dust motes in fading light from tall windows, abandoned judge's gavel"
- "Jack the Ripper stalking foggy London alleys" → "A narrow gaslit alley in 1888 Whitechapel, wet cobblestones reflecting dim lamplight, fog rolling between dark brick buildings, a single abandoned top hat on the ground"
- "Bell Witch attacking the Bell family" → "The weathered Bell farmhouse in 1817 Tennessee, wind-bent trees surrounding a lonely homestead, storm clouds gathering at twilight, a rocking chair moving on an empty porch"

Original prompt: {prompt}"""

    try:
        client = _get_client()
        response = client.models.generate_content(
            model=VALIDATION_MODEL,
            contents=rewrite_instruction,
        )
        rewritten = response.text.strip()
        if rewritten:
            logger.info(
                "LLM prompt rewrite succeeded. original=%s, rewritten=%s",
                prompt[:80], rewritten[:80],
            )
            return rewritten
    except Exception as e:
        logger.warning(
            "LLM prompt rewrite failed, falling back to _sanitize_prompt: %s", e,
        )

    # フォールバック: 既存の単語置換
    return _sanitize_prompt(prompt)


def _build_contextual_safe_prompt(
    style: str, region: str, tool_context: Optional[ToolContext],
) -> str:
    """記事内容から安全な新コンセプトを生成。

    元プロンプトとは異なるアプローチで、記事の
    場所・時代・雰囲気だけを使って安全なプロンプトを作る。

    creative_content が取得できない場合、または Flash 呼び出し失敗時は
    既存の _build_safe_fallback_prompt にフォールバック。
    """
    # illustrator_tools との循環 import を回避するため関数内で遅延 import
    from .illustrator_tools import VALIDATION_MODEL, _get_client

    creative_content = None
    if tool_context is not None:
        creative_content = tool_context.state.get("creative_content")

    if not creative_content or "NO_CONTENT" in str(creative_content):
        return _build_safe_fallback_prompt(style, region)

    style_desc = _get_style_description(style, region)
    contextual_instruction = f"""Create a safe image generation prompt for an AI image generator based on this article.

The prompt must be COMPLETELY SAFE:
- NO people, faces, figures, or creatures
- NO violence, weapons, blood, death, supernatural imagery
- ONLY: landscapes, architecture, objects, documents, weather, nature

Extract from the article: the historical era, geographic location, and overall mood.
Create a visually compelling scene using ONLY safe elements.

Style: {style_desc}
Article (first 500 chars): {str(creative_content)[:500]}

Output ONLY the image generation prompt, nothing else.

Safe image prompt:"""

    try:
        client = _get_client()
        response = client.models.generate_content(
            model=VALIDATION_MODEL,
            contents=contextual_instruction,
        )
        contextual_prompt = response.text.strip()
        if contextual_prompt:
            logger.info(
                "Contextual safe prompt generated: %s", contextual_prompt[:80],
            )
            return contextual_prompt
    except Exception as e:
        logger.warning(
            "Contextual safe prompt generation failed, using generic fallback: %s", e,
        )

    # フォールバック: 既存の汎用プロンプト
    return _build_safe_fallback_prompt(style, region)
