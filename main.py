"""Ghost in the Archive - CLI Entry Point

This module provides the CLI entry point for running the Ghost Commander pipeline.
The agent definition lives in archive_agents/agent.py (ADK convention).
"""

import asyncio
import sys
from pathlib import Path

from dotenv import load_dotenv

# Load environment variables
load_dotenv(Path(__file__).parent / ".env")

from google.adk.agents.run_config import RunConfig
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

from archive_agents.agent import ghost_commander
from archive_agents.utils.pipeline_logger import PipelineLogger
from shared.pipeline_run import (
    create_pipeline_run,
    update_agent_started,
    update_agent_completed,
    complete_pipeline_run,
    error_pipeline_run,
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
    print(f"調査依頼: {query}")
    print()
    print("-" * 70)
    print()

    # Create pipeline run for progress tracking (if not provided)
    if run_id is None:
        run_id = create_pipeline_run("blog", query=query)

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
        state={"pipeline_log": []},
    )

    # Pipeline logger
    logger = PipelineLogger()
    current_agent_name: str | None = None
    accumulated_text: list[str] = []
    current_log_index: int | None = None

    run_config = RunConfig(max_llm_calls=50)

    try:
        async with asyncio.timeout(PIPELINE_TIMEOUT_SECONDS):
            # Run the investigation
            async for event in runner.run_async(
                user_id=user_id,
                session_id=session_id,
                new_message=types.Content(
                    role="user",
                    parts=[types.Part(text=query)],
                ),
                run_config=run_config,
            ):
                # Detect agent transitions via event.author
                author = getattr(event, "author", None)
                if author and author != "ghost_commander" and author != current_agent_name:
                    # Complete previous agent
                    if current_agent_name:
                        summary = " ".join(accumulated_text)[:200]
                        logger.complete_agent(summary or "(no text output)")
                        # Update pipeline run with completed agent
                        completed_logs = logger.get_logs()
                        if completed_logs:
                            update_agent_completed(
                                run_id, current_log_index, completed_logs[-1]
                            )
                        accumulated_text = []
                    # Start new agent
                    current_agent_name = author
                    logger.start_agent(current_agent_name)
                    # Update pipeline run with new agent
                    current_log_index = update_agent_started(
                        run_id, current_agent_name, logger.get_logs()[-1]
                    )

                # Print text responses from agents
                if event.content and event.content.parts:
                    for part in event.content.parts:
                        if hasattr(part, "text") and part.text:
                            print(part.text)
                            accumulated_text.append(part.text[:100])

        # Complete final agent
        if current_agent_name:
            summary = " ".join(accumulated_text)[:200]
            logger.complete_agent(summary or "(no text output)")
            completed_logs = logger.get_logs()
            if completed_logs:
                update_agent_completed(
                    run_id, current_log_index, completed_logs[-1]
                )

        # Store pipeline log in session state for Publisher
        session = await session_service.get_session(
            app_name="ghost_in_the_archive",
            user_id=user_id,
            session_id=session_id,
        )
        if session:
            session.state["pipeline_log"] = logger.get_logs()

        # Extract mystery_id from published_episode
        mystery_id = None
        if session:
            published = session.state.get("published_episode", "")
            if isinstance(published, str) and published.startswith("{"):
                import json

                try:
                    published_data = json.loads(published)
                    mystery_id = published_data.get("mystery_id")
                except (json.JSONDecodeError, AttributeError):
                    pass
            elif isinstance(published, dict):
                mystery_id = published.get("mystery_id")

        complete_pipeline_run(run_id, mystery_id=mystery_id)

    except TimeoutError:
        error_pipeline_run(run_id, f"Pipeline timed out after {PIPELINE_TIMEOUT_SECONDS}s")
        raise
    except Exception as e:
        error_pipeline_run(run_id, str(e))
        raise

    print()
    print("=" * 70)
    print("調査完了")
    print("=" * 70)

    # Print execution summary
    print("\n実行ログ:")
    for log in logger.get_logs():
        icon = "✓" if log["status"] == "completed" else "✗" if log["status"] == "error" else "⋯"
        dur = f'{log["duration_seconds"]}s' if log["duration_seconds"] else "running"
        print(f"  {icon} {log['agent_name']:12s} {dur:>8s}")

    return run_id


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
