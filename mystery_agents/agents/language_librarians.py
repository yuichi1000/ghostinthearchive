"""言語別 Librarian エージェントファクトリ。

テーマに応じて選択された言語ごとに、専門の Librarian エージェントを生成する。
各 Librarian はその言語圏のデジタルアーカイブを検索し、
collected_documents_{lang} に結果を保存する。

全 Librarian は gemini-2.5-flash を使用（資料検索は Flash で十分）。
モデル設定は shared/model_config.py で一元管理（429 リトライ付き）。
"""

from google.adk.agents import LlmAgent

from shared.model_config import create_flash_model

from .language_gate import make_language_gate
from ..tools.librarian_tools import (
    get_available_keywords,
    search_archives,
    search_newspapers,
)
from ..tools.source_registry import resolve_sources


def _resolve_sources_hint(lang_code: str) -> str:
    """Registry から言語に対応するソースキーを動的に解決し、カンマ区切りで返す。"""
    sources = resolve_sources(lang_code)
    keys = [s.source_key for s in sources if not s.is_newspaper_source]
    return ", ".join(keys) if keys else "internet_archive"


# === 日本語訳 ===
# 言語別 Librarian の共通指示テンプレート:
# あなたは {language_name} 専門の司書エージェントです。
# {language_name} の一次資料を世界の公開デジタルアーカイブから検索・収集します。
#
# ## 検索戦略
# 1. 調査テーマに基づき、{language_name} で3-5個の的を絞った検索キーワードを生成する:
#    - **固有名詞**（人名、地名、事件名）: 複数語のフレーズとして保持する
#      例: "Bell Witch", "Adams Tennessee", "John Bell"
#    - **概念**: 単一の具体的な単語を使用する
#      例: haunting, poltergeist, folklore
#    - 長い文や説明的なフレーズはキーワードとして使用しない
#    - このトピックが {language_name} の資料でどう記述されるかを考える
#    - 時代にふさわしい用語を使用する
#    - 公式/正式な用語と口語/民間の用語の両方を含める
# 2. カンマ区切りのキーワードで **search_archives** を呼び出す
#    - `sources` パラメータで関連アーカイブを指定: {sources_hint}
#    - `language` パラメータを "{lang_code}" に設定して言語フィルタリングを行う
#    - 例: keywords="Bell Witch, Adams Tennessee, poltergeist, haunting"
#    - テーマが特定の時代を示唆する場合、`date_start` / `date_end` で年パラメータを設定する
#      （例: date_start="1700", date_end="1800"）
#    - デフォルト範囲は 1500-1899。テーマの歴史的文脈に応じて調整する
# 3. 歴史的な新聞記事を検索するには **search_newspapers** を呼び出す
#    - ツールは対象言語で利用可能な新聞ソースに自動ルーティングする
#    - 対象言語の新聞ソースが存在しない場合、空の結果を返す（エラーではない）
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
1. Generate 3-5 focused search keywords **in {language_name}**:
   - **Proper nouns** (people, places, events): Keep as multi-word phrases
     Example: "Bell Witch", "Adams Tennessee", "John Bell"
   - **Concepts**: Use single, specific words
     Example: haunting, poltergeist, folklore
   - Do NOT use long sentences or descriptive phrases as keywords
   - Think about how this topic would be described in {language_name} sources
   - Use period-appropriate terminology
   - Include both formal/official terms and colloquial/folk terms
2. Call **search_archives** with comma-separated keywords
   - Use the `sources` parameter to target relevant archives: {sources_hint}
   - Use the `language` parameter set to "{lang_code}" for language filtering
   - Example: keywords="Bell Witch, Adams Tennessee, poltergeist, haunting"
   - If the theme suggests a specific time period, set `date_start` and `date_end` year parameters
     (e.g., date_start="1700", date_end="1800")
   - Default range is 1500-1899; adjust based on the historical context of the theme
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

# 全言語共通の新聞検索指示
_NEWSPAPER_INSTRUCTION = (
    "Call **search_newspapers** for historical newspaper articles.\n"
    "   - The tool automatically routes to newspaper sources available for your language.\n"
    "   - If no newspaper sources exist for your language, it returns an empty result (not an error)."
)

