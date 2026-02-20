"""Curator Server - FastAPI HTTP wrapper for the Curator agent.

Exposes the Curator agent (theme suggestion) as an HTTP service
for Cloud Run Service deployment. After generating English suggestions,
runs the Translator to produce Japanese translations.

Endpoints:
    POST /suggest-theme  - Run Curator + Translator and return bilingual suggestions
    GET  /health         - Health check
"""

import asyncio
import json
import logging
import os

from fastapi import FastAPI
from fastapi.responses import JSONResponse
import uvicorn

from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

from curator_agents.agents.curator import curator_agent
from curator_agents.queries import (
    get_existing_titles,
    get_category_distribution,
    format_category_distribution,
)
from curator_agents.schemas import strip_markdown_codeblock, validate_suggestions
from mystery_agents.agents.translator import translator_agent
from shared.logging_config import PipelineContext, set_pipeline_context, setup_logging
from shared.pipeline_failure import get_recent_failures

# プロジェクト全体のログを有効化（Cloud Run: JSON / ローカル: プレーンテキスト）
setup_logging()

logger = logging.getLogger(__name__)


class _HealthCheckFilter(logging.Filter):
    """ヘルスチェック（/health）の INFO ログを抑制する。"""

    def filter(self, record: logging.LogRecord) -> bool:
        if record.levelno >= logging.WARNING:
            return True
        msg = record.getMessage()
        if "/health" in msg:
            return False
        return True


logging.getLogger("uvicorn.access").addFilter(_HealthCheckFilter())

# 認証エラーを示すキーワード
_AUTH_ERROR_KEYWORDS = ("reauthentication", "default credentials", "invalid_grant")

app = FastAPI()


def _is_auth_error(error: Exception) -> bool:
    """例外が Google Cloud 認証エラーかどうかを判定する。"""
    msg = str(error).lower()
    return any(kw in msg for kw in _AUTH_ERROR_KEYWORDS)


async def run_curator() -> list[dict]:
    """Run the Curator agent and return parsed English suggestions."""
    # 3つの Firestore クエリを並列実行
    existing_titles, recent_failures, distribution = await asyncio.gather(
        asyncio.to_thread(get_existing_titles),
        asyncio.to_thread(get_recent_failures, 20),
        asyncio.to_thread(get_category_distribution),
    )

    titles_text = (
        "\n".join(f"- {t}" for t in existing_titles)
        if existing_titles
        else "(None - no themes have been investigated yet)"
    )

    failed_themes = list({f["theme"] for f in recent_failures if f.get("theme")})
    failed_themes_text = (
        "\n".join(f"- {t}" for t in failed_themes)
        if failed_themes
        else "(None)"
    )

    category_distribution_text = format_category_distribution(distribution)

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
            "category_distribution": category_distribution_text,
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

    # マークダウンコードブロック除去 + JSON パース + スキーマ検証
    cleaned = strip_markdown_codeblock(result_text)
    raw_suggestions = json.loads(cleaned)
    return validate_suggestions(raw_suggestions)


async def translate_suggestions(suggestions: list[dict]) -> list[dict]:
    """Translate English suggestions to Japanese using the Translator agent.

    Args:
        suggestions: List of English suggestion dicts with 'theme' and 'description'.

    Returns:
        List of bilingual suggestion dicts with theme, description, theme_ja, description_ja.
    """
    # Translator が期待するのは theme + description のみ（category 等を除去）
    translation_input = {
        "suggestions": [
            {"theme": s.get("theme", ""), "description": s.get("description", "")}
            for s in suggestions
        ],
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
        # Translator のインストラクションが {creative_content}, {mystery_report},
        # {structured_report} を参照するため、空文字で初期化する。
        # Curator 経由の場合はユーザーメッセージの JSON が翻訳ソースとなる。
        state={
            "creative_content": "",
            "mystery_report": "",
            "structured_report": "",
        },
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

    # マークダウンコードブロック除去
    cleaned = strip_markdown_codeblock(result_text)

    try:
        translation = json.loads(cleaned)
    except json.JSONDecodeError:
        # 翻訳パース失敗時は英語のみで返す
        logger.warning(
            "翻訳結果の JSON パース失敗。英語のみで返却。Translator 出力: %.500s",
            cleaned,
        )
        return suggestions

    # Merge English and Japanese
    ja_suggestions = translation.get("suggestions", [])
    bilingual = []
    for i, en_suggestion in enumerate(suggestions):
        entry = {
            "theme": en_suggestion.get("theme", ""),
            "description": en_suggestion.get("description", ""),
        }
        if i < len(ja_suggestions):
            entry["theme_ja"] = ja_suggestions[i].get("theme", "")
            entry["description_ja"] = ja_suggestions[i].get("description", "")
        bilingual.append(entry)

    return bilingual


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/suggest-theme")
async def suggest_theme():
    set_pipeline_context(PipelineContext(pipeline_type="curator"))
    try:
        # Step 1: Generate English suggestions
        suggestions = await run_curator()

        # Step 2: Translate to Japanese
        try:
            bilingual_suggestions = await translate_suggestions(suggestions)
        except Exception as e:
            logger.warning("翻訳失敗、英語のみで返却: %s", e)
            bilingual_suggestions = suggestions

        return JSONResponse(content={"suggestions": bilingual_suggestions})
    except json.JSONDecodeError as e:
        return JSONResponse(
            status_code=500,
            content={"error": "Failed to parse suggestions from agent", "detail": str(e)},
        )
    except Exception as e:
        if _is_auth_error(e):
            return JSONResponse(
                status_code=500,
                content={
                    "error": "Failed to generate theme suggestions",
                    "error_type": "auth_error",
                    "detail": "Google Cloud の認証が切れています。サーバーで gcloud auth application-default login を実行してください。",
                },
            )
        return JSONResponse(
            status_code=500,
            content={"error": "Failed to generate theme suggestions", "detail": str(e)},
        )


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8080"))
    uvicorn.run(app, host="0.0.0.0", port=port)
