"""Podcast Pipeline - CLI Entry Point

Generates a podcast (script + audio) for a published mystery article.
Reads the article from Firestore, runs Scriptwriter -> Producer, and saves results back.

Usage:
    python -m podcast_agents <mystery_id>

Also serves as the entry point for Cloud Run Jobs.
"""

import asyncio
import sys
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")

from .agent import podcast_commander
from .tools.firestore_tools import (
    load_mystery,
    save_podcast_result,
    set_podcast_status,
)
from shared.orchestrator import run_pipeline
from shared.pipeline_run import create_pipeline_run


PIPELINE_TIMEOUT_SECONDS = 1200  # 20 minutes


async def generate_podcast(mystery_id: str, *, run_id: str | None = None) -> str | None:
    """Generate a podcast for a given mystery article.

    Args:
        mystery_id: The Firestore document ID of the mystery.
        run_id: Optional pre-created pipeline run ID. If None, creates a new one.

    Returns:
        The pipeline run ID.
    """
    print("=" * 70)
    print("Ghost in the Archive - Podcast Generation")
    print("=" * 70)
    print()
    print(f"Mystery ID: {mystery_id}")
    print()

    # Firestore から記事読み込み
    mystery = load_mystery(mystery_id)
    if not mystery:
        raise ValueError(f"Mystery '{mystery_id}' not found in Firestore.")

    narrative_content = mystery.get("narrative_content", "")
    if not narrative_content:
        raise ValueError(f"Mystery '{mystery_id}' has no narrative_content.")

    title = mystery.get("title", mystery_id)
    print(f"Article: {title}")
    print("-" * 70)
    print()

    # Podcast 生成中マーク
    set_podcast_status(mystery_id, "generating")

    # pipeline_run ドキュメント作成（未指定時）
    if run_id is None:
        run_id = create_pipeline_run("podcast", mystery_id=mystery_id)

    try:
        # Orchestrator 呼び出し
        result = await run_pipeline(
            agent=podcast_commander,
            app_name="ghost_in_the_archive_podcast",
            user_message=f"\u4ee5\u4e0b\u306e\u30d6\u30ed\u30b0\u8a18\u4e8b\u304b\u3089\u30dd\u30c3\u30c9\u30ad\u30e3\u30b9\u30c8\u3092\u4f5c\u6210\u3057\u3066\u304f\u3060\u3055\u3044: {title}",
            initial_state={"creative_content": narrative_content},
            run_id=run_id,
            run_type="podcast",
            timeout_seconds=PIPELINE_TIMEOUT_SECONDS,
            max_llm_calls=30,
            skip_authors={"podcast_commander"},
            on_text=lambda text: print(text),
        )

        # Podcast 固有の後処理: セッション状態から結果取得 → Firestore 保存
        podcast_script = result.session_state.get("podcast_script", "")
        audio_assets = result.session_state.get("audio_assets", "")
        save_result = save_podcast_result(mystery_id, podcast_script, audio_assets)

        print()
        print("=" * 70)
        print(f"Podcast generation complete: {save_result}")
        print("=" * 70)

        return result.run_id

    except TimeoutError:
        print(f"Error: Pipeline timed out after {PIPELINE_TIMEOUT_SECONDS}s")
        set_podcast_status(mystery_id, "error")
        raise
    except Exception as e:
        print(f"Error during podcast generation: {e}")
        set_podcast_status(mystery_id, "error")
        raise


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print("Usage: python -m podcast_agents <mystery_id>")
        print('Example: python -m podcast_agents "MYSTERY-1820-BOSTON-001"')
        sys.exit(1)

    mystery_id = sys.argv[1]
    asyncio.run(generate_podcast(mystery_id))


if __name__ == "__main__":
    main()
