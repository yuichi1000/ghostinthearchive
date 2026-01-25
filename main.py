"""Ghost in the Archive - Entry Point

This module provides the main entry point for running the Librarian Agent.
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

from agents import librarian_agent


async def run_librarian_demo():
    """Run the Librarian Agent with a sample historical mystery search."""
    print("=" * 60)
    print("Ghost in the Archive - Librarian Agent Demo")
    print("=" * 60)
    print()

    # Create runner with in-memory session
    session_service = InMemorySessionService()
    runner = Runner(
        agent=librarian_agent,
        app_name="ghost_in_the_archive",
        session_service=session_service,
    )

    # Create a session
    user_id = "demo_user"
    session_id = "demo_session"

    session = await session_service.create_session(
        app_name="ghost_in_the_archive",
        user_id=user_id,
        session_id=session_id,
    )

    # Sample query - investigating a Spanish ship disappearance
    query = """
    ボストン港で1820年代に発生したスペイン船の失踪について調査してください。
    新聞記事と公文書の両方から関連資料を収集し、結果を保存してください。
    キーワード: disappearance, Spanish, ship, Boston, mystery
    """

    print(f"Query: {query.strip()}")
    print()
    print("-" * 60)
    print("Agent Response:")
    print("-" * 60)
    print()

    # Run the agent
    async for event in runner.run_async(
        user_id=user_id,
        session_id=session_id,
        new_message=types.Content(
            role="user",
            parts=[types.Part(text=query)],
        ),
    ):
        # Print text responses from the agent
        if event.content and event.content.parts:
            for part in event.content.parts:
                if hasattr(part, "text") and part.text:
                    print(part.text)

    print()
    print("=" * 60)
    print("Demo completed. Check the data/ directory for saved results.")
    print("=" * 60)


def main():
    """Main entry point."""
    print("Ghost in the Archive - Historical Mystery Discovery System")
    print()

    # Run the async demo
    asyncio.run(run_librarian_demo())


if __name__ == "__main__":
    main()
