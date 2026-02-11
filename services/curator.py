"""Curator Server - FastAPI HTTP wrapper for the Curator agent.

Exposes the Curator agent (theme suggestion) as an HTTP service
for Cloud Run Service deployment. After generating English suggestions,
runs the Translator to produce Japanese translations.

Endpoints:
    POST /suggest-theme  - Run Curator + Translator and return bilingual suggestions
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

from curator_agents.agents.curator import curator_agent
from translator_agents.agents.translator import translator_agent
from shared.firestore import get_firestore_client
from shared.pipeline_failure import get_recent_failures

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
    """Run the Curator agent and return parsed English suggestions."""
    existing_titles = get_existing_titles()
    titles_text = (
        "\n".join(f"- {t}" for t in existing_titles)
        if existing_titles
        else "(None - no themes have been investigated yet)"
    )

    # 最近失敗したテーマを取得し、Curator に渡す
    recent_failures = get_recent_failures(limit=20)
    failed_themes = list({f["theme"] for f in recent_failures if f.get("theme")})
    failed_themes_text = (
        "\n".join(f"- {t}" for t in failed_themes)
        if failed_themes
        else "(None)"
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
        state={
            "existing_titles": titles_text,
            "failed_themes": failed_themes_text,
        },
    )

    result_text = ""
    async for event in runner.run_async(
        user_id=user_id,
        session_id=session_id,
        new_message=types.Content(
            role="user",
            parts=[types.Part(text="Suggest 5 research themes.")],
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


async def translate_suggestions(suggestions: list[dict]) -> list[dict]:
    """Translate English suggestions to Japanese using the Translator agent.

    Args:
        suggestions: List of English suggestion dicts with 'theme' and 'description'.

    Returns:
        List of bilingual suggestion dicts with theme, description, theme_ja, description_ja.
    """
    # Build translation input
    translation_input = {
        "suggestions": suggestions,
    }

    session_service = InMemorySessionService()
    runner = Runner(
        agent=translator_agent,
        app_name="ghost_in_the_archive_curator_translator",
        session_service=session_service,
    )

    user_id = "curator_translator"
    session_id = "theme_translation"

    await session_service.create_session(
        app_name="ghost_in_the_archive_curator_translator",
        user_id=user_id,
        session_id=session_id,
        state={},
    )

    result_text = ""
    async for event in runner.run_async(
        user_id=user_id,
        session_id=session_id,
        new_message=types.Content(
            role="user",
            parts=[types.Part(text=(
                f"Translate the following theme suggestions to Japanese:\n\n"
                f"{json.dumps(translation_input, ensure_ascii=False, indent=2)}"
            ))],
        ),
    ):
        if event.content and event.content.parts:
            for part in event.content.parts:
                if hasattr(part, "text") and part.text:
                    result_text += part.text

    # Parse translation result
    cleaned = result_text.strip()
    if "```json" in cleaned:
        cleaned = cleaned.split("```json", 1)[1].split("```", 1)[0].strip()
    elif "```" in cleaned:
        cleaned = cleaned.split("```", 1)[1].split("```", 1)[0].strip()

    try:
        translation = json.loads(cleaned)
    except json.JSONDecodeError:
        # If translation fails, return original suggestions without Japanese
        return suggestions

    # Merge English and Japanese
    ja_suggestions = translation.get("suggestions_ja", [])
    bilingual = []
    for i, en_suggestion in enumerate(suggestions):
        entry = {
            "theme": en_suggestion.get("theme", ""),
            "description": en_suggestion.get("description", ""),
        }
        if i < len(ja_suggestions):
            entry["theme_ja"] = ja_suggestions[i].get("theme_ja", "")
            entry["description_ja"] = ja_suggestions[i].get("description_ja", "")
        bilingual.append(entry)

    return bilingual


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/suggest-theme")
async def suggest_theme():
    try:
        # Step 1: Generate English suggestions
        suggestions = await run_curator()

        # Step 2: Translate to Japanese
        try:
            bilingual_suggestions = await translate_suggestions(suggestions)
        except Exception as e:
            print(f"Warning: Translation failed, returning English only: {e}")
            bilingual_suggestions = suggestions

        return JSONResponse(content={"suggestions": bilingual_suggestions})
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
