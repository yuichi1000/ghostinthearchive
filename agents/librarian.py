"""Librarian Agent - 公文書館APIからの資料調査・収集

This agent specializes in searching historical archives and retrieving
relevant documents for mystery investigation.
"""

from pathlib import Path

from dotenv import load_dotenv
from google.adk.agents import LlmAgent

from tools import (
    get_available_keywords,
    save_search_results,
    search_nara_records,
    search_newspapers,
)

# Load environment variables from .env file
load_dotenv(Path(__file__).parent.parent / ".env")

# Agent instruction in Japanese
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

# Create the Librarian Agent instance using ADK LlmAgent
librarian_agent = LlmAgent(
    name="librarian",
    model="gemini-2.5-flash",
    description="公文書館APIから歴史的ミステリーに関連する資料を調査・収集するエージェント。"
    "Chronicling AmericaとNARA Catalogの両方を検索し、英語とスペイン語のバイリンガル検索をサポートします。",
    instruction=LIBRARIAN_INSTRUCTION,
    tools=[
        search_newspapers,
        search_nara_records,
        save_search_results,
        get_available_keywords,
    ],
)


class LibrarianAgent:
    """公文書館APIから関連性の高い資料を調査・収集するエージェント

    This class provides a wrapper around the LlmAgent for backward compatibility.
    """

    def __init__(self):
        self.agent = librarian_agent
        print("[LibrarianAgent] Initialized - Ready to search archives")

    def get_agent(self) -> LlmAgent:
        """Get the underlying LlmAgent instance."""
        return self.agent
