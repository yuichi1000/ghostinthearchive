"""Theme Suggester - CLI Entry Point

Suggests investigation themes for the Ghost in the Archive blog pipeline.
Fetches existing mystery titles from Firestore to avoid duplicates,
then runs the Theme Suggester agent to generate new theme ideas.

Outputs JSON to stdout (last line) for consumption by the web API.

Usage:
    python theme_suggester_main.py
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

from archive_agents.agents.theme_suggester import theme_suggester_agent
from shared.firestore import get_firestore_client


def get_existing_titles() -> list[str]:
    """Fetch titles of all existing mysteries from Firestore."""
    try:
        db = get_firestore_client()
        docs = db.collection("mysteries").select(["title"]).stream()
        return [doc.to_dict().get("title", "") for doc in docs if doc.to_dict().get("title")]
    except Exception as e:
        print(f"Warning: Could not fetch existing titles: {e}", file=sys.stderr)
        return []


async def suggest_themes() -> None:
    """Run the Theme Suggester agent and output JSON to stdout."""
    existing_titles = get_existing_titles()
    titles_text = "\n".join(f"- {t}" for t in existing_titles) if existing_titles else "(なし - まだ調査済みのテーマはありません)"

    session_service = InMemorySessionService()
    runner = Runner(
        agent=theme_suggester_agent,
        app_name="ghost_in_the_archive_theme_suggester",
        session_service=session_service,
    )

    user_id = "theme_suggester"
    session_id = "theme_suggestion"

    await session_service.create_session(
        app_name="ghost_in_the_archive_theme_suggester",
        user_id=user_id,
        session_id=session_id,
        state={"existing_titles": titles_text},
    )

    result_text = ""
    async for event in runner.run_async(
        user_id=user_id,
        session_id=session_id,
        new_message=types.Content(
            role="user",
            parts=[types.Part(text="調査テーマを5件提案してください。")],
        ),
    ):
        if event.content and event.content.parts:
            for part in event.content.parts:
                if hasattr(part, "text") and part.text:
                    result_text += part.text

    # Extract JSON from the result (handle markdown code blocks)
    cleaned = result_text.strip()
    if "```json" in cleaned:
        cleaned = cleaned.split("```json", 1)[1].split("```", 1)[0].strip()
    elif "```" in cleaned:
        cleaned = cleaned.split("```", 1)[1].split("```", 1)[0].strip()

    # Validate JSON and output
    try:
        suggestions = json.loads(cleaned)
        print(json.dumps(suggestions, ensure_ascii=False))
    except json.JSONDecodeError:
        print(json.dumps({"error": "Failed to parse suggestions", "raw": result_text[:500]}, ensure_ascii=False))
        sys.exit(1)


def main():
    """Main entry point."""
    asyncio.run(suggest_themes())


if __name__ == "__main__":
    main()
