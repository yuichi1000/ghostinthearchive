"""Podcast Pipeline - CLI Entry Point

脚本生成と音声生成の2つのモードを提供する。

Usage:
    python -m podcast_agents script <mystery_id> [--instructions "..."]
    python -m podcast_agents audio <podcast_id> [--voice "en-US-Studio-O"]

脚本生成: Scriptwriter → Podcast Translator（JA）の ADK パイプラインを実行
音声生成: 確定脚本を TTS で音声合成し GCS にアップロード
"""

import asyncio
import sys
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")

from .agent import podcast_script_commander
from .tools.firestore_tools import (
    load_mystery,
    create_podcast,
    get_podcast,
    save_script_result,
    save_audio_result,
    set_podcast_status,
)
from .tools.tts import generate_podcast_audio, DEFAULT_VOICE_NAME
from shared.orchestrator import run_pipeline
from shared.pipeline_run import create_pipeline_run


PIPELINE_TIMEOUT_SECONDS = 1200  # 20分


async def generate_script(
    mystery_id: str,
    custom_instructions: str = "",
    *,
    run_id: str | None = None,
    podcast_id: str | None = None,
) -> tuple[str, str]:
    """脚本 + 日本語訳を生成する。

    1. mystery から narrative_content 取得
    2. podcasts ドキュメント作成（または外部から受け取り）
    3. run_pipeline(podcast_script_commander)
    4. session state から structured_script + podcast_script_ja 取得
    5. podcasts 更新 (status=script_ready)

    Args:
        mystery_id: Firestore の mystery ドキュメント ID
        custom_instructions: 管理者からのカスタム指示
        run_id: 事前作成済みのパイプライン実行 ID
        podcast_id: 事前作成済みの podcast ドキュメント ID

    Returns:
        (podcast_id, run_id) のタプル
    """
    print("=" * 70)
    print("Ghost in the Archive - Podcast Script Generation")
    print("=" * 70)
    print()
    print(f"Mystery ID: {mystery_id}")
    if custom_instructions:
        print(f"Custom Instructions: {custom_instructions}")
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

    # podcasts ドキュメント作成（外部から渡されていない場合は自前で作成: CLI 利用時）
    if podcast_id is None:
        podcast_id = create_podcast(mystery_id, custom_instructions)
    print(f"Podcast ID: {podcast_id}")

    # pipeline_run ドキュメント作成（未指定時）
    if run_id is None:
        run_id = create_pipeline_run("podcast", mystery_id=mystery_id)

    # pipeline_run_id を podcast に紐付け
    from shared.firestore import get_firestore_client
    db = get_firestore_client()
    db.collection("podcasts").document(podcast_id).update({
        "pipeline_run_id": run_id,
    })

    try:
        # Orchestrator 呼び出し
        result = await run_pipeline(
            agent=podcast_script_commander,
            app_name="ghost_in_the_archive_podcast",
            user_message=f"以下のブログ記事からポッドキャストを作成してください: {title}",
            initial_state={
                "creative_content": narrative_content,
                "custom_instructions": custom_instructions,
            },
            run_id=run_id,
            run_type="podcast",
            timeout_seconds=PIPELINE_TIMEOUT_SECONDS,
            max_llm_calls=30,
            skip_authors={"podcast_script_commander"},
            on_text=lambda text: print(text),
        )

        # セッション状態から結果取得
        structured_script = result.session_state.get("structured_script", {})
        script_ja = result.session_state.get("podcast_script_ja", "")

        # Firestore に保存
        save_script_result(podcast_id, structured_script, script_ja)

        print()
        print("=" * 70)
        print("Script generation complete!")
        print(f"  Podcast ID: {podcast_id}")
        if structured_script:
            print(f"  Episode: {structured_script.get('episode_title', 'N/A')}")
            print(f"  Segments: {len(structured_script.get('segments', []))}")
        print("=" * 70)

        return podcast_id, result.run_id

    except TimeoutError:
        print(f"Error: Pipeline timed out after {PIPELINE_TIMEOUT_SECONDS}s")
        set_podcast_status(podcast_id, "error", "Pipeline timed out")
        raise
    except Exception as e:
        print(f"Error during script generation: {e}")
        set_podcast_status(podcast_id, "error", str(e))
        raise


