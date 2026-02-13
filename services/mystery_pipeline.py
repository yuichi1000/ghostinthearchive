"""Pipeline Server - FastAPI HTTP wrapper for Blog/Podcast pipelines.

Exposes the long-running pipelines as HTTP endpoints using a
fire-and-forget pattern: each request creates a pipeline_run document,
spawns the pipeline as a background asyncio task, and immediately returns
the run_id to the caller.

NOTE: This is a separate Cloud Run Service from Curator (services/curator.py).
Curator returns synchronous responses in seconds, while these pipelines run
for 10-30 minutes. The different execution profiles require different
resource limits, timeouts, and CPU allocation strategies:
  - Curator: 1 CPU, 1Gi, 300s timeout, cpu_idle=true
  - Pipeline: 2 CPU, 2Gi, 1800s timeout, cpu_idle=false
Combining them would force the expensive Pipeline config onto Curator.

Endpoints:
    POST /investigate              - Start blog creation pipeline
    POST /podcast/generate-script  - Start podcast script generation
    POST /podcast/generate-audio   - Start podcast audio generation
    GET  /health                   - Health check
"""

import asyncio
import logging
import os

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import uvicorn

from shared.pipeline_run import create_pipeline_run, error_pipeline_run

# プロジェクト全体のログを有効化（Publisher, Illustrator 等の既存ログが出力される）
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(name)s [%(levelname)s] %(message)s",
)

logger = logging.getLogger(__name__)

app = FastAPI()


class InvestigateRequest(BaseModel):
    query: str


class GenerateScriptRequest(BaseModel):
    mystery_id: str
    custom_instructions: str = ""


class GenerateAudioRequest(BaseModel):
    podcast_id: str
    script: dict | None = None  # 管理者が編集した脚本
    voice_name: str = "en-US-Studio-O"


async def _run_investigate(query: str, run_id: str) -> None:
    """Background task wrapper for the blog pipeline.

    CLI を経由せず Orchestrator を直接呼ぶことで、stdout ノイズを除去する。
    """
    try:
        from shared.orchestrator import run_pipeline
        from mystery_agents.agent import ghost_commander

        await run_pipeline(
            agent=ghost_commander,
            app_name="ghost_in_the_archive",
            user_message=query,
            initial_state={"investigation_query": query},
            run_id=run_id,
            run_type="blog",
        )
    except Exception as e:
        logger.exception("Blog pipeline failed: %s", e)
        error_pipeline_run(run_id, str(e))


async def _run_generate_script(
    mystery_id: str, custom_instructions: str, run_id: str, podcast_id: str
) -> None:
    """Background task wrapper for podcast script generation."""
    try:
        from podcast_agents.cli import generate_script

        await generate_script(
            mystery_id, custom_instructions, run_id=run_id, podcast_id=podcast_id
        )
    except Exception as e:
        logger.exception("Podcast script generation failed: %s", e)
        error_pipeline_run(run_id, str(e))


async def _run_generate_audio(
    podcast_id: str,
    script: dict | None,
    voice_name: str,
) -> None:
    """Background task wrapper for podcast audio generation."""
    try:
        from podcast_agents.cli import generate_audio

        await generate_audio(podcast_id, script_override=script, voice_name=voice_name)
    except Exception as e:
        logger.exception("Podcast audio generation failed: %s", e)


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/investigate")
async def investigate_endpoint(body: InvestigateRequest):
    try:
        run_id = create_pipeline_run("blog", query=body.query)
        asyncio.create_task(_run_investigate(body.query, run_id))
        return JSONResponse(content={"status": "accepted", "run_id": run_id})
    except Exception as e:
        logger.exception("Failed to start blog pipeline: %s", e)
        return JSONResponse(
            status_code=500,
            content={"error": "Failed to start blog pipeline", "detail": str(e)},
        )


@app.post("/podcast/generate-script")
async def generate_script_endpoint(body: GenerateScriptRequest):
    """脚本 + 日本語訳を生成（fire-and-forget）

    podcast_id を同期的に作成してレスポンスに含める。
    フロントエンドが即座に /podcasts/{podcast_id} に遷移できるようにする。
    """
    try:
        from podcast_agents.tools.firestore_tools import create_podcast

        run_id = create_pipeline_run("podcast", mystery_id=body.mystery_id)
        podcast_id = create_podcast(body.mystery_id, body.custom_instructions)
        asyncio.create_task(
            _run_generate_script(
                body.mystery_id, body.custom_instructions, run_id, podcast_id
            )
        )
        return JSONResponse(
            content={
                "status": "accepted",
                "run_id": run_id,
                "podcast_id": podcast_id,
            }
        )
    except Exception as e:
        logger.exception("Failed to start podcast script generation: %s", e)
        return JSONResponse(
            status_code=500,
            content={"error": "Failed to start podcast script generation", "detail": str(e)},
        )


@app.post("/podcast/generate-audio")
async def generate_audio_endpoint(body: GenerateAudioRequest):
    """音声生成（fire-and-forget）"""
    try:
        asyncio.create_task(
            _run_generate_audio(body.podcast_id, body.script, body.voice_name)
        )
        return JSONResponse(
            content={"status": "accepted", "podcast_id": body.podcast_id}
        )
    except Exception as e:
        logger.exception("Failed to start podcast audio generation: %s", e)
        return JSONResponse(
            status_code=500,
            content={"error": "Failed to start podcast audio generation", "detail": str(e)},
        )


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8080"))
    uvicorn.run(app, host="0.0.0.0", port=port)
