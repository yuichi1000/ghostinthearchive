"""Storyteller Agent - Fusing historical rigor with eerie atmosphere

This agent transforms historical analysis data into creative content that
balances historical rigor with eerie atmosphere, fusing fact and folklore
into compelling narratives.

Output formats:
- Blog articles (in English)

Input: Mystery Report with Folkloric Context (from Scholar)
Output: Creative content that weaves together fact and legend
"""

import logging
from pathlib import Path

from dotenv import load_dotenv
from google.adk.agents import LlmAgent
from google.adk.agents.callback_context import CallbackContext
from google.adk.models import LlmRequest, LlmResponse
from google.genai import types

from shared.model_config import (
    DEFAULT_STORYTELLER,
    STORYTELLER_MODELS,
    create_storyteller_model,
)
from shared.state_keys import STORYTELLER_LLM_METADATA

from .storyteller_instructions import STORYTELLER_INSTRUCTION

logger = logging.getLogger(__name__)

load_dotenv(Path(__file__).parent.parent / ".env")

def _estimate_tokens(text: str) -> int:
    """英語4文字≒1トークンの概算。ログ用途。"""
    return len(text) // 4 if text else 0


def _is_leaked_content(content: types.Content) -> bool:
    """ADK _present_other_agent_message が生成したリークコンテンツを検出する。

    ADK の SequentialAgent 内（branch=None）では include_contents='none' が無効化され、
    上流エージェントの会話履歴が role='user' + 先頭パート "For context:" の形式でリークする。
    """
    if not content.parts:
        return False
    first_text = next((p.text for p in content.parts if p.text), None)
    return first_text == "For context:"


def _has_function_parts(content: types.Content) -> bool:
    """function_call または function_response パーツを含むか。"""
    return any(
        p.function_call or p.function_response
        for p in (content.parts or [])
    )


def _storyteller_before_model(
    callback_context: CallbackContext,
    llm_request: LlmRequest,
) -> LlmResponse | None:
    """リークした上流会話履歴をパージし、診断ログを出力する。"""
    # mystery_report のトークン推定
    mystery_report = callback_context.state.get("mystery_report", "")
    report_tokens = _estimate_tokens(mystery_report)

    # パージ: リークコンテンツを除去し、ツール呼び出し/応答は保持
    original_contents = llm_request.contents or []
    purged_contents: list[types.Content] = []
    purged_tokens = 0

    for content in original_contents:
        if _is_leaked_content(content) and not _has_function_parts(content):
            # リークコンテンツのトークン数を集計
            leaked_text = " ".join(
                p.text for p in (content.parts or []) if p.text
            )
            purged_tokens += _estimate_tokens(leaked_text)
        else:
            purged_contents.append(content)

    llm_request.contents = purged_contents

    # 診断ログ: system_instruction + contents のトークン内訳
    si_text = ""
    if llm_request.config and llm_request.config.system_instruction:
        si = llm_request.config.system_instruction
        if isinstance(si, str):
            si_text = si
        elif hasattr(si, "parts") and si.parts:
            si_text = " ".join(p.text for p in si.parts if p.text)
    si_tokens = _estimate_tokens(si_text)

    contents_text = " ".join(
        p.text
        for c in purged_contents
        for p in (c.parts or [])
        if p.text
    )
    contents_tokens = _estimate_tokens(contents_text)

    total_tokens = si_tokens + contents_tokens
    logger.info(
        "Storyteller before_model 診断: mystery_report=%s tokens (Polymath出力), "
        "system_instruction=%s tokens, contents=%s tokens (パージ後), "
        "パージ除去=%s tokens, 合計推定=%s tokens",
        f"{report_tokens:,}",
        f"{si_tokens:,}",
        f"{contents_tokens:,}",
        f"{purged_tokens:,}",
        f"{total_tokens:,}",
    )

    return None


def _storyteller_after_model(
    callback_context: CallbackContext,
    llm_response: LlmResponse,
) -> LlmResponse | None:
    """Storyteller の LLM 応答メタデータを記録する。"""
    has_text = (
        llm_response.content
        and llm_response.content.parts
        and any(
            hasattr(p, "text") and p.text
            for p in llm_response.content.parts
        )
    )

    # モデル情報をセッション状態から取得
    storyteller_key = callback_context.state.get("storyteller", DEFAULT_STORYTELLER)
    model_config = STORYTELLER_MODELS.get(storyteller_key, {})
    # 実際にレスポンスを返したモデル名（LiteLlm アダプタが設定）
    actual_model = getattr(llm_response, "model_version", None)

    if has_text and not llm_response.error_code:
        # 正常応答: モデル情報 + トークン使用量をログ
        metadata = {
            "storyteller": storyteller_key,
            "display_name": model_config.get("display_name", "unknown"),
            "model_id": model_config.get("model_id", "unknown"),
            "actual_model": actual_model,
            "prompt_tokens": (
                llm_response.usage_metadata.prompt_token_count
                if llm_response.usage_metadata else None
            ),
            "output_tokens": (
                llm_response.usage_metadata.candidates_token_count
                if llm_response.usage_metadata else None
            ),
        }
        logger.info(
            "Storyteller 応答完了: selected=%s, actual=%s, tokens=%s/%s",
            metadata["model_id"],
            metadata["actual_model"],
            metadata["prompt_tokens"],
            metadata["output_tokens"],
        )
        callback_context.state[STORYTELLER_LLM_METADATA] = metadata
        return None

    # 異常応答: メタデータをログ + セッション状態に記録
    metadata = {
        "storyteller": storyteller_key,
        "display_name": model_config.get("display_name", "unknown"),
        "model_id": model_config.get("model_id", "unknown"),
        "actual_model": actual_model,
        "finish_reason": str(llm_response.finish_reason) if llm_response.finish_reason else None,
        "error_code": llm_response.error_code,
        "error_message": llm_response.error_message,
        "has_content": llm_response.content is not None,
        "prompt_tokens": (
            llm_response.usage_metadata.prompt_token_count
            if llm_response.usage_metadata else None
        ),
        "output_tokens": (
            llm_response.usage_metadata.candidates_token_count
            if llm_response.usage_metadata else None
        ),
    }
    logger.error(
        "Storyteller 異常応答: selected=%s, actual=%s, finish_reason=%s, error_code=%s",
        metadata["model_id"],
        metadata["actual_model"],
        metadata["finish_reason"],
        metadata["error_code"],
        extra=metadata,
    )
    callback_context.state[STORYTELLER_LLM_METADATA] = metadata
    return None


def create_storyteller(storyteller: str = DEFAULT_STORYTELLER) -> LlmAgent:
    """指定ストーリーテラーで Storyteller エージェントを生成する。

    Args:
        storyteller: ストーリーテラー名（STORYTELLER_MODELS のキー）

    Returns:
        Storyteller LlmAgent インスタンス
    """
    return LlmAgent(
        name="storyteller",
        model=create_storyteller_model(storyteller),
        description=(
            "Creative agent that weaves narratives fusing historical rigor with eerie atmosphere. "
            "Receives the Mystery Report (including Folkloric Context) and generates "
            "an English blog article that interweaves fact and legend."
        ),
        instruction=STORYTELLER_INSTRUCTION,
        tools=[],
        output_key="creative_content",
        include_contents="none",
        before_model_callback=_storyteller_before_model,
        after_model_callback=_storyteller_after_model,
    )


# 後方互換: デフォルトシングルトン（ADK CLI / adk web 用）
storyteller_agent = create_storyteller()
