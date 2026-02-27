"""言語別 Scholar エージェントファクトリ。

各言語圏の視点で資料を分析する Scholar エージェントを生成する。
各 Scholar は自言語の資料 + 英語資料の両方を参照可能。
分析結果は英語で出力（Armchair Polymath が統合するため）。

mode="analysis" で分析モード、mode="debate" で討論モードのエージェントを生成する。
同じ SCHOLAR_CONFIGS を共有し、文化的視点は統一される。

2層構造:
- Named Scholar（EN, DE, JA, FR, ES, IT）: 専用の文化的視点を持つ
- Multilingual Scholar: Named 以外の言語をまとめて横断分析する

注意: save_structured_report は呼び出さない（Armchair Polymath が統合後に呼び出す）。
"""

from google.adk.agents import LlmAgent

from shared.language_names import get_language_name
from shared.model_config import create_pro_model

from ..tools.debate_tools import append_to_whiteboard
from .language_gate import make_debate_gate
from .scholar_instructions import (
    BASE_SCHOLAR_DEBATE_INSTRUCTION as _BASE_SCHOLAR_DEBATE_INSTRUCTION,
    BASE_SCHOLAR_INSTRUCTION as _BASE_SCHOLAR_INSTRUCTION,
    DYNAMIC_DEBATE_INSTRUCTION as _DYNAMIC_DEBATE_INSTRUCTION,
    MULTILINGUAL_ANALYSIS_INSTRUCTION as _MULTILINGUAL_ANALYSIS_INSTRUCTION,
    MULTILINGUAL_DEBATE_INSTRUCTION as _MULTILINGUAL_DEBATE_INSTRUCTION,
)

SCHOLAR_CONFIGS = {
    "en": {
        "language_name": "English",
        "lang_code": "en",
        "cultural_perspective": (
            "You bring the perspective of English-language historical scholarship:\n"
            "- Official government records, diplomatic correspondence (UK, US, Commonwealth)\n"
            "- English-language press narratives and their biases across eras and regions\n"
            "- The Anglo-American historiographic tradition and its blind spots\n"
            "- Protestant and Enlightenment cultural frameworks and their influence on record-keeping\n"
            "- Consider whose voices are centered and whose are marginalized in English sources"
        ),
    },
    "de": {
        "language_name": "German",
        "lang_code": "de",
        "cultural_perspective": (
            "You bring the perspective of German-language cultural and intellectual history:\n"
            "- Germanic historiographic traditions (Ranke, Historismus, Quellenkritik)\n"
            "- Protestant Reformation heritage and its influence on documentation\n"
            "- German, Austrian, and Swiss archival traditions\n"
            "- Heimat culture, Vereinswesen (club culture), and their documentation traditions\n"
            "- German folk traditions (Märchen, Sagen) and Romantic-era folklore studies\n"
            "- Central European perspectives on cross-cultural contact and migration"
        ),
    },
    "es": {
        "language_name": "Spanish",
        "lang_code": "es",
        "cultural_perspective": (
            "You bring the perspective of Spanish and Latin American cultural history:\n"
            "- Spanish imperial administration and its record-keeping practices\n"
            "- Latin American independence movements and their historiography\n"
            "- Catholic mission records, Inquisition documentation, and their cultural context\n"
            "- Indigenous-Spanish cultural contact and mestizo traditions\n"
            "- La Leyenda Negra vs. historical reality of Spanish colonialism\n"
            "- Folk Catholicism and syncretic religious practices across the Hispanic world"
        ),
    },
    "fr": {
        "language_name": "French",
        "lang_code": "fr",
        "cultural_perspective": (
            "You bring the perspective of Francophone cultural and intellectual history:\n"
            "- French colonial administration across Africa, Asia, Americas, and the Pacific\n"
            "- Enlightenment philosophy and its global influence\n"
            "- French Revolutionary and Napoleonic era documentation\n"
            "- Francophone oral traditions and ethnographic studies\n"
            "- Annales school historiography and mentalités approach\n"
            "- Creole cultures and syncretic traditions in the Francophone world"
        ),
    },
    "nl": {
        "language_name": "Dutch",
        "lang_code": "nl",
        "cultural_perspective": (
            "You bring the perspective of Dutch and Flemish commercial and colonial history:\n"
            "- Dutch Golden Age documentation and its commercial worldview\n"
            "- VOC/WIC records and the Dutch maritime trading empire\n"
            "- Dutch Reformed Church records and community documentation\n"
            "- Colonial administration records (Indonesia, Suriname, Caribbean, South Africa)\n"
            "- Dutch cartographic and scientific traditions\n"
            "- Flemish/Belgian perspectives and their distinct archival traditions"
        ),
    },
    "pt": {
        "language_name": "Portuguese",
        "lang_code": "pt",
        "cultural_perspective": (
            "You bring the perspective of Portuguese and Lusophone world history:\n"
            "- Portuguese Age of Discovery and maritime exploration records\n"
            "- Atlantic trade networks and their documentation\n"
            "- Brazilian colonial and imperial history\n"
            "- Lusophone Africa (Angola, Mozambique, Cape Verde) and Macau records\n"
            "- Sephardic Jewish communities and their diaspora narratives\n"
            "- Portuguese influence on global maritime terminology and navigation records"
        ),
    },
    "ja": {
        "language_name": "Japanese",
        "lang_code": "ja",
        "cultural_perspective": (
            "You bring the perspective of Japanese historical and cultural scholarship:\n"
            "- Kokugaku (国学) and Kangaku (漢学) intellectual traditions\n"
            "- Domain feudal records (藩政記録) and temple/shrine registers (寺社台帳)\n"
            "- Kaidan research (怪談研究) from Edo period to modern folkloristics\n"
            "- Buddhist and Shinto cosmological frameworks and their influence on record-keeping\n"
            "- Meiji modernization and the systematic rewriting of pre-modern narratives\n"
            "- Japanese ethnographic traditions (柳田国男, 折口信夫) and their methodologies"
        ),
    },
    "it": {
        "language_name": "Italian",
        "lang_code": "it",
        "cultural_perspective": (
            "You bring the perspective of Italian cultural and intellectual history:\n"
            "- Italian Microhistory tradition (Ginzburg, Levi) and its focus on marginalized voices\n"
            "- Vatican and papal archives — the world's oldest continuous diplomatic records\n"
            "- Mediterranean folk traditions, witchcraft trials (benandanti), and popular religion\n"
            "- Renaissance humanism and its transformation of record-keeping practices\n"
            "- Italian city-state archives (Venice, Florence, Genoa) and their commercial documentation\n"
            "- Southern Italian and Sicilian folk traditions, secret societies, and oral history"
        ),
    },
}