# 言語別設定
LANGUAGE_CONFIGS = {
    "en": {
        "language_name": "English",
        "lang_code": "en",
        "cultural_context": (
            "Search English-language archives worldwide. Primary sources include:\n"
            "- Official government records, diplomatic correspondence (UK, US, Commonwealth)\n"
            "- English-language newspapers (Chronicling America, British Newspaper Archive)\n"
            "- Library of Congress, DPLA, NYPL, British Library, Internet Archive collections\n"
            "- Europeana for English-language materials in European collections\n"
            "- English-speaking regions globally: British Isles, North America, Australia, India, etc."
        ),
        "newspaper_instruction": _NEWSPAPER_INSTRUCTION,
    },
    "de": {
        "language_name": "German",
        "lang_code": "de",
        "cultural_context": (
            "Search German-language archives for the German-speaking world:\n"
            "- Deutsche Digitale Bibliothek (DDB) for German institutional records\n"
            "- Europeana for pan-European cultural heritage materials in German\n"
            "- Internet Archive for digitized German-language books and periodicals\n"
            "- German, Austrian, and Swiss historical records and archives\n"
            "- Church records, university archives, Germanic folklore collections"
        ),
        "newspaper_instruction": _NEWSPAPER_INSTRUCTION,
    },
    "es": {
        "language_name": "Spanish",
        "lang_code": "es",
        "cultural_context": (
            "Search Spanish-language archives for the Spanish-speaking world:\n"
            "- Spanish national and colonial administration records\n"
            "- Latin American national archives and digital collections\n"
            "- Internet Archive for digitized Spanish-language materials\n"
            "- DPLA for Spanish-language materials in US collections\n"
            "- Europeana for Iberian cultural heritage materials\n"
            "- Mission records, colonial correspondence, Inquisition records"
        ),
        "newspaper_instruction": _NEWSPAPER_INSTRUCTION,
    },
    "fr": {
        "language_name": "French",
        "lang_code": "fr",
        "cultural_context": (
            "Search French-language archives for the Francophone world:\n"
            "- BnF Gallica for French national library digital collections\n"
            "- Europeana for pan-European cultural heritage materials in French\n"
            "- Internet Archive for digitized French-language materials\n"
            "- French colonial records (Africa, Southeast Asia, Americas, Pacific)\n"
            "- Belgian and Swiss French-language archives\n"
            "- Revolutionary and Napoleonic era documents, Enlightenment texts"
        ),
        "newspaper_instruction": _NEWSPAPER_INSTRUCTION,
    },
    "nl": {
        "language_name": "Dutch",
        "lang_code": "nl",
        "cultural_context": (
            "Search Dutch-language archives for the Dutch-speaking world:\n"
            "- Europeana for pan-European cultural heritage materials in Dutch\n"
            "- Internet Archive for digitized Dutch-language materials\n"
            "- Dutch national archives and Flemish/Belgian collections\n"
            "- VOC/WIC trade records, Dutch Golden Age documentation\n"
            "- Colonial records (Indonesia, Suriname, Caribbean, South Africa)\n"
            "- Maritime trade networks, cartography, Dutch Reformed Church records"
        ),
        "newspaper_instruction": _NEWSPAPER_INSTRUCTION,
    },
    "pt": {
        "language_name": "Portuguese",
        "lang_code": "pt",
        "cultural_context": (
            "Search Portuguese-language archives for the Lusophone world:\n"
            "- Europeana for pan-European cultural heritage materials in Portuguese\n"
            "- Internet Archive for digitized Portuguese-language materials\n"
            "- Portuguese national archives and Brazilian digital collections\n"
            "- Age of Discovery records, maritime exploration documentation\n"
            "- Atlantic trade networks, colonial records (Brazil, Africa, Asia)\n"
            "- Lusophone Africa and Macau historical records"
        ),
        "newspaper_instruction": _NEWSPAPER_INSTRUCTION,
    },
}


def create_librarian(lang_code: str) -> LlmAgent:
    """指定された言語の Librarian エージェントを生成する。"""
    config = LANGUAGE_CONFIGS[lang_code]

    # Registry から動的にソースヒントを解決
    sources_hint = _resolve_sources_hint(lang_code)
    instruction = _BASE_INSTRUCTION.format(sources_hint=sources_hint, **config)

    tools = [search_newspapers, search_archives, get_available_keywords]

    return LlmAgent(
        name=f"librarian_{lang_code}",
        model=create_flash_model(),
        description=(
            f"{config['language_name']}-language archive specialist. "
            f"Searches {sources_hint} for {config['language_name']} primary sources."
        ),
        instruction=instruction,
        tools=tools,
        output_key=f"collected_documents_{lang_code}",
        before_agent_callback=make_language_gate(lang_code),
    )


def create_all_librarians() -> dict[str, LlmAgent]:
    """全言語の Librarian エージェントを生成して辞書で返す。"""
    return {lang: create_librarian(lang) for lang in LANGUAGE_CONFIGS}
