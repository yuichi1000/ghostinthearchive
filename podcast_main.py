"""Podcast Pipeline - CLI Entry Point

Generates a podcast (script + audio) for a published mystery article.
Reads the article from Firestore, runs Scriptwriter → Producer, and saves results back.

Usage:
    python podcast_main.py <mystery_id>

Also serves as the entry point for Cloud Run Jobs.
"""

import asyncio
import sys
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / ".env")

from google.adk.agents.run_config import RunConfig
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

from podcast_agents.agent import podcast_commander
from podcast_agents.tools.firestore_tools import (
    load_mystery,
    save_podcast_result,
    set_podcast_status,
)
from shared.pipeline_run import (
    create_pipeline_run,
    update_agent_started,
    update_agent_completed,
    complete_pipeline_run,
    error_pipeline_run,
)


PIPELINE_TIMEOUT_SECONDS = 1200  # 20 minutes


async def generate_podcast(mystery_id: str) -> None:
    """Generate a podcast for a given mystery article.

    Args:
        mystery_id: The Firestore document ID of the mystery.
    """
    print("=" * 70)
    print("Ghost in the Archive - Podcast Generation")
    print("=" * 70)
    print()
    print(f"Mystery ID: {mystery_id}")
    print()

    # Load mystery from Firestore
    mystery = load_mystery(mystery_id)
    if not mystery:
        print(f"Error: Mystery '{mystery_id}' not found in Firestore.")
        sys.exit(1)

    narrative_content = mystery.get("narrative_content", "")
    if not narrative_content:
        print(f"Error: Mystery '{mystery_id}' has no narrative_content.")
        sys.exit(1)

    title = mystery.get("title", mystery_id)
    print(f"Article: {title}")
    print("-" * 70)
    print()

    # Mark as generating
    set_podcast_status(mystery_id, "generating")

    # Create pipeline run for progress tracking
    run_id = create_pipeline_run("podcast", mystery_id=mystery_id)

    # Create runner with session pre-loaded with creative_content
    session_service = InMemorySessionService()
    runner = Runner(
        agent=podcast_commander,
        app_name="ghost_in_the_archive_podcast",
        session_service=session_service,
    )

    user_id = "podcast_generator"
    session_id = f"podcast_{mystery_id}"

    await session_service.create_session(
        app_name="ghost_in_the_archive_podcast",
        user_id=user_id,
        session_id=session_id,
        state={
            "creative_content": narrative_content,
            "pipeline_log": [],
        },
    )

    # Run the podcast pipeline
    podcast_script = ""
    audio_assets = ""
    current_agent_name: str | None = None
    current_log_index: int | None = None

    from datetime import datetime, timezone

    agent_start_time: datetime | None = None

    run_config = RunConfig(max_llm_calls=30)

    try:
        async with asyncio.timeout(PIPELINE_TIMEOUT_SECONDS):
            async for event in runner.run_async(
                user_id=user_id,
                session_id=session_id,
                new_message=types.Content(
                    role="user",
                    parts=[types.Part(text=f"以下のブログ記事からポッドキャストを作成してください: {title}")],
                ),
                run_config=run_config,
            ):
                # Track agent transitions
                author = getattr(event, "author", None)
                if author and author != "podcast_commander" and author != current_agent_name:
                    # Complete previous agent
                    if current_agent_name and agent_start_time:
                        end_time = datetime.now(timezone.utc)
                        duration = (end_time - agent_start_time).total_seconds()
                        completed_entry = {
                            "agent_name": current_agent_name,
                            "status": "completed",
                            "start_time": agent_start_time.isoformat(),
                            "end_time": end_time.isoformat(),
                            "duration_seconds": round(duration, 2),
                            "output_summary": f"{current_agent_name} completed",
                        }
                        update_agent_completed(run_id, current_log_index, completed_entry)

                    # Start new agent
                    current_agent_name = author
                    agent_start_time = datetime.now(timezone.utc)
                    log_entry = {
                        "agent_name": current_agent_name,
                        "status": "running",
                        "start_time": agent_start_time.isoformat(),
                        "end_time": None,
                        "duration_seconds": None,
                        "output_summary": None,
                    }
                    current_log_index = update_agent_started(run_id, current_agent_name, log_entry)

                if event.content and event.content.parts:
                    for part in event.content.parts:
                        if hasattr(part, "text") and part.text:
                            print(part.text)

        # Complete final agent
        if current_agent_name and agent_start_time:
            end_time = datetime.now(timezone.utc)
            duration = (end_time - agent_start_time).total_seconds()
            completed_entry = {
                "agent_name": current_agent_name,
                "status": "completed",
                "start_time": agent_start_time.isoformat(),
                "end_time": end_time.isoformat(),
                "duration_seconds": round(duration, 2),
                "output_summary": f"{current_agent_name} completed",
            }
            update_agent_completed(run_id, current_log_index, completed_entry)

        # Retrieve results from session state
        session = await session_service.get_session(
            app_name="ghost_in_the_archive_podcast",
            user_id=user_id,
            session_id=session_id,
        )
        if session:
            podcast_script = session.state.get("podcast_script", "")
            audio_assets = session.state.get("audio_assets", "")

        # Save results to Firestore
        result = save_podcast_result(mystery_id, podcast_script, audio_assets)
        complete_pipeline_run(run_id, mystery_id=mystery_id)
        print()
        print("=" * 70)
        print(f"Podcast generation complete: {result}")
        print("=" * 70)

    except TimeoutError:
        print(f"Error: Pipeline timed out after {PIPELINE_TIMEOUT_SECONDS}s")
        set_podcast_status(mystery_id, "error")
        error_pipeline_run(run_id, f"Pipeline timed out after {PIPELINE_TIMEOUT_SECONDS}s")
        raise
    except Exception as e:
        print(f"Error during podcast generation: {e}")
        set_podcast_status(mystery_id, "error")
        error_pipeline_run(run_id, str(e))
        raise


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print("Usage: python podcast_main.py <mystery_id>")
        print('Example: python podcast_main.py "MYSTERY-1820-BOSTON-001"')
        sys.exit(1)

    mystery_id = sys.argv[1]
    asyncio.run(generate_podcast(mystery_id))


if __name__ == "__main__":
    main()
