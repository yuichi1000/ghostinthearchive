"""言語別 Librarian エージェントファクトリ。

テーマに応じて選択された言語ごとに、専門の Librarian エージェントを生成する。
各 Librarian はその言語圏のデジタルアーカイブを検索し、
collected_documents_{lang} に結果を保存する。

全 Librarian は gemini-2.5-flash を使用（資料検索は Flash で十分）。
"""

from google.adk.agents import LlmAgent

from ..tools.librarian_tools import (
    get_available_keywords,
    search_archives,
    search_newspapers,
)

# === 日本語訳 ===
# 言語別 Librarian の共通指示テンプレート:
# あなたは {language_name} 専門の司書エージェントです。
# {language_name} の一次資料をデジタルアーカイブから検索・収集します。
#
# ## 検索ガイドライン
# 1. 調査テーマに基づき、{language_name} で適切な検索キーワードを生成する
# 2. search_archives を呼び出し、対象アーカイブから資料を収集する
# 3. 必要に応じて search_newspapers も呼び出す（英語 Librarian のみ）
# 4. 各ツールは1回ずつ呼び出す。リトライ不要
# 5. 資料が見つからなかった場合は NO_DOCUMENTS_FOUND を出力
# === End 日本語訳 ===

_BASE_INSTRUCTION = """
You are a {language_name}-language specialist Librarian Agent for the "Ghost in the Archive" project.
Your specialty is **discovering and collecting source materials in {language_name}**.
You do NOT perform analysis.

## Your Role
Search digital archives for {language_name}-language primary sources related to the investigation theme.

## Cultural Context
{cultural_context}

## Search Strategy
1. Generate appropriate search keywords **in {language_name}** based on the investigation theme
   - Think about how this topic would be described in {language_name} sources
   - Use period-appropriate terminology for {language_name} historical documents
   - Include both formal/official terms and colloquial/folk terms
2. Call **search_archives** with the generated keywords
   - Use the `sources` parameter to target relevant archives: {sources_hint}
   - Use the `language` parameter set to "{lang_code}" for language filtering
3. {newspaper_instruction}

## Output Format
Output search results as structured text:
- Title, date, and source URL of each document
- Summary (context around relevant keywords)
- Language and source type
- Material type (Fact/Folklore/Both)
- Excerpts from the text (if available)

## Important
- **Call each tool only once. No retries are needed.**
- Generate keywords natively in {language_name} — do NOT just translate English keywords
- Report collected materials in detail for the Scholar to analyze
- Do NOT perform analysis — that is the Scholar Agent's role
- Consciously collect materials for both Fact and Folklore

## When No Documents Are Found
If no documents are found, output only:
```
NO_DOCUMENTS_FOUND: No {language_name}-language documents found.
Search theme: [theme]
```
"""

