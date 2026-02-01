"""Ghost in the Archive - Entry Point

This module provides the main entry point for running the Ghost Commander pipeline,
which sequentially executes Librarian → Historian → Storyteller agents using
ADK's SequentialAgent for deterministic execution order.
"""

import asyncio
import sys
from pathlib import Path

from dotenv import load_dotenv

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent))

# Load environment variables
load_dotenv(Path(__file__).parent / ".env")

from google.adk.agents import SequentialAgent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

from agents.librarian import librarian_agent
from agents.historian import historian_agent
from agents.storyteller import storyteller_agent
from agents.designer import designer_agent
from agents.publisher import publisher_agent

# Ghost Commander - Sequential Pipeline
# ADK の SequentialAgent が Librarian → Historian → Storyteller → Designer → Publisher を固定順序で実行
# 各エージェントは output_key でセッション状態にデータを保存し、
# 次のエージェントが {key} で参照する
ghost_commander = SequentialAgent(
    name="ghost_commander",
    description=(
        "Ghost in the Archive パイプライン。"
        "Librarian → Historian → Storyteller → Designer → Publisher の順で実行し、"
        "歴史的ミステリーと民俗学的怪異を調査・分析・コンテンツ化・画像生成・公開する。"
    ),
    sub_agents=[librarian_agent, historian_agent, storyteller_agent, designer_agent, publisher_agent],
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
    if len(sys.argv) < 2:
        print("Usage: python main.py <調査クエリ>")
        print('Example: python main.py "1840年代のボストンにおけるスペイン関連の歴史的矛盾を調査せよ"')
        sys.exit(1)

    query = " ".join(sys.argv[1:])
    asyncio.run(investigate(query))


if __name__ == "__main__":
    main()
