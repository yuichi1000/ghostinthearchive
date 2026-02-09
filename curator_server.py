"""Curator Server - FastAPI HTTP wrapper for the Curator agent.

Exposes the Curator agent (theme suggestion) as an HTTP service
for Cloud Run Service deployment.

Endpoints:
    POST /suggest-theme  - Run Curator agent and return theme suggestions
    GET  /health         - Health check
"""

import json
import os

from fastapi import FastAPI
from fastapi.responses import JSONResponse
import uvicorn

from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

from archive_agents.agents.curator import curator_agent
from shared.firestore import get_firestore_client

app = FastAPI()


def get_existing_titles() -> list[str]:
    """Fetch titles of all existing mysteries from Firestore."""
    try:
        db = get_firestore_client()
        docs = db.collection("mysteries").select(["title"]).stream(timeout=10)
        return [
            doc.to_dict().get("title", "")
            for doc in docs
            if doc.to_dict().get("title")
        ]
    except Exception as e:
        print(f"Warning: Could not fetch existing titles: {e}")
        return []


async def run_curator() -> dict:
    """Run the Curator agent and return parsed suggestions."""
    existing_titles = get_existing_titles()
    titles_text = (
        "\n".join(f"- {t}" for t in existing_titles)
        if existing_titles
        else "(なし - まだ調査済みのテーマはありません)"
    )

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
        state={"existing_titles": titles_text},
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

    return json.loads(cleaned)


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/suggest-theme")
async def suggest_theme():
    try:
        suggestions = await run_curator()
        return JSONResponse(content={"suggestions": suggestions})
    except json.JSONDecodeError as e:
        return JSONResponse(
            status_code=500,
            content={"error": "Failed to parse suggestions from agent", "detail": str(e)},
        )
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": "Failed to generate theme suggestions", "detail": str(e)},
        )


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8080"))
    uvicorn.run(app, host="0.0.0.0", port=port)
