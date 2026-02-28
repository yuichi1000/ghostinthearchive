"""API ベース Librarian エージェントファクトリ。

言語ベース Librarian に代わり、API グループごとに Librarian を生成する。
各 Librarian はテーマに応じて検索言語を自律的に判断し、
collected_documents_{api_key} に結果を保存する。

後段の AggregatorAgent が全 Librarian 出力を言語別に再集約する。

全 Librarian は gemini-2.5-flash を使用（資料検索は Flash で十分）。
モデル設定は shared/model_config.py で一元管理（429 リトライ付き）。
"""

from google.adk.agents import LlmAgent
from google.genai import types

from shared.model_config import create_flash_model
from shared.token_tracker import create_token_tracking_callback

from ..tools.librarian_tools import search_archives, search_newspapers
from .librarian_instructions import BASE_INSTRUCTION as _BASE_INSTRUCTION

# ---------------------------------------------------------------------------
# API 別設定
# ---------------------------------------------------------------------------

API_CONFIGS: dict[str, dict] = {
    "us_archives": {
        "api_display_name": "US Digital Archives",
        "api_capabilities": (
            "You manage two major US digital archives plus historical newspapers:\n"
            "- **NYPL Digital Collections**: 1M+ items from New York Public Library.\n"
            "  Strong in New York City history, performing arts, and rare manuscripts.\n"
            "- **Chronicling America** (via search_newspapers): Historical US newspapers (1690-1963).\n"
            "  LOC-curated, full-text searchable, includes Spanish-language newspapers."
        ),
        "relevance_guidance": (
            "Your archives are primarily English-language and US-focused.\n"
            "Chronicling America also contains significant Spanish-language materials.\n\n"
            "**Always search** if the theme has ANY connection to:\n"
            "- United States history, culture, geography, or politics\n"
            "- English-speaking world topics (British colonial era, transatlantic events)\n"
            "- International events with US involvement or documentation\n"
            "- Broadly applicable themes (folklore, supernatural, historical mysteries)\n\n"
            "**Skip only** if the theme is exclusively about a non-US, non-English region\n"
            "with no plausible US archival record (e.g., purely local Japanese folklore\n"
            "with no Western documentation)."
        ),
        "search_strategy": (
            "1. Extract proper nouns, dates, and places from the theme → `reference_keywords`\n"
            "2. Generate creative/associative terms → `keywords`\n"
            '3. Call **search_archives** with:\n'
            '   - `sources="nypl"`, `language="en"`\n'
            '   - `reference_keywords="Bell, Adams, Tennessee, 1820"`\n'
            '   - `keywords="poltergeist, haunting, frontier spirit"`\n'
            "4. Call **search_newspapers** with the same two-phase keywords\n"
            "   - The tool searches Chronicling America automatically\n"
            "5. Date filtering is OPTIONAL. Only set `date_start` and `date_end` when\n"
            "   the theme clearly indicates a specific time period"
        ),
        "has_newspapers": True,
    },
    "europeana": {
        "api_display_name": "Europeana",
        "api_capabilities": (
            "You manage **Europeana**, the pan-European digital cultural heritage platform:\n"
            "- Aggregates 6,000+ European cultural institutions\n"
            "- 50M+ items: artworks, books, music, newspapers, maps, archives\n"
            "- Supports language filtering and country-based filtering\n"
            "- Strong for: European history, art, manuscripts, religious records\n"
            "- Materials in all major European languages: English, German, French,\n"
            "  Spanish, Dutch, Portuguese, Italian, and many more\n"
            "- Historical documents often in Latin regardless of country of origin"
        ),
        "relevance_guidance": (
            "Europeana covers all of Europe. **Always search** if the theme has\n"
            "ANY connection to:\n"
            "- European history, culture, art, or religion\n"
            "- Colonial history (European colonial powers worldwide)\n"
            "- Western civilization topics (philosophy, science, warfare)\n"
            "- Christianity, Judaism, Islam in European context\n"
            "- Maritime exploration, trade routes, diplomacy\n\n"
            "**Skip only** if the theme is exclusively about a non-European region\n"
            "with no European colonial, trade, or cultural connection."
        ),
        "search_strategy": (
            "1. Analyze the theme and determine which European languages are relevant\n"
            "   (up to 3 languages)\n"
            "2. For EACH language, split keywords into reference (proper nouns/places)\n"
            "   and exploratory (associative terms)\n"
            '3. Call **search_archives** once per language with:\n'
            '   - `sources="europeana"`, `language` set to the relevant code\n'
            "   - Example for a German theme:\n"
            '     reference_keywords="Rhein, Loreley, 1801"\n'
            '     keywords="Geisterschiff, Schiffbruch, Sage"\n'
            "   - Example for a Franco-German border theme:\n"
            '     Call 1: reference_keywords="Rhein, Elsass", keywords="Grenze, Geist", language="de"\n'
            '     Call 2: reference_keywords="Rhin, Alsace", keywords="frontière, fantôme", language="fr"\n'
            "4. Always search in the primary language of the theme's region.\n"
            "   Add additional languages when the theme spans borders or cultures.\n"
            "5. Date filtering is OPTIONAL — use only when the time period is clear"
        ),
        "has_newspapers": False,
    },
    "internet_archive": {
        "api_display_name": "Internet Archive",
        "api_capabilities": (
            "You manage the **Internet Archive** (archive.org):\n"
            "- 40M+ books and texts, plus audio, video, and web archives\n"
            "- Massive collection of digitized out-of-copyright books and periodicals\n"
            "- Materials in virtually every language\n"
            "- Strong for: obscure and rare publications, folklore collections,\n"
            "  old journals, government reports, pamphlets\n"
            "- Often hosts digitized copies of materials from other institutions"
        ),
        "relevance_guidance": (
            "Internet Archive has materials on virtually any topic.\n"
            "**Always search** — the breadth of IA's collection makes it relevant\n"
            "to almost every investigation theme.\n\n"
            "Focus your search on finding materials that complement what other\n"
            "specialized archives might have — rare books, obscure periodicals,\n"
            "and folklore collections that may not be in institutional archives."
        ),
        "search_strategy": (
            "1. Extract proper nouns/places → `reference_keywords`, creative terms → `keywords`\n"
            '2. Call **search_archives** with:\n'
            '   - `sources="internet_archive"`, `language="en"`\n'
            '   - `reference_keywords="Transylvania, Vlad, Wallachia"`\n'
            '   - `keywords="vampire folklore, superstition, undead"`\n'
            "3. If the theme is strongly connected to a non-English culture,\n"
            "   consider keywords in that language as well\n"
            "4. Date filtering is OPTIONAL"
        ),
        "has_newspapers": False,
    },
    "ndl": {
        "api_display_name": "National Diet Library (NDL Search)",
        "api_capabilities": (
            "You manage **NDL Search** (国立国会図書館サーチ):\n"
            "- Japan's national library digital search service\n"
            "- Covers books, periodicals, manuscripts, and institutional publications\n"
            "- Materials primarily in Japanese\n"
            "- Strong for: Edo/Meiji/Taisho/Showa era records, kaidan (怪談) collections,\n"
            "  yokai folklore, temple and shrine records, local histories\n"
            "- Includes government publications, academic journals, and rare manuscripts"
        ),
        "relevance_guidance": (
            "NDL is focused on Japanese-language materials.\n\n"
            "**Search** if the theme has ANY connection to:\n"
            "- Japanese history, culture, or mythology\n"
            "- East Asian supernatural traditions (yokai, yurei, kaidan)\n"
            "- Japan's interactions with the West (Perry, Meiji modernization)\n"
            "- Buddhist or Shinto religious traditions\n"
            "- Japanese colonial history (Korea, Taiwan, Manchuria)\n"
            "- Specific Japanese locations, events, or historical figures\n\n"
            "**Skip** if the theme has no plausible Japanese connection."
        ),
        "search_strategy": (
            "1. Extract proper nouns/places → `reference_keywords` in Japanese\n"
            "   Generate associative terms → `keywords` in Japanese\n"
            "   - Use appropriate kanji/hiragana for historical topics\n"
            "   - Include both modern and historical terminology\n"
            '2. Call **search_archives** with:\n'
            '   - `sources="ndl"`, `language="ja"`\n'
            '   - `reference_keywords="番町, 皿屋敷, 江戸"`\n'
            '   - `keywords="怪談, 幽霊, 心霊現象, 民間伝承"`\n'
            "3. Date filtering is OPTIONAL"
        ),
        "has_newspapers": False,
    },
    "trove": {
        "api_display_name": "Trove (National Library of Australia)",
        "api_capabilities": (
            "You manage **Trove** from the National Library of Australia:\n"
            "- Australia's comprehensive discovery service for cultural heritage\n"
            "- Digitized newspapers, books, images, maps, music, and archives\n"
            "- Materials primarily in English\n"
            "- Strong for: Australian and Oceanian history, Aboriginal culture,\n"
            "  British colonial records in the Pacific, maritime history\n"
            "- Historical newspapers from 1803 to present"
        ),
        "relevance_guidance": (
            "Trove is focused on Australia and Oceania.\n\n"
            "**Search** if the theme has ANY connection to:\n"
            "- Australian or New Zealand history and culture\n"
            "- Pacific Island nations and Oceanian traditions\n"
            "- British colonial history in the Pacific\n"
            "- Aboriginal Australian culture, Dreamtime, or sacred sites\n"
            "- Maritime history in the Pacific and Indian Ocean\n"
            "- Transportation of convicts, gold rush era\n\n"
            "**Skip** if the theme has no plausible Oceanian or Pacific connection."
        ),
        "search_strategy": (
            "1. Extract proper nouns/places → `reference_keywords`\n"
            "   Generate creative terms → `keywords`\n"
            "   - Focus on Australian/Oceanian terminology and place names\n"
            '2. Call **search_archives** with:\n'
            '   - `sources="trove"`, `language="en"`\n'
            '   - `reference_keywords="Bass Strait, Melbourne, 1852"`\n'
            '   - `keywords="ghost ship, shipwreck, colonial mystery"`\n'
            "3. Date filtering is OPTIONAL"
        ),
        "has_newspapers": False,
    },
}


def create_api_librarian(api_key: str) -> LlmAgent:
    """指定された API グループの Librarian エージェントを生成する。

    Args:
        api_key: API_CONFIGS のキー（例: "us_archives", "europeana"）

    Returns:
        LlmAgent インスタンス
    """
    config = API_CONFIGS[api_key]
    instruction = _BASE_INSTRUCTION.format(**config)
    tools = [search_archives]
    if config.get("has_newspapers"):
        tools.append(search_newspapers)

    return LlmAgent(
        name=f"librarian_{api_key}",
        model=create_flash_model(),
        description=(
            f"{config['api_display_name']} specialist librarian. "
            f"Searches {config['api_display_name']} for primary sources."
        ),
        instruction=instruction,
        tools=tools,
        output_key=f"collected_documents_{api_key}",
        generate_content_config=types.GenerateContentConfig(temperature=0.3),
        after_model_callback=create_token_tracking_callback(f"librarian_{api_key}"),
    )


def create_all_api_librarians() -> list[LlmAgent]:
    """全 API グループの Librarian エージェントをリストで返す。"""
    return [create_api_librarian(key) for key in API_CONFIGS]
