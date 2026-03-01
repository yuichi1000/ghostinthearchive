"""パイプラインゲートコールバック。

前段エージェントの出力を確認し、有意なデータがない場合に
後続エージェントをスキップして無駄なトークン消費を防ぐ。
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Optional

from google.genai import types

from shared.constants import DEFAULT_SELECTED_LANGUAGES, is_meaningful
from shared.state_keys import (
    CREATIVE_CONTENT,
    FULLTEXT_METRICS,
    INVESTIGATION_QUERY,
    MYSTERY_REPORT,
    PIPELINE_RUN_ID,
    SELECTED_LANGUAGES,
    collected_documents_key,
)

if TYPE_CHECKING:
    from google.adk.agents.callback_context import CallbackContext

logger = logging.getLogger(__name__)

# 後方互換エイリアス（既存コードが _is_meaningful を参照）
_is_meaningful = is_meaningful


def _log_and_record_failure(callback_context: CallbackContext, stage: str, message: str) -> None:
    """パイプライン失敗をログに記録し、Firestore にも書き込む。"""
    logger.warning(
        "Pipeline gate [%s]: %s", stage, message,
        extra={"gate_name": stage, "decision": "skip", "reason": message},
    )
    try:
        from shared.pipeline_failure import log_pipeline_failure

        theme = callback_context.state.get(INVESTIGATION_QUERY, "unknown")
        run_id = callback_context.state.get(PIPELINE_RUN_ID)
        log_pipeline_failure(
            theme=str(theme),
            stage=stage,
            reason=message,
            run_id=str(run_id) if run_id else None,
        )
    except Exception:
        # Firestore 書き込み失敗はパイプラインをブロックしない
        logger.debug("Failed to log pipeline failure to Firestore", exc_info=True)


def make_scholar_gate():
    """全 Librarian が失敗した場合に ParallelScholars をスキップ。"""

    def gate(callback_context: CallbackContext) -> Optional[types.Content]:
        selected = callback_context.state.get(SELECTED_LANGUAGES, DEFAULT_SELECTED_LANGUAGES)
        if not isinstance(selected, list):
            selected = list(DEFAULT_SELECTED_LANGUAGES)

        has_docs = False
        for lang in selected:
            docs = callback_context.state.get(collected_documents_key(lang), "")
            if _is_meaningful(docs):
                has_docs = True
                break

        if not has_docs:
            message = (
                "INSUFFICIENT_DATA: All Librarians returned no documents. "
                "Pipeline terminated to conserve resources."
            )
            _log_and_record_failure(callback_context, "librarian", message)
            return types.Content(
                parts=[types.Part(text=message)],
                role="model",
            )

        # Check 2: 全文ドキュメントが 0 件なら早期終了
        metrics = callback_context.state.get(FULLTEXT_METRICS)
        if isinstance(metrics, dict) and metrics.get("fulltext_documents", -1) == 0:
            message = (
                "NO_FULLTEXT_AVAILABLE: Documents found but none contain full text. "
                "Scholar analysis requires full text excerpts. "
                "Pipeline terminated to conserve resources."
            )
            _log_and_record_failure(callback_context, "aggregator", message)
            return types.Content(
                parts=[types.Part(text=message)],
                role="model",
            )

        logger.info(
            "Pipeline gate [scholar]: 通過",
            extra={"gate_name": "scholar", "decision": "pass"},
        )
        return None

    return gate


def make_storyteller_gate():
    """mystery_report が空なら Storyteller をスキップ。"""

    def gate(callback_context: CallbackContext) -> Optional[types.Content]:
        report = callback_context.state.get(MYSTERY_REPORT, "")
        if _is_meaningful(report):
            logger.info(
                "Pipeline gate [storyteller]: 通過",
                extra={"gate_name": "storyteller", "decision": "pass"},
            )
            return None

        message = "NO_CONTENT: No mystery report available. Pipeline terminated."
        _log_and_record_failure(callback_context, "polymath", message)
        return types.Content(
            parts=[types.Part(text=message)],
            role="model",
        )

    return gate


def make_post_story_gate():
    """creative_content が空なら Illustrator/Translator/Publisher をスキップ。"""

    def gate(callback_context: CallbackContext) -> Optional[types.Content]:
        content = callback_context.state.get(CREATIVE_CONTENT, "")
        if _is_meaningful(content):
            logger.info(
                "Pipeline gate [post_story]: 通過",
                extra={"gate_name": "post_story", "decision": "pass"},
            )
            return None

        message = "NO_CONTENT: No story content available. Skipped."
        _log_and_record_failure(callback_context, "storyteller", message)
        return types.Content(
            parts=[types.Part(text=message)],
            role="model",
        )

    return gate
