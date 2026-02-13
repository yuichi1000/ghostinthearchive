"""Curator - CLI Entry Point

Suggests investigation themes for the Ghost in the Archive blog pipeline.
Fetches existing mystery titles from Firestore to avoid duplicates,
then runs the Curator agent to generate new theme ideas.

Outputs JSON to stdout (last line) for consumption by the web API.

Usage:
    python -m curator_agents
"""

import asyncio
import json
import sys
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")

from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

from .agents.curator import curator_agent
from .queries import get_existing_titles, get_category_distribution, format_category_distribution
from .schemas import strip_markdown_codeblock, validate_suggestions
from shared.pipeline_failure import get_recent_failures


async def suggest_themes() -> None:
    """Run the Curator agent and output JSON to stdout."""
    # 3つの Firestore クエリを並列実行
    existing_titles, recent_failures, distribution = await asyncio.gather(
        asyncio.to_thread(get_existing_titles),
        asyncio.to_thread(get_recent_failures, 20),
        asyncio.to_thread(get_category_distribution),
    )

    titles_text = "\n".join(f"- {t}" for t in existing_titles) if existing_titles else "(なし - まだ調査済みのテーマはありません)"

    failed_themes = list({f["theme"] for f in recent_failures if f.get("theme")})
    failed_themes_text = (
        "\n".join(f"- {t}" for t in failed_themes)
        if failed_themes
        else "(None)"
    )

    category_distribution_text = format_category_distribution(distribution)

    session_service = InMemorySessionService()
    runner = Runner(
        agent=curator_agent,
        app_name="ghost_in_the_archive_curator",
        session_service=session_service,
    )

    user_id = "curator"
    session_id = "theme_suggestion"

    await session_service.create_session(
        app_name="ghost_in_the_archive_curator",
        user_id=user_id,
        session_id=session_id,
        state={
            "existing_titles": titles_text,
            "failed_themes": failed_themes_text,
            "category_distribution": category_distribution_text,
        },
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

    # マークダウンコードブロック除去 + JSON パース + スキーマ検証
    cleaned = strip_markdown_codeblock(result_text)

    try:
        raw_suggestions = json.loads(cleaned)
    except json.JSONDecodeError:
        print(json.dumps({"error": "Failed to parse suggestions", "raw": result_text[:500]}, ensure_ascii=False))
        sys.exit(1)

    suggestions = validate_suggestions(raw_suggestions)
    if not suggestions:
        print(json.dumps({"error": "All suggestions failed schema validation", "raw": result_text[:500]}, ensure_ascii=False))
        sys.exit(1)

    print(json.dumps(suggestions, ensure_ascii=False))


def main():
    """Main entry point."""
    asyncio.run(suggest_themes())


if __name__ == "__main__":
    main()
