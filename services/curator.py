"""Curator Server - FastAPI HTTP wrapper for the Curator agent.

Exposes the Curator agent (theme suggestion) as an HTTP service
for Cloud Run Service deployment. After generating English suggestions,
runs the Translator to produce Japanese translations.

Endpoints:
    POST /suggest-theme  - Run Curator + Translator and return bilingual suggestions
    GET  /health         - Health check
"""

import json
import logging
import os

from fastapi import FastAPI
from fastapi.responses import JSONResponse
import uvicorn

from curator_agents.core import suggest_themes as run_curator
from curator_agents.runner import run_single_agent
from curator_agents.schemas import strip_markdown_codeblock
from mystery_agents.agents.translator import translator_agent
from shared.logging_config import (
    PipelineContext,
    set_pipeline_context,
    setup_logging,
    suppress_health_check_logs,
)

# プロジェクト全体のログを有効化（Cloud Run: JSON / ローカル: プレーンテキスト）
setup_logging()
suppress_health_check_logs()

logger = logging.getLogger(__name__)

# 認証エラーを示すキーワード
_AUTH_ERROR_KEYWORDS = ("reauthentication", "default credentials", "invalid_grant")

# Translator のインストラクションが {creative_content}, {mystery_report},
# {structured_report} を参照するため、空文字で初期化する必須ワークアラウンド。
# Curator 経由の場合はユーザーメッセージの JSON が翻訳ソースとなる。
_TRANSLATOR_EMPTY_STATE = {
    "creative_content": "",
    "mystery_report": "",
    "structured_report": "",
}

app = FastAPI()


def _is_auth_error(error: Exception) -> bool:
    """例外が Google Cloud 認証エラーかどうかを判定する。"""
    msg = str(error).lower()
    return any(kw in msg for kw in _AUTH_ERROR_KEYWORDS)


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

    result_text = await run_single_agent(
        translator_agent,
        app_name="ghost_in_the_archive_curator_translator",
        user_id="curator_translator",
        session_id="theme_translation",
        state=_TRANSLATOR_EMPTY_STATE,
        user_message=(
            f"Translate the following theme suggestions to Japanese:\n\n"
            f"{json.dumps(translation_input, ensure_ascii=False, indent=2)}"
        ),
    )

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

    # Merge English and Japanese（カバレッジフィールドを保持）
    ja_suggestions = translation.get("suggestions", [])
    bilingual = []
    for i, en_suggestion in enumerate(suggestions):
        entry = {
            "theme": en_suggestion.get("theme", ""),
            "description": en_suggestion.get("description", ""),
            "coverage_score": en_suggestion.get("coverage_score"),
            "primary_apis": en_suggestion.get("primary_apis", []),
            "probe_hits": en_suggestion.get("probe_hits", {}),
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
