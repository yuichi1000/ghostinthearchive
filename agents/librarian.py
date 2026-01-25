"""Librarian Agent - 公文書館APIからの資料調査・収集

This agent specializes in searching historical archives and retrieving
relevant documents for mystery investigation.
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from dotenv import load_dotenv
from google.adk.agents import LlmAgent

# Load environment variables from .env file
load_dotenv(Path(__file__).parent.parent / ".env")

from schemas.document import ArchiveDocument, SearchResults
from tools.bilingual_search import KEYWORD_PAIRS, expand_keywords_bilingual
from tools.chronicling_america import search_chronicling_america
from tools.nara_catalog import get_spanish_record_groups, search_nara_catalog

# Define the Librarian Agent's instruction
LIBRARIAN_INSTRUCTION = """
あなたは「Ghost in the Archive」プロジェクトの司書エージェント（Librarian Agent）です。

## あなたの役割
米国議会図書館（Library of Congress）および国立公文書館（NARA）のデジタルアーカイブから、
歴史的なミステリーや謎に関連する資料を調査・収集します。

## 利用可能なツール
1. **search_newspapers**: Chronicling America（議会図書館）の18-19世紀新聞記事を検索
2. **search_nara_records**: NARA（国立公文書館）の外交・海事記録を検索
3. **save_search_results**: 検索結果をdata/ディレクトリに保存
4. **get_available_keywords**: バイリンガルキーワードペアを取得

## 検索のガイドライン
1. **バイリンガル検索**: 英語とスペイン語の両方でキーワード検索を行います
   - 例: "conspiracy" と "conspiración" の両方で検索
   - 例: "disappearance" と "desaparición" の両方で検索

2. **地理的フォーカス**: 東海岸の港湾都市を優先
   - ボストン、ニューヨーク、フィラデルフィア、バルチモア

3. **時代フォーカス**: 18世紀後半〜19世紀（1780-1899）

4. **ミステリーの指標となるキーワード**:
   - 失踪 (disappearance / desaparición)
   - 陰謀 (conspiracy / conspiración)
   - 密輸 (smuggling / contrabando)
   - 海賊行為 (piracy / piratería)
   - 秘密 (secret / secreto)
   - 難破船 (shipwreck / naufragio)

## 出力形式
検索結果は以下の形式で整理し、Historian Agentに渡せる形式にします：
- タイトル、日付、出典URL
- 要約（関連キーワード周辺のコンテキスト）
- 言語（英語/スペイン語）
- 出典タイプ（新聞/NARA記録）