# Named Scholar: 専用の文化的視点を持つ言語（各々が固有の Scholar エージェント）
NAMED_SCHOLAR_LANGUAGES = {"en", "de", "ja", "fr", "es", "it"}


def get_scholar_config(lang_code: str) -> dict[str, str]:
    """SCHOLAR_CONFIGS にあればそれを返し、なければ汎用テンプレートで動的生成する。

    Args:
        lang_code: ISO 639-1 言語コード

    Returns:
        language_name, lang_code, cultural_perspective を含む dict
    """
    if lang_code in SCHOLAR_CONFIGS:
        return SCHOLAR_CONFIGS[lang_code]
    lang_name = get_language_name(lang_code)
    return {
        "language_name": lang_name,
        "lang_code": lang_code,
        "cultural_perspective": (
            f"You bring the perspective of {lang_name}-language scholarship:\n"
            f"- Analyze how {lang_name}-language sources frame and document the theme\n"
            f"- Identify information unique to {lang_name} records that other languages miss\n"
            f"- Consider the historiographic traditions and archival practices of "
            f"{lang_name}-speaking communities\n"
            f"- Note how translation and cultural context affect the interpretation of sources"
        ),
    }


def create_scholar(
    lang_code: str,
    mode: str = "analysis",
    active_langs: list[str] | None = None,
) -> LlmAgent:
    """指定された言語の Scholar エージェントを生成する。

    Args:
        lang_code: 言語コード（en, de, es, fr, nl, pt, ja, it 等）
        mode: "analysis"（分析モード）または "debate"（討論モード）
        active_langs: 討論参加言語のリスト（DynamicScholarBlock から指定）。
            指定された場合、討論 instruction に参加言語のみ記載し、
            before_agent_callback を省略する（DynamicScholarBlock がゲートを担当）。
    """
    config = get_scholar_config(lang_code)

    if mode == "analysis":
        instruction = _BASE_SCHOLAR_INSTRUCTION.format(**config)
        return LlmAgent(
            name=f"scholar_{lang_code}",
            model=create_pro_model(),
            description=(
                f"Analyzes materials from the {config['language_name']} cultural perspective. "
                f"Identifies anomalies and discrepancies through interdisciplinary analysis "
                f"of {config['language_name']}-language sources."
            ),
            instruction=instruction,
            tools=[],  # save_structured_report は呼び出さない
            output_key=f"scholar_analysis_{lang_code}",
        )
    elif mode == "debate":
        if active_langs:
            # 動的討論: 参加言語のみ instruction に含める（肥大化防止）
            lang_references = "\n".join(
                f"- {{scholar_analysis_{lang}}}: "
                f"{get_scholar_config(lang)['language_name']} cultural perspective analysis"
                for lang in active_langs
                if lang != lang_code
            )
            instruction = _DYNAMIC_DEBATE_INSTRUCTION.format(
                language_name=config["language_name"],
                cultural_perspective=config["cultural_perspective"],
                language_references=lang_references,
            )
            return LlmAgent(
                name=f"scholar_{lang_code}_debate",
                model=create_pro_model(),
                description=(
                    f"Debates from the {config['language_name']} cultural perspective. "
                    f"Challenges, corroborates, and synthesizes findings from other Scholars "
                    f"using the shared debate whiteboard."
                ),
                instruction=instruction,
                tools=[append_to_whiteboard],
                # DynamicScholarBlock がゲートを担当するため callback 不要
            )
        else:
            # 静的討論（後方互換: LoopAgent ベースのパイプライン用）
            instruction = _BASE_SCHOLAR_DEBATE_INSTRUCTION.format(
                language_name=config["language_name"],
                cultural_perspective=config["cultural_perspective"],
            )
            return LlmAgent(
                name=f"scholar_{lang_code}_debate",
                model=create_pro_model(),
                description=(
                    f"Debates from the {config['language_name']} cultural perspective. "
                    f"Challenges, corroborates, and synthesizes findings from other Scholars "
                    f"using the shared debate whiteboard."
                ),
                instruction=instruction,
                tools=[append_to_whiteboard],
                before_agent_callback=make_debate_gate(lang_code),
            )
    else:
        raise ValueError(f"Unknown mode: {mode!r}. Use 'analysis' or 'debate'.")