async def generate_audio(
    podcast_id: str,
    script_override: dict | None = None,
    voice_name: str = DEFAULT_VOICE_NAME,
) -> dict:
    """確定脚本から音声を生成する。

    1. podcasts ドキュメント取得
    2. script_override があれば使用（管理者の編集反映）
    3. status → audio_generating
    4. tts.generate_podcast_audio() 呼び出し
    5. podcasts 更新 (status=audio_ready, audio={...})

    Args:
        podcast_id: Podcast ドキュメント ID
        script_override: 管理者が編集した脚本（None の場合は保存済み脚本を使用）
        voice_name: TTS ボイス名

    Returns:
        音声メタデータ dict
    """
    print("=" * 70)
    print("Ghost in the Archive - Podcast Audio Generation")
    print("=" * 70)
    print()
    print(f"Podcast ID: {podcast_id}")
    print(f"Voice: {voice_name}")
    print()

    # podcast ドキュメント取得
    podcast = get_podcast(podcast_id)
    if not podcast:
        raise ValueError(f"Podcast '{podcast_id}' not found.")

    # 脚本を取得
    if script_override:
        script = script_override
        print("Using script override from admin")
    else:
        script = podcast.get("script")
        if not script:
            raise ValueError(f"Podcast '{podcast_id}' has no script. Run script generation first.")

    segments = script.get("segments", [])
    if not segments:
        raise ValueError("Script has no segments.")

    print(f"Episode: {script.get('episode_title', 'N/A')}")
    print(f"Segments: {len(segments)}")
    print("-" * 70)
    print()

    # ステータス更新
    set_podcast_status(podcast_id, "audio_generating")

    try:
        # TTS 音声生成
        audio_metadata = generate_podcast_audio(
            segments=segments,
            podcast_id=podcast_id,
            voice_name=voice_name,
        )

        # Firestore に保存
        save_audio_result(podcast_id, audio_metadata)

        print()
        print("=" * 70)
        print("Audio generation complete!")
        print(f"  Duration: {audio_metadata['duration_seconds']}s")
        print(f"  URL: {audio_metadata['public_url']}")
        print(f"  GCS: {audio_metadata['gcs_path']}")
        print("=" * 70)

        return audio_metadata

    except Exception as e:
        print(f"Error during audio generation: {e}")
        set_podcast_status(podcast_id, "error", str(e))
        raise


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print("Usage:")
        print('  python -m podcast_agents script <mystery_id> [--instructions "..."]')
        print('  python -m podcast_agents audio <podcast_id> [--voice "en-US-Studio-O"]')
        sys.exit(1)

    command = sys.argv[1]

    if command == "script":
        if len(sys.argv) < 3:
            print("Usage: python -m podcast_agents script <mystery_id> [--instructions '...']")
            sys.exit(1)

        mystery_id = sys.argv[2]
        instructions = ""

        # --instructions パース
        for i, arg in enumerate(sys.argv[3:], start=3):
            if arg == "--instructions" and i + 1 < len(sys.argv):
                instructions = sys.argv[i + 1]
                break

        asyncio.run(generate_script(mystery_id, instructions))

    elif command == "audio":
        if len(sys.argv) < 3:
            print("Usage: python -m podcast_agents audio <podcast_id> [--voice '...']")
            sys.exit(1)

        podcast_id = sys.argv[2]
        voice = DEFAULT_VOICE_NAME

        # --voice パース
        for i, arg in enumerate(sys.argv[3:], start=3):
            if arg == "--voice" and i + 1 < len(sys.argv):
                voice = sys.argv[i + 1]
                break

        asyncio.run(generate_audio(podcast_id, voice_name=voice))

    else:
        print(f"Unknown command: {command}")
        print("Available commands: script, audio")
        sys.exit(1)


if __name__ == "__main__":
    main()
