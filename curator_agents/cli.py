"""Curator - CLI Entry Point

Suggests investigation themes for the Ghost in the Archive blog pipeline.
Delegates to core.suggest_themes() for the actual logic.

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

from .core import suggest_themes


async def _run() -> None:
    """Run the Curator agent and output JSON to stdout."""
    try:
        suggestions = await suggest_themes(
            user_message="調査テーマを5件提案してください。",
            empty_titles_text="(なし - まだ調査済みのテーマはありません)",
        )
    except json.JSONDecodeError:
        print(json.dumps(
            {"error": "Failed to parse suggestions"},
            ensure_ascii=False,
        ))
        sys.exit(1)
    except ValueError as e:
        print(json.dumps(
            {"error": str(e)},
            ensure_ascii=False,
        ))
        sys.exit(1)

    print(json.dumps(suggestions, ensure_ascii=False))


def main():
    """Main entry point."""
    asyncio.run(_run())


if __name__ == "__main__":
    main()
