"""DynamicPolymathBlock — Armchair Polymath の動的 instruction 構築。

アクティブ言語の Scholar 分析のみを instruction に含め、
非アクティブ言語の空プレースホルダーを排除する。
DynamicScholarBlock と同じ BaseAgent パターン。

Named Scholar + Multilingual Scholar の両方の分析結果を動的に参照。

ゲート機能を内包: 全 Scholar 分析が空なら INSUFFICIENT_DATA を返す。
"""

import logging
from collections.abc import AsyncGenerator

from google.adk.agents import BaseAgent, LlmAgent
from google.adk.agents.invocation_context import InvocationContext
from google.adk.events.event import Event
from google.genai import types

from shared.model_config import create_pro_model

from .armchair_polymath import (
    INSTRUCTION_BODY,
    INSTRUCTION_PREAMBLE,
    POLYMATH_DESCRIPTION,
    POLYMATH_MAX_OUTPUT_TOKENS,
    POLYMATH_TOOLS,
    log_polymath_tool_call,
)
from .language_scholars import get_scholar_config
from .pipeline_gate import _is_meaningful, _log_and_record_failure

logger = logging.getLogger(__name__)


def _build_analyses_section(meaningful_langs: list[str], has_multilingual: bool = False) -> str:
    """アクティブ言語のみの Scholar Analyses セクションを構築する。

    Args:
        meaningful_langs: 有意な分析がある Named Scholar の言語コードリスト
        has_multilingual: Multilingual Scholar の分析が有意かどうか
    """
    lang_lines = []
    for lang in meaningful_langs:
        name = get_scholar_config(lang)["language_name"]
        lang_lines.append(
            f"- {{scholar_analysis_{lang}}}: {name} cultural perspective analysis"
        )
    if has_multilingual:
        lang_lines.append(
            "- {scholar_analysis_multilingual}: Multilingual peripheral languages analysis"
        )

    lang_names = ", ".join(
        get_scholar_config(lang)["language_name"] for lang in meaningful_langs
    )
    if has_multilingual:
        lang_names += ", Multilingual"

    total_count = len(meaningful_langs) + (1 if has_multilingual else 0)
    return (
        "## Input: Scholar Analyses\n"
        f"Scholar analyses available for {total_count} source(s): "
        f"{lang_names}.\n\n"
        + "\n".join(lang_lines)
    )


class DynamicPolymathBlock(BaseAgent):
    """アクティブ言語のみの instruction で Armchair Polymath を実行する。

    Named Scholar + Multilingual Scholar の分析を動的に参照。
    ゲート機能を内包: 有意な Scholar 分析がなければスキップ。
    """

    async def _run_async_impl(
        self, ctx: InvocationContext
    ) -> AsyncGenerator[Event, None]:
        state = ctx.session.state

        # 有意な分析がある Named Scholar の言語を特定
        active_langs = state.get("active_languages", [])
        meaningful_langs = [
            lang
            for lang in active_langs
            if _is_meaningful(state.get(f"scholar_analysis_{lang}", ""))
        ]

        # Multilingual Scholar の有意性チェック
        has_multilingual = _is_meaningful(
            state.get("scholar_analysis_multilingual", "")
        )

        total_meaningful = len(meaningful_langs) + (1 if has_multilingual else 0)

        # ゲート: 有意な分析なし → INSUFFICIENT_DATA
        if total_meaningful == 0:
            message = (
                "INSUFFICIENT_DATA: No meaningful Scholar analyses available. "
                "Pipeline terminated."
            )
            _log_and_record_failure(
                type("_Ctx", (), {"state": state})(),
                "scholar",
                message,
            )
            yield Event(
                invocation_id=ctx.invocation_id,
                author=self.name,
                branch=ctx.branch,
                content=types.Content(
                    role="model",
                    parts=[types.Part(text=message)],
                ),
            )
            return

        logger.info(
            "DynamicPolymathBlock: %d 件の分析で Polymath 実行: %s%s",
            total_meaningful,
            ", ".join(meaningful_langs),
            " + multilingual" if has_multilingual else "",
        )

        # アクティブ言語のみの instruction を動的に組み立て
        analyses_section = _build_analyses_section(meaningful_langs, has_multilingual)
        instruction = INSTRUCTION_PREAMBLE + "\n" + analyses_section + "\n" + INSTRUCTION_BODY

        # LlmAgent を生成・実行
        polymath = LlmAgent(
            name="armchair_polymath",
            model=create_pro_model(),
            description=POLYMATH_DESCRIPTION,
            instruction=instruction,
            tools=POLYMATH_TOOLS,
            output_key="mystery_report",
            generate_content_config=types.GenerateContentConfig(
                max_output_tokens=POLYMATH_MAX_OUTPUT_TOKENS,
            ),
            before_tool_callback=log_polymath_tool_call,
        )
        async for event in polymath.run_async(ctx):
            yield event


def create_dynamic_polymath_block() -> DynamicPolymathBlock:
    """DynamicPolymathBlock を新規生成する。"""
    return DynamicPolymathBlock(
        name="dynamic_polymath_block",
        description=(
            "Dynamically builds Armchair Polymath instruction with only active "
            "language analyses (Named + Multilingual). Integrates polymath gate: "
            "skips when no meaningful Scholar analyses are available."
        ),
    )
