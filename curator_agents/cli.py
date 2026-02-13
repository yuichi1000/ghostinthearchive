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
from shared.pipeline_failure import get_recent_failures


async def suggest_themes() -> None:
    """Run the Curator agent and output JSON to stdout."""
    existing_titles = get_existing_titles()
    titles_text = "\n".join(f"- {t}" for t in existing_titles) if existing_titles else "(なし - まだ調査済みのテーマはありません)"

    # 最近失敗したテーマを取得し、Curator に渡す
    recent_failures = get_recent_failures(limit=20)
    failed_themes = list({f["theme"] for f in recent_failures if f.get("theme")})
    failed_themes_text = (
        "\n".join(f"- {t}" for t in failed_themes)
        if failed_themes
        else "(None)"
    )

    # カテゴリ分布を取得してプロンプト用テキストに変換
    distribution = get_category_distribution()
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
