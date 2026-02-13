"""Ghost in the Archive - CLI Entry Point

This module provides the CLI entry point for running the Ghost Commander pipeline.
The agent definition lives in mystery_agents/agent.py (ADK convention).
"""

import asyncio
import logging
import sys
from pathlib import Path

from dotenv import load_dotenv

# .env はプロジェクトルートに配置
load_dotenv(Path(__file__).parent.parent / ".env")

from .agent import ghost_commander, SKIP_AUTHORS
from shared.orchestrator import run_pipeline

# プロジェクト全体のログを有効化（Publisher, Illustrator 等の既存ログが出力される）
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(name)s [%(levelname)s] %(message)s",
)

PIPELINE_TIMEOUT_SECONDS = 1800  # 30 minutes


async def investigate(query: str, *, run_id: str | None = None) -> str | None:
    """Run the Ghost Commander with a given investigation query.

    Args:
        query: The investigation query to process
        run_id: Optional pre-created pipeline run ID. If None, creates a new one.

    Returns:
        The pipeline run ID.
    """
    print("=" * 70)
    print("Ghost in the Archive - Historical Mystery Investigation System")
    print("=" * 70)
    print()
    print(f"Investigation Query: {query}")
    print()
    print("-" * 70)
    print()

    # Orchestrator 呼び出し（print コールバック付き）
    result = await run_pipeline(
        agent=ghost_commander,
        app_name="ghost_in_the_archive",
        user_message=query,
        initial_state={"investigation_query": query},
        run_id=run_id,
        run_type="blog",
        timeout_seconds=PIPELINE_TIMEOUT_SECONDS,
        max_llm_calls=120,
        skip_authors=SKIP_AUTHORS,
        on_text=lambda text: print(text),
    )

    print()
    print("=" * 70)
    print("Investigation Complete")
    print("=" * 70)

    # 実行ログのサマリ表示
    print("\nExecution Log:")
    for log in result.logs:
        icon = "\u2713" if log["status"] == "completed" else "\u2717" if log["status"] == "error" else "\u22ef"
        dur = f'{log["duration_seconds"]}s' if log["duration_seconds"] else "running"
        print(f"  {icon} {log['agent_name']:28s} {dur:>8s}")

    return result.run_id


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print("Usage: python -m mystery_agents <investigation query>")
        print('Example: python -m mystery_agents "Investigate historical discrepancies related to Spain in 1840s Boston"')
        sys.exit(1)

    query = " ".join(sys.argv[1:])
    asyncio.run(investigate(query))


if __name__ == "__main__":
    main()
