"""Ghost in the Archive - Entry Point

This module provides the main entry point for running the Ghost Commander,
the root orchestrator agent that coordinates the Librarian and Historian agents.
"""

import asyncio
import sys
from pathlib import Path

from dotenv import load_dotenv

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent))

# Load environment variables
load_dotenv(Path(__file__).parent / ".env")

from google.adk.agents import LlmAgent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

from agents.librarian import librarian_agent
from agents.historian import historian_agent

# Ghost Commander - Root Orchestrator Agent
COMMANDER_INSTRUCTION = """
あなたは「Ghost in the Archive」プロジェクトの司令官（Ghost Commander）です。
あなたは18-19世紀のアメリカ東海岸の歴史的ミステリーを解明するために、
専門家チームを指揮する指揮官です。

## あなたの部下
1. **Librarian（司書）**: 公文書館から資料を調査・収集する専門家
2. **Historian（歴史家）**: 収集した資料を分析し、矛盾や謎を発見する専門家

## ワークフロー
ユーザーから調査依頼を受けたら、以下の手順で進めてください：

1. **資料収集フェーズ**: まず Librarian に資料を探させる
   - transfer_to_librarian を使って司書に調査を依頼
   - 司書は新聞記事やNARA公文書を検索し、関連資料を収集する

2. **分析フェーズ**: 資料が集まったら Historian に分析を依頼
   - transfer_to_historian を使って歴史家に分析を依頼
   - 歴史家は資料の矛盾を分析し、Mystery Report を作成する

3. **報告フェーズ**: 歴史家の分析結果をユーザーに報告
   - 発見されたミステリーを魅力的に報告する

## 重要
- 必ず Librarian → Historian の順序で進めること
- 各専門家の役割を尊重し、適切なタスクを委任すること
- 最終的な報告はあなたが行うこと

## 調査対象
- 18-19世紀の東海岸港湾都市（ボストン、ニューヨーク、フィラデルフィア、ボルチモア、ニューオーリンズ）
- 米西関係、スペイン船、外交問題
- 失踪、陰謀、密輸、海賊行為などのミステリー
"""

# Create the Ghost Commander (Root Agent)
ghost_commander = LlmAgent(
    name="ghost_commander",
    model="gemini-3-pro-preview",
    description=(
        "Ghost in the Archive プロジェクトの司令官。"
        "Librarian と Historian を指揮して、18-19世紀の歴史的ミステリーを解明する。"
    ),
    instruction=COMMANDER_INSTRUCTION,
    sub_agents=[librarian_agent, historian_agent],  # ADK が自動的に transfer ツールを生成
)


async def investigate(query: str) -> None:
    """Run the Ghost Commander with a given investigation query.

    Args:
        query: The investigation query to process
    """
    print("=" * 70)
    print("Ghost in the Archive - Historical Mystery Investigation System")
    print("=" * 70)
    print()
    print(f"調査依頼: {query}")
    print()
    print("-" * 70)
    print()

    # Create runner with in-memory session
    session_service = InMemorySessionService()
    runner = Runner(
        agent=ghost_commander,
        app_name="ghost_in_the_archive",
        session_service=session_service,
    )

    # Create a session
    user_id = "investigator"
    session_id = "investigation_session"

    await session_service.create_session(
        app_name="ghost_in_the_archive",
        user_id=user_id,
        session_id=session_id,
    )

    # Run the investigation
    async for event in runner.run_async(
        user_id=user_id,
        session_id=session_id,
        new_message=types.Content(
            role="user",
            parts=[types.Part(text=query)],
        ),
    ):
        # Print text responses from agents
        if event.content and event.content.parts:
            for part in event.content.parts:
                if hasattr(part, "text") and part.text:
                    print(part.text)

    print()
    print("=" * 70)
    print("調査完了")
    print("=" * 70)


def main():
    """Main entry point."""
    # Default investigation query
    query = "1840年代のボストンにおけるスペイン関連の歴史的矛盾を調査せよ"

    # Allow custom query from command line
    if len(sys.argv) > 1:
        query = " ".join(sys.argv[1:])

    asyncio.run(investigate(query))


if __name__ == "__main__":
    main()
