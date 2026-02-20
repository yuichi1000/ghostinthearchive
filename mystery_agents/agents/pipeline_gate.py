"""パイプラインゲートコールバック。

前段エージェントの出力を確認し、有意なデータがない場合に
後続エージェントをスキップして無駄なトークン消費を防ぐ。
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Optional

from google.genai import types

from shared.constants import DEFAULT_SELECTED_LANGUAGES

if TYPE_CHECKING:
    from google.adk.agents.callback_context import CallbackContext

logger = logging.getLogger(__name__)

# 失敗マーカー
_FAILURE_MARKERS = frozenset({
    "NO_DOCUMENTS_FOUND",
    "INSUFFICIENT_DATA",
    "NO_CONTENT",
    "Not available",
})


def _is_meaningful(value: str) -> bool:
    """セッション状態の値が有意なデータを含むか判定する。

    テキストの先頭が失敗マーカーで始まる場合のみ「無意味」と判定する。
    ドキュメント本文の途中や末尾に部分的な失敗マーカーが含まれていても、
    先頭に有意なデータがあれば有意とみなす。
    """
    if not value:
        return False
    text = str(value).strip()
    return not any(text.startswith(marker) for marker in _FAILURE_MARKERS)


def _log_and_record_failure(callback_context: CallbackContext, stage: str, message: str) -> None:
    """パイプライン失敗をログに記録し、Firestore にも書き込む。"""
    logger.warning(
        "Pipeline gate [%s]: %s", stage, message,
        extra={"gate_name": stage, "decision": "skip", "reason": message},
    )
    try:
        from shared.pipeline_failure import log_pipeline_failure

        theme = callback_context.state.get("investigation_query", "unknown")
        run_id = callback_context.state.get("pipeline_run_id")
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
        selected = callback_context.state.get("selected_languages", DEFAULT_SELECTED_LANGUAGES)
        if not isinstance(selected, list):
            selected = list(DEFAULT_SELECTED_LANGUAGES)

        for lang in selected:
            docs = callback_context.state.get(f"collected_documents_{lang}", "")
            if _is_meaningful(docs):
                logger.info(
                    "Pipeline gate [scholar]: 通過（%s に有意なデータあり）", lang,
                    extra={"gate_name": "scholar", "decision": "pass"},
                )
                return None  # 有意なデータあり → 実行

        message = (
            "INSUFFICIENT_DATA: All Librarians returned no documents. "
            "Pipeline terminated to conserve resources."
        )
        _log_and_record_failure(callback_context, "librarian", message)
        return types.Content(
            parts=[types.Part(text=message)],
            role="model",
        )

    return gate


def make_polymath_gate():
    """全 Scholar が失敗した場合に ArmchairPolymath をスキップ。"""

    def gate(callback_context: CallbackContext) -> Optional[types.Content]:
        selected = callback_context.state.get("selected_languages", DEFAULT_SELECTED_LANGUAGES)
        if not isinstance(selected, list):
            selected = list(DEFAULT_SELECTED_LANGUAGES)

        for lang in selected:
            analysis = callback_context.state.get(f"scholar_analysis_{lang}", "")
            if _is_meaningful(analysis):
                logger.info(
                    "Pipeline gate [polymath]: 通過（%s に有意な分析あり）", lang,
                    extra={"gate_name": "polymath", "decision": "pass"},
                )
                return None

        message = (
            "INSUFFICIENT_DATA: No meaningful Scholar analyses available. "
            "Pipeline terminated."
        )
        _log_and_record_failure(callback_context, "scholar", message)
        return types.Content(
            parts=[types.Part(text=message)],
            role="model",
        )

    return gate


def make_storyteller_gate():
    """mystery_report が空なら Storyteller をスキップ。"""

    def gate(callback_context: CallbackContext) -> Optional[types.Content]:
        report = callback_context.state.get("mystery_report", "")
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
        content = callback_context.state.get("creative_content", "")
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
