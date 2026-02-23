"""Pipeline Server - FastAPI HTTP wrapper for Blog/Podcast/Design pipelines.

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
    POST /design/generate          - Start design proposal generation
    POST /design/render-assets     - Start design asset rendering
    GET  /health                   - Health check
"""

import asyncio
import logging
import os

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import uvicorn

from shared.logging_config import setup_logging
from shared.pipeline_run import create_pipeline_run, error_pipeline_run

# プロジェクト全体のログを有効化（Cloud Run: JSON / ローカル: プレーンテキスト）
setup_logging()

logger = logging.getLogger(__name__)


class _HealthCheckFilter(logging.Filter):
    """ヘルスチェック（/health）の INFO ログを抑制する。

    Cloud Run のヘルスチェックは数秒ごとに発火し、ログが大量に生成されるため
    INFO 以下を除外する。WARNING 以上は通す。
    """

    def filter(self, record: logging.LogRecord) -> bool:
        if record.levelno >= logging.WARNING:
            return True
        msg = record.getMessage()
        # uvicorn のアクセスログ: "GET /health HTTP/1.1"
        if "/health" in msg:
            return False
        return True


# uvicorn のアクセスログにフィルタ適用
logging.getLogger("uvicorn.access").addFilter(_HealthCheckFilter())

app = FastAPI()


class InvestigateRequest(BaseModel):
    query: str


class GenerateScriptRequest(BaseModel):
    mystery_id: str
    custom_instructions: str = ""


class GenerateAudioRequest(BaseModel):
    podcast_id: str
    script: dict | None = None  # 管理者が編集した脚本
    voice_name: str = "en-US-Chirp3-HD-Enceladus"


class GenerateDesignRequest(BaseModel):
    mystery_id: str
    custom_instructions: str = ""


class RenderAssetsRequest(BaseModel):
    design_id: str


async def _run_investigate(query: str, run_id: str) -> None:
    """Background task wrapper for the blog pipeline.

    CLI を経由せず Orchestrator を直接呼ぶことで、stdout ノイズを除去する。
    """
    try:
        from shared.orchestrator import run_pipeline
        from mystery_agents.agent import ghost_commander, SKIP_AUTHORS

        await run_pipeline(
            agent=ghost_commander,
            app_name="ghost_in_the_archive",
            user_message=query,
            initial_state={"investigation_query": query},
            run_id=run_id,
            run_type="blog",
            skip_authors=SKIP_AUTHORS,
        )
    except Exception as e:
        logger.exception("Blog pipeline failed: %s", e)
        error_pipeline_run(run_id, str(e), error_detail={
            "error_type": "exception",
            "exception_class": type(e).__name__,
        })


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
        # podcast ドキュメントもエラーに更新（script_generating でスタック防止）
        from podcast_agents.tools.firestore_tools import set_podcast_status
        set_podcast_status(podcast_id, "error", str(e))


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
        # podcast ドキュメントもエラーに更新（audio_generating でスタック防止）
        from podcast_agents.tools.firestore_tools import set_podcast_status
        set_podcast_status(podcast_id, "error", str(e))


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
        podcast_id = create_podcast(
            body.mystery_id, body.custom_instructions, pipeline_run_id=run_id
        )
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


async def _run_generate_design(
    mystery_id: str, custom_instructions: str, run_id: str, design_id: str
) -> None:
    """Background task wrapper for design proposal generation."""
    try:
        from alchemist_agents.cli import generate_design

        await generate_design(
            mystery_id, custom_instructions, run_id=run_id, design_id=design_id
        )
    except Exception as e:
        logger.exception("Design generation failed: %s", e)
        error_pipeline_run(run_id, str(e))
        from alchemist_agents.tools.firestore_tools import set_design_status
        set_design_status(design_id, "error", str(e))


async def _run_render_assets(design_id: str, run_id: str) -> None:
    """Background task wrapper for design asset rendering."""
    try:
        from alchemist_agents.cli import render_assets

        await render_assets(design_id, run_id=run_id)
    except Exception as e:
        logger.exception("Design rendering failed: %s", e)
        error_pipeline_run(run_id, str(e))
        from alchemist_agents.tools.firestore_tools import set_design_status
        set_design_status(design_id, "error", str(e))


@app.post("/design/generate")
async def generate_design_endpoint(body: GenerateDesignRequest):
    """デザイン提案を生成（fire-and-forget）

    design_id を同期的に作成してレスポンスに含める。
    フロントエンドが即座に /designs/{design_id} に遷移できるようにする。
    """
    try:
        from alchemist_agents.tools.firestore_tools import create_design

        run_id = create_pipeline_run("design", mystery_id=body.mystery_id)
        design_id = create_design(
            body.mystery_id, body.custom_instructions, pipeline_run_id=run_id
        )
        asyncio.create_task(
            _run_generate_design(
                body.mystery_id, body.custom_instructions, run_id, design_id
            )
        )
        return JSONResponse(
            content={
                "status": "accepted",
                "run_id": run_id,
                "design_id": design_id,
            }
        )
    except Exception as e:
        logger.exception("Failed to start design generation: %s", e)
        return JSONResponse(
            status_code=500,
            content={"error": "Failed to start design generation", "detail": str(e)},
        )


@app.post("/design/render-assets")
async def render_assets_endpoint(body: RenderAssetsRequest):
    """デザインアセットをレンダリング（fire-and-forget）"""
    try:
        from alchemist_agents.tools.firestore_tools import get_design

        design = get_design(body.design_id)
        if not design:
            return JSONResponse(
                status_code=404,
                content={"error": f"Design '{body.design_id}' not found"},
            )

        mystery_id = design.get("mystery_id", "")
        run_id = create_pipeline_run("design_render", mystery_id=mystery_id)
        asyncio.create_task(
            _run_render_assets(body.design_id, run_id)
        )
        return JSONResponse(
            content={
                "status": "accepted",
                "run_id": run_id,
                "design_id": body.design_id,
            }
        )
    except Exception as e:
        logger.exception("Failed to start design rendering: %s", e)
        return JSONResponse(
            status_code=500,
            content={"error": "Failed to start design rendering", "detail": str(e)},
        )


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8080"))
    uvicorn.run(app, host="0.0.0.0", port=port)
