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
    POST /investigate  - Start blog creation pipeline
    POST /podcast      - Start podcast generation pipeline
    GET  /health       - Health check
"""

import asyncio
import logging
import os

# プロジェクト全体のログを有効化（Publisher, Illustrator 等の既存ログが出力される）
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(name)s [%(levelname)s] %(message)s",
)

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import uvicorn

from shared.pipeline_run import create_pipeline_run, error_pipeline_run

logger = logging.getLogger(__name__)

app = FastAPI()


class InvestigateRequest(BaseModel):
    query: str


class MysteryIdRequest(BaseModel):
    mystery_id: str


async def _run_investigate(query: str, run_id: str) -> None:
    """Background task wrapper for the blog pipeline."""
    try:
        from mystery_agents.cli import investigate

        await investigate(query, run_id=run_id)
    except Exception as e:
        logger.exception("Blog pipeline failed: %s", e)
        error_pipeline_run(run_id, str(e))


async def _run_podcast(mystery_id: str, run_id: str) -> None:
    """Background task wrapper for the podcast pipeline."""
    try:
        from podcast_agents.cli import generate_podcast

        await generate_podcast(mystery_id, run_id=run_id)
    except Exception as e:
        logger.exception("Podcast pipeline failed: %s", e)
        error_pipeline_run(run_id, str(e))


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


@app.post("/podcast")
async def podcast_endpoint(body: MysteryIdRequest):
    try:
        run_id = create_pipeline_run("podcast", mystery_id=body.mystery_id)
        asyncio.create_task(_run_podcast(body.mystery_id, run_id))
        return JSONResponse(content={"status": "accepted", "run_id": run_id})
    except Exception as e:
        logger.exception("Failed to start podcast pipeline: %s", e)
        return JSONResponse(
            status_code=500,
            content={"error": "Failed to start podcast pipeline", "detail": str(e)},
        )


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8080"))
    uvicorn.run(app, host="0.0.0.0", port=port)
