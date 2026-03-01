"""Translator Agent Factory - Multilingual translation

Creates translator agents for 3 target languages (ja, es, de).
Each translator maintains language-specific tone and cultural nuance.

Used in two contexts:
- Blog pipeline: ParallelAgent runs all 3 translators concurrently
  (reads creative_content / mystery_report / structured_report from session state)
- Curator pipeline: Japanese translator for theme suggestions
  (reads JSON from user message)

Output: Translation result (JSON with translated fields, no suffix)
"""

from pathlib import Path

from dotenv import load_dotenv
from google.adk.agents import LlmAgent
from google.genai import types

from shared.model_config import create_flash_model
from shared.token_tracker import create_token_tracking_callback

from .translator_instructions import BASE_TRANSLATOR_INSTRUCTION as _BASE_TRANSLATOR_INSTRUCTION

load_dotenv(Path(__file__).parent.parent / ".env")

# === 日本語訳 ===
# 各言語の翻訳ガイドライン設定
#
# ja: 学術的信頼性 + 怪異情緒、「歴史探偵 + 怪異蒐集家」
# es: 学術的荘厳さ + lo misterioso、スペイン文学ジャーナリズム
# de: 学術的精密さ + Unheimlichkeit（不気味なもの）
# === End 日本語訳 ===

TRANSLATOR_CONFIGS: dict[str, dict[str, str]] = {
    "ja": {
        "language_name": "Japanese",
        "tone": (
            "Maintain academic credibility while evoking an eerie atmosphere (怪異的情緒). "
            "Japanese equivalent of Atlas Obscura / Smithsonian Magazine readability. "
            "A hybrid style of 'historical detective' (歴史探偵) and 'collector of the uncanny' (怪異蒐集家)."
        ),
        "speculation": (
            "- 'It is said that...' → 「～と言われている」\n"
            "- 'Perhaps...' → 「おそらく～」/ 「～かもしれない」\n"
            "- 'According to legend...' → 「伝承によれば～」"
        ),
        "terminology": (
            "- Historical terms: Use standard academic Japanese expressions\n"
            "- Folklore terms: folklore → 民間伝承, legend → 伝説, myth → 神話\n"
            "- Place names: Use Japanese katakana (e.g., Boston → ボストン)\n"
            "- Person names: Keep original and supplement with katakana "
            "(e.g., Captain James → ジェームズ船長 (Captain James))"
        ),
    },
    "es": {
        "language_name": "Spanish",
        "tone": (
            "Academic solemnity infused with 'lo misterioso' — the sense of the uncanny. "
            "Follow the tradition of Spanish literary journalism (periodismo narrativo). "
            "Evoke the atmosphere of Gabriel García Márquez's non-fiction or Javier Cercas's historical investigations."
        ),
        "speculation": (
            "- 'It is said that...' → 'Se dice que...'\n"
            "- 'Perhaps...' → 'Quizás...' / 'Tal vez...'\n"
            "- 'According to legend...' → 'Según la leyenda...'"
        ),
        "terminology": (
            "- Historical terms: Use standard academic Spanish\n"
            "- Folklore terms: folklore → folclore, legend → leyenda, myth → mito\n"
            "- Place names: Use standard Spanish transliteration where applicable\n"
            "- Person names: Keep original with Spanish-style reference"
        ),
    },
    "de": {
        "language_name": "German",
        "tone": (
            "Academic precision combined with 'Unheimlichkeit' (the uncanny, per Freud). "
            "Follow the tradition of German Wissenschaftsjournalismus (science journalism) "
            "with undertones of Romantik-era mystery. Measured, precise, yet atmospheric."
        ),
        "speculation": (
            "- 'It is said that...' → 'Es heißt, dass...'\n"
            "- 'Perhaps...' → 'Vielleicht...' / 'Möglicherweise...'\n"
            "- 'According to legend...' → 'Der Legende nach...'"
        ),
        "terminology": (
            "- Historical terms: Use standard academic German\n"
            "- Folklore terms: folklore → Volkskunde, legend → Legende/Sage, myth → Mythos\n"
            "- Place names: Use German forms where they exist (e.g., Munich not München for English readers)\n"
            "- Person names: Keep original with German-style reference"
        ),
    },
}



def create_translator(target_lang: str) -> LlmAgent:
    """指定言語の Translator エージェントを生成する。

    Args:
        target_lang: 翻訳先の言語コード (ja, es, de)

    Returns:
        LlmAgent: 翻訳エージェント

    Raises:
        ValueError: サポートされていない言語コードの場合
    """
    if target_lang not in TRANSLATOR_CONFIGS:
        raise ValueError(
            f"Unsupported target language: {target_lang}. "
            f"Supported: {list(TRANSLATOR_CONFIGS.keys())}"
        )

    config = TRANSLATOR_CONFIGS[target_lang]
    instruction = _BASE_TRANSLATOR_INSTRUCTION.format(
        language_name=config["language_name"],
        tone=config["tone"],
        terminology=config["terminology"],
        speculation=config["speculation"],
    )

    return LlmAgent(
        name=f"translator_{target_lang}",
        model=create_flash_model(),
        description=(
            f"Translates English mystery articles and theme suggestions into {config['language_name']}. "
            f"Maintains historical terminology accuracy and Fact × Folklore nuance."
        ),
        instruction=instruction,
        generate_content_config=types.GenerateContentConfig(temperature=0.2),
        output_key=f"translation_result_{target_lang}",
        include_contents="none",
        after_model_callback=create_token_tracking_callback(f"translator_{target_lang}"),
    )


def create_all_translators() -> dict[str, LlmAgent]:
    """全3言語の Translator エージェントを生成する。

    Returns:
        dict[str, LlmAgent]: 言語コード → LlmAgent の辞書
    """
    return {lang: create_translator(lang) for lang in TRANSLATOR_CONFIGS}


# 後方互換: 既存コード（Curator 等）が translator_agent を参照している場合に対応
translator_agent = create_translator("ja")