def create_all_scholars(mode: str = "analysis") -> dict[str, LlmAgent]:
    """全言語の Scholar エージェントを生成して辞書で返す。

    Args:
        mode: "analysis"（分析モード）または "debate"（討論モード）
    """
    return {lang: create_scholar(lang, mode) for lang in SCHOLAR_CONFIGS}


def create_multilingual_scholar(
    languages: list[str],
    mode: str = "analysis",
    active_named_langs: list[str] | None = None,
) -> LlmAgent:
    """複数言語をまとめて分析する Multilingual Scholar を生成する。

    Args:
        languages: 対象言語コードのリスト（例: ["nl", "pt", "pl"]）
        mode: "analysis" または "debate"
        active_named_langs: 討論時に参照する Named Scholar の言語リスト
    """
    lang_names = [get_language_name(lang) for lang in languages]
    language_list = "\n".join(f"- {get_language_name(lang)} ({lang})" for lang in languages)
    language_list_short = ", ".join(lang_names)

    if mode == "analysis":
        # 各言語の collected_documents 参照を動的構築
        doc_references = "\n".join(
            f"- {{collected_documents_{lang}}}: Materials collected in {get_language_name(lang)}"
            for lang in languages
        )
        instruction = _MULTILINGUAL_ANALYSIS_INSTRUCTION.format(
            language_list=language_list,
            language_list_short=language_list_short,
            document_references=doc_references,
        )
        return LlmAgent(
            name="scholar_multilingual",
            model=create_pro_model(),
            description=(
                f"Multilingual Scholar analyzing peripheral language sources "
                f"({language_list_short}). Cross-compares smaller language traditions "
                f"to discover patterns invisible to single-language analysis."
            ),
            instruction=instruction,
            tools=[],
            output_key="scholar_analysis_multilingual",
        )
    elif mode == "debate":
        # Named Scholar の分析参照を動的構築
        named_langs = active_named_langs or []
        named_refs = "\n".join(
            f"- {{scholar_analysis_{lang}}}: "
            f"{get_scholar_config(lang)['language_name']} cultural perspective analysis"
            for lang in named_langs
        )
        instruction = _MULTILINGUAL_DEBATE_INSTRUCTION.format(
            language_list_short=language_list_short,
            named_analysis_references=named_refs,
        )
        return LlmAgent(
            name="scholar_multilingual_debate",
            model=create_pro_model(),
            description=(
                f"Multilingual Scholar debating from peripheral perspectives "
                f"({language_list_short}). Challenges and enriches Named Scholar analyses."
            ),
            instruction=instruction,
            tools=[append_to_whiteboard],
        )
    else:
        raise ValueError(f"Unknown mode: {mode!r}. Use 'analysis' or 'debate'.")
