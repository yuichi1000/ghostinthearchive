"""DynamicPolymathBlock — Armchair Polymath の動的 instruction 構築。

アクティブ言語の Scholar 分析のみを instruction に含め、
非アクティブ言語の空プレースホルダーを排除する。
DynamicScholarBlock と同じ BaseAgent パターン。

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
    POLYMATH_TOOLS,
)
from .language_scholars import SCHOLAR_CONFIGS
from .pipeline_gate import _is_meaningful, _log_and_record_failure

logger = logging.getLogger(__name__)


def _build_analyses_section(meaningful_langs: list[str]) -> str:
    """アクティブ言語のみの Scholar Analyses セクションを構築する。"""
    lang_lines = []
    for lang in meaningful_langs:
        name = SCHOLAR_CONFIGS[lang]["language_name"]
        lang_lines.append(
            f"- {{scholar_analysis_{lang}}}: {name} cultural perspective analysis"
        )

    lang_names = ", ".join(
        SCHOLAR_CONFIGS[l]["language_name"] for l in meaningful_langs
    )
    return (
        "## Input: Scholar Analyses\n"
        f"Scholar analyses available for {len(meaningful_langs)} language(s): "
        f"{lang_names}.\n\n"
        + "\n".join(lang_lines)
    )


class DynamicPolymathBlock(BaseAgent):
    """アクティブ言語のみの instruction で Armchair Polymath を実行する。

    ゲート機能を内包: 有意な Scholar 分析がなければスキップ。
    """

    async def _run_async_impl(
        self, ctx: InvocationContext
    ) -> AsyncGenerator[Event, None]:
        state = ctx.session.state

        # 有意な分析がある言語を特定
        active_langs = state.get("active_languages", [])
        meaningful_langs = [
            lang
            for lang in active_langs
            if lang in SCHOLAR_CONFIGS
            and _is_meaningful(state.get(f"scholar_analysis_{lang}", ""))
        ]

        # ゲート: 有意な分析なし → INSUFFICIENT_DATA
        if not meaningful_langs:
            message = (
                "INSUFFICIENT_DATA: No meaningful Scholar analyses available. "
                "Pipeline terminated."
            )
            # _log_and_record_failure は CallbackContext（.state 属性）を期待する。
            # InvocationContext は ctx.session.state なので、アダプタとして
            # state 属性を持つ簡易オブジェクトを渡す。
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
            "DynamicPolymathBlock: %d 言語の分析で Polymath 実行: %s",
            len(meaningful_langs),
            ", ".join(meaningful_langs),
        )

        # アクティブ言語のみの instruction を動的に組み立て
        analyses_section = _build_analyses_section(meaningful_langs)
        instruction = INSTRUCTION_PREAMBLE + "\n" + analyses_section + "\n" + INSTRUCTION_BODY

        # LlmAgent を生成・実行
        polymath = LlmAgent(
            name="armchair_polymath",
            model=create_pro_model(),
            description=POLYMATH_DESCRIPTION,
            instruction=instruction,
            tools=POLYMATH_TOOLS,
            output_key="mystery_report",
        )
        async for event in polymath.run_async(ctx):
            yield event


def create_dynamic_polymath_block() -> DynamicPolymathBlock:
    """DynamicPolymathBlock を新規生成する。"""
    return DynamicPolymathBlock(
        name="dynamic_polymath_block",
        description=(
            "Dynamically builds Armchair Polymath instruction with only active "
            "language analyses. Integrates polymath gate: skips when no meaningful "
            "Scholar analyses are available."
        ),
    )