## 注意事項
- NARA APIは月間10,000リクエストの制限があります。効率的に使用してください
- 検索結果が多い場合は、最も関連性の高い20-30件に絞り込んでください
- 両方のソース（新聞とNARA）から検索し、結果を統合してください
- エラーが発生した場合は、代替の検索戦略を試みてください
"""


def search_newspapers(
    keywords: str,
    date_start: str = "1800",
    date_end: str = "1899",
    states: Optional[str] = None,
    max_results: int = 20,
) -> str:
    """Search historical newspapers in Chronicling America.

    Searches the Library of Congress Chronicling America database for
    18th-19th century newspaper articles. Automatically expands keywords
    to include both English and Spanish variants.

    Args:
        keywords: Comma-separated list of search keywords related to historical mysteries
        date_start: Start year (default: 1800)
        date_end: End year (default: 1899)
        states: Comma-separated US states to search (default: East Coast states)
        max_results: Maximum number of results to return (default: 20)

    Returns:
        JSON string containing search results with documents matching the query
    """
    # Parse keywords
    keyword_list = [kw.strip() for kw in keywords.split(",") if kw.strip()]

    # Expand keywords to bilingual
    expanded = expand_keywords_bilingual(keyword_list)
    all_keywords = expanded["en"] + expanded["es"]

    # Parse states if provided
    state_list = None
    if states:
        state_list = [s.strip() for s in states.split(",") if s.strip()]

    # Perform search
    results = search_chronicling_america(
        keywords=all_keywords,
        date_start=date_start,
        date_end=date_end,
        states=state_list,
        rows=max_results,
    )

    # Convert to JSON-serializable format
    if results["documents"]:
        docs = [doc.model_dump() for doc in results["documents"]]
    else:
        docs = []

    return json.dumps(
        {
            "source": "chronicling_america",
            "keywords_used": all_keywords,
            "total_hits": results["total_hits"],
            "documents_returned": len(docs),
            "documents": docs,
            "error": results.get("error"),
        },
        ensure_ascii=False,
        indent=2,
    )


def search_nara_records(
    keywords: str,
    record_groups: Optional[str] = None,
    include_spanish_records: bool = True,
    max_results: int = 25,
) -> str:
    """Search NARA (National Archives) catalog for historical records.

    Searches diplomatic, trade, and maritime records from the National
    Archives. Particularly useful for Spanish-related records and
    international incidents.

    Args:
        keywords: Comma-separated list of search keywords related to historical mysteries
        record_groups: Comma-separated NARA Record Groups to search
                       (e.g., "RG 59, RG 45" for State Department and Naval records)
        include_spanish_records: Include Spanish-related Record Groups (default: True)
        max_results: Maximum number of results to return (default: 25)

    Returns:
        JSON string containing search results with archival records
    """
    # Parse keywords
    keyword_list = [kw.strip() for kw in keywords.split(",") if kw.strip()]

    # Expand keywords to bilingual
    expanded = expand_keywords_bilingual(keyword_list)
    all_keywords = expanded["en"] + expanded["es"]

    # Parse record groups
    rg_list = None
    if record_groups:
        rg_list = [rg.strip() for rg in record_groups.split(",") if rg.strip()]
    elif include_spanish_records:
        rg_list = list(get_spanish_record_groups().keys())

    # Perform search
    results = search_nara_catalog(
        keywords=all_keywords,
        record_groups=rg_list,
        rows=max_results,
    )

    # Convert to JSON-serializable format
    if results["documents"]:
        docs = [doc.model_dump() for doc in results["documents"]]
    else:
        docs = []

    return json.dumps(
        {
            "source": "nara_catalog",
            "keywords_used": all_keywords,
            "record_groups_searched": rg_list,
            "total_hits": results["total_hits"],
            "documents_returned": len(docs),
            "documents": docs,
            "error": results.get("error"),
        },
        ensure_ascii=False,
        indent=2,
    )


def save_search_results(
    theme: str,
    results_json: str,
    filename: Optional[str] = None,
) -> str:
    """Save search results to the data directory.

    Saves the collected search results to a JSON file in the data/ directory
    for later processing by the Historian Agent.

    Args:
        theme: The original search theme (e.g., "Spanish ship disappearance in Boston Harbor")
        results_json: JSON string containing all search results
        filename: Optional custom filename (default: auto-generated from timestamp)

    Returns:
        Path to the saved file
    """
    # Find project root (where data/ directory should be)
    data_dir = Path(__file__).parent.parent / "data"
    data_dir.mkdir(exist_ok=True)

    if filename is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        # Create safe filename from theme
        safe_theme = "".join(c if c.isalnum() or c in " _-" else "_" for c in theme[:30])
        safe_theme = safe_theme.replace(" ", "_")
        filename = f"search_{safe_theme}_{timestamp}.json"

    filepath = data_dir / filename

    # Parse and re-structure the results
    try:
        results_data = json.loads(results_json)
    except json.JSONDecodeError:
        results_data = {"raw": results_json}

    output = {
        "theme": theme,
        "search_timestamp": datetime.now().isoformat(),
        "results": results_data,
    }

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    return json.dumps(
        {
            "status": "success",
            "message": f"Results saved successfully",
            "filepath": str(filepath),
            "theme": theme,
        },
        ensure_ascii=False,
    )


def get_available_keywords() -> str:
    """Get the list of available bilingual keyword pairs.

    Returns the predefined English-Spanish keyword pairs that can be
    used for searching historical mysteries.

    Returns:
        JSON string containing keyword pairs
    """
    return json.dumps(
        {
            "description": "Available bilingual keyword pairs for historical mystery searches",
            "keyword_pairs": KEYWORD_PAIRS,
            "usage": "Use these keywords to search both English and Spanish sources",
        },
        ensure_ascii=False,
        indent=2,
    )


# Create the Librarian Agent instance using ADK LlmAgent
librarian_agent = LlmAgent(
    name="librarian",
    model="gemini-2.5-flash",
    description="公文書館APIから歴史的ミステリーに関連する資料を調査・収集するエージェント。Chronicling AmericaとNARA Catalogの両方を検索し、英語とスペイン語のバイリンガル検索をサポートします。",
    instruction=LIBRARIAN_INSTRUCTION,
    tools=[
        search_newspapers,
        search_nara_records,
        save_search_results,
        get_available_keywords,
    ],
)


# Keep the class for backward compatibility with existing imports
class LibrarianAgent:
    """公文書館APIから関連性の高い資料を調査・収集するエージェント

    This class provides a wrapper around the LlmAgent for backward compatibility
    and additional utility methods.
    """

    def __init__(self):
        self.agent = librarian_agent
        print("[LibrarianAgent] Initialized - Ready to search archives")

    def get_agent(self) -> LlmAgent:
        """Get the underlying LlmAgent instance."""
        return self.agent
