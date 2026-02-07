"""Translation Pipeline - CLI Entry Point

Translates a pending mystery article from Japanese to English.
Reads the article from Firestore, runs Translator, and saves results back.

Usage:
    python translate_main.py <mystery_id>

Also serves as the entry point for Cloud Run Jobs.
"""

import asyncio
import json
import sys
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / ".env")

from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

from translator_agents.agent import translator_commander
from translator_agents.tools.firestore_tools import (
    load_mystery_for_translation,
    save_translation_result,
    set_translation_error,
)


async def translate_mystery(mystery_id: str) -> None:
    """Translate a mystery article from Japanese to English.

    Args:
        mystery_id: The Firestore document ID of the mystery.
    """
    print("=" * 70)
    print("Ghost in the Archive - Translation Pipeline")
    print("=" * 70)
    print()
    print(f"Mystery ID: {mystery_id}")
    print()

    # Load mystery from Firestore
    mystery = load_mystery_for_translation(mystery_id)
    if not mystery:
        print(f"Error: Mystery '{mystery_id}' not found in Firestore.")
        sys.exit(1)

    narrative_content = mystery.get("narrative_content", "")
    if not narrative_content:
        print(f"Error: Mystery '{mystery_id}' has no narrative_content.")
        set_translation_error(mystery_id)
        sys.exit(1)

    title = mystery.get("title", mystery_id)
    print(f"Article: {title}")
    print("-" * 70)
    print()

    # Create runner with session pre-loaded with Japanese content
    session_service = InMemorySessionService()
    runner = Runner(
        agent=translator_commander,
        app_name="ghost_in_the_archive_translator",
        session_service=session_service,
    )

    user_id = "translator"
    session_id = f"translate_{mystery_id}"

    # Set Japanese fields in session state
    alternative_hypotheses = mystery.get("alternative_hypotheses", [])
    if isinstance(alternative_hypotheses, list):
        alternative_hypotheses_str = json.dumps(alternative_hypotheses, ensure_ascii=False)
    else:
        alternative_hypotheses_str = str(alternative_hypotheses)

    story_hooks = mystery.get("story_hooks", [])
    if isinstance(story_hooks, list):
        story_hooks_str = json.dumps(story_hooks, ensure_ascii=False)
    else:
        story_hooks_str = str(story_hooks)

    await session_service.create_session(
        app_name="ghost_in_the_archive_translator",
        user_id=user_id,
        session_id=session_id,
        state={
            "title": mystery.get("title", ""),
            "summary": mystery.get("summary", ""),
            "narrative_content": narrative_content,
            "discrepancy_detected": mystery.get("discrepancy_detected", ""),
            "hypothesis": mystery.get("hypothesis", ""),
            "alternative_hypotheses": alternative_hypotheses_str,
            "political_climate": mystery.get("political_climate", ""),
            "story_hooks": story_hooks_str,
            "pipeline_log": [],
        },
    )

    # Run the translation pipeline
    translation_result = ""

    try:
        async for event in runner.run_async(
            user_id=user_id,
            session_id=session_id,
            new_message=types.Content(
                role="user",
                parts=[types.Part(text=f"以下の日本語記事を英語に翻訳してください: {title}")],
            ),
        ):
            if event.content and event.content.parts:
                for part in event.content.parts:
                    if hasattr(part, "text") and part.text:
                        print(part.text)

        # Retrieve results from session state
        session = await session_service.get_session(
            app_name="ghost_in_the_archive_translator",
            user_id=user_id,
            session_id=session_id,
        )
        if session:
            translation_result = session.state.get("translation_result", "")

        # Check for NO_TRANSLATION marker
        if "NO_TRANSLATION" in translation_result:
            print()
            print("Translation skipped: No content to translate.")
            set_translation_error(mystery_id)
            sys.exit(1)

        # Save results to Firestore
        result = save_translation_result(mystery_id, translation_result)
        print()
        print("=" * 70)
        print(f"Translation complete: {result}")
        print("=" * 70)

    except Exception as e:
        print(f"Error during translation: {e}")
        set_translation_error(mystery_id)
        raise


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print("Usage: python translate_main.py <mystery_id>")
        print('Example: python translate_main.py "MYSTERY-1820-BOSTON-001"')
        sys.exit(1)

    mystery_id = sys.argv[1]
    asyncio.run(translate_mystery(mystery_id))


if __name__ == "__main__":
    main()