# 言語別設定
LANGUAGE_CONFIGS = {
    "en": {
        "language_name": "English",
        "lang_code": "en",
        "cultural_context": (
            "Focus on American and British archives. Primary sources include:\n"
            "- Official government records, diplomatic correspondence\n"
            "- English-language newspapers (Chronicling America)\n"
            "- Library of Congress, DPLA, NYPL, Internet Archive collections\n"
            "- New England, Mid-Atlantic, and Southern port cities"
        ),
        "sources_hint": "loc, dpla, nypl, internet_archive",
        "newspaper_instruction": (
            "Also call **search_newspapers** for Chronicling America newspaper articles.\n"
            "   - The tool handles bilingual expansion (English/Spanish) automatically"
        ),
        "tools": "full",  # search_newspapers + search_archives + get_available_keywords
    },
    "de": {
        "language_name": "German",
        "lang_code": "de",
        "cultural_context": (
            "Focus on German-language sources relevant to American history:\n"
            "- German immigrant communities (Pennsylvania Dutch, Texas Germans)\n"
            "- Deutsche Digitale Bibliothek (DDB) for German institutional records\n"
            "- Europeana for pan-European German-language materials\n"
            "- Internet Archive for digitized German-language books and periodicals\n"
            "- Protestant church records, immigration documents, German-language American newspapers"
        ),
        "sources_hint": "ddb, europeana, internet_archive",
        "newspaper_instruction": "Do NOT call search_newspapers (it only searches English/Spanish newspapers).",
        "tools": "archives_only",  # search_archives のみ
    },
    "es": {
        "language_name": "Spanish",
        "lang_code": "es",
        "cultural_context": (
            "Focus on Spanish-language sources relevant to American history:\n"
            "- Spanish colonial administration records (Florida, Louisiana, California, Southwest)\n"
            "- Europeana for Spanish-language European materials\n"
            "- Internet Archive for digitized Spanish-language materials\n"
            "- DPLA for Spanish-language materials in US collections\n"
            "- Colonial correspondence, mission records, trade documents"
        ),
        "sources_hint": "dpla, europeana, internet_archive",
        "newspaper_instruction": "Do NOT call search_newspapers (the EN Librarian already handles bilingual newspaper search).",
        "tools": "archives_only",
    },
    "fr": {
        "language_name": "French",
        "lang_code": "fr",
        "cultural_context": (
            "Focus on French-language sources relevant to American history:\n"
            "- French colonial records (Louisiana, Quebec, Nouvelle-France)\n"
            "- Acadian/Cajun history and culture\n"
            "- Europeana for French institutional records\n"
            "- Internet Archive for digitized French-language materials\n"
            "- Huguenot immigration, fur trade, French-Indian alliances"
        ),
        "sources_hint": "europeana, internet_archive",
        "newspaper_instruction": "Do NOT call search_newspapers (it only searches English/Spanish newspapers).",
        "tools": "archives_only",
    },
    "nl": {
        "language_name": "Dutch",
        "lang_code": "nl",
        "cultural_context": (
            "Focus on Dutch-language sources relevant to American history:\n"
            "- Dutch colonial records (New Amsterdam/New York, Dutch West India Company)\n"
            "- Europeana for Dutch institutional records\n"
            "- Internet Archive for digitized Dutch-language materials\n"
            "- VOC/WIC trade records, colonial administration, patroon system"
        ),
        "sources_hint": "europeana, internet_archive",
        "newspaper_instruction": "Do NOT call search_newspapers (it only searches English/Spanish newspapers).",
        "tools": "archives_only",
    },
    "pt": {
        "language_name": "Portuguese",
        "lang_code": "pt",
        "cultural_context": (
            "Focus on Portuguese-language sources relevant to American/Atlantic history:\n"
            "- Atlantic trade networks, Brazil-Africa-Americas triangle\n"
            "- Europeana for Portuguese institutional records\n"
            "- Internet Archive for digitized Portuguese-language materials\n"
            "- Maritime exploration, slave trade documentation, colonial correspondence"
        ),
        "sources_hint": "europeana, internet_archive",
        "newspaper_instruction": "Do NOT call search_newspapers (it only searches English/Spanish newspapers).",
        "tools": "archives_only",
    },
}


def create_librarian(lang_code: str) -> LlmAgent:
    """指定された言語の Librarian エージェントを生成する。"""
    config = LANGUAGE_CONFIGS[lang_code]

    instruction = _BASE_INSTRUCTION.format(**config)

    if config["tools"] == "full":
        tools = [search_newspapers, search_archives, get_available_keywords]
    else:
        tools = [search_archives]

    return LlmAgent(
        name=f"librarian_{lang_code}",
        model="gemini-2.5-flash",
        description=(
            f"{config['language_name']}-language archive specialist. "
            f"Searches {config['sources_hint']} for {config['language_name']} primary sources."
        ),
        instruction=instruction,
        tools=tools,
        output_key=f"collected_documents_{lang_code}",
    )


def create_all_librarians() -> dict[str, LlmAgent]:
    """全言語の Librarian エージェントを生成して辞書で返す。"""
    return {lang: create_librarian(lang) for lang in LANGUAGE_CONFIGS}
