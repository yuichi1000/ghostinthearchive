"""DynamicScholarBlock — Librarian 結果に基づき Scholar を動的に生成・実行する。

AggregatorAgent が書き込む active_languages を読み取り、
ドキュメントが存在する言語のみ Scholar を生成する。

2層構造:
- Named Scholar: NAMED_SCHOLAR_LANGUAGES に含まれる言語は個別の Scholar を生成
- Multilingual Scholar: それ以外の言語は1体の Multilingual Scholar にまとめる

Phase 1: 分析 — Named Scholar（並列）+ Multilingual Scholar（1体）を並列実行
Phase 2: 討論 — 有意な分析が2件以上ある場合、討論ループを実行
          （最大 MAX_DEBATE_ITERATIONS 回、収束判定で早期終了可能）

討論の instruction には参加言語のみ記載し、肥大化を防ぐ。
収束判定は LLM を介さず純粋関数（is_debate_converged）で直接実行する。
"""

import logging
from collections.abc import AsyncGenerator

from google.adk.agents import BaseAgent, ParallelAgent
from google.adk.agents.invocation_context import InvocationContext
from google.adk.events.event import Event, EventActions
from google.genai import types

from shared.language_names import get_language_name

from ..tools.debate_tools import is_debate_converged
from .language_scholars import (
    NAMED_SCHOLAR_LANGUAGES,
    create_multilingual_scholar,
    create_scholar,
    get_scholar_config,
)
from .pipeline_gate import _is_meaningful

logger = logging.getLogger(__name__)

# 上限値
MAX_DEBATE_ITERATIONS = 2


class DynamicScholarBlock(BaseAgent):
    """Librarian 結果に基づき Scholar を動的に生成・実行する BaseAgent。

    2層構造:
    - Named Scholar: NAMED_SCHOLAR_LANGUAGES の言語は個別 Scholar
    - Multilingual Scholar: それ以外は1体にまとめて横断分析

    分析フェーズ後に有意な結果が2件以上あれば討論フェーズに進む。
    """

    async def _run_async_impl(
        self, ctx: InvocationContext
    ) -> AsyncGenerator[Event, None]:
        state = ctx.session.state

        # Aggregator が設定した active_languages を取得
        active_langs: list[str] = state.get("active_languages", [])

        if not active_langs:
            logger.warning("DynamicScholarBlock: ドキュメントなし — スキップ")
            yield Event(
                invocation_id=ctx.invocation_id,
                author=self.name,
                branch=ctx.branch,
                content=types.Content(
                    role="model",
                    parts=[types.Part(
                        text="INSUFFICIENT_DATA: No documents available for analysis."
                    )],
                ),
            )
            return

        # 2層振り分け
        named_langs = [l for l in active_langs if l in NAMED_SCHOLAR_LANGUAGES]
        other_langs = [l for l in active_langs if l not in NAMED_SCHOLAR_LANGUAGES]

        logger.info(
            "DynamicScholarBlock: 分析フェーズ開始 — Named %d (%s), Other %d (%s)",
            len(named_langs),
            ", ".join(named_langs),
            len(other_langs),
            ", ".join(other_langs),
        )

        # === Phase 1: 分析（並列） ===
        analysis_agents = [
            create_scholar(lang, mode="analysis") for lang in named_langs
        ]
        if other_langs:
            analysis_agents.append(
                create_multilingual_scholar(other_langs, mode="analysis")
            )

        parallel_analysis = ParallelAgent(
            name="dynamic_analysis",
            sub_agents=analysis_agents,
        )
        async for event in parallel_analysis.run_async(ctx):
            yield event

        # 有意な分析を出した Named Scholar を特定
        meaningful_named = [
            lang for lang in named_langs
            if _is_meaningful(state.get(f"scholar_analysis_{lang}", ""))
        ]
        # Multilingual Scholar の有意性チェック
        has_meaningful_multilingual = (
            bool(other_langs)
            and _is_meaningful(state.get("scholar_analysis_multilingual", ""))
        )

        # active_analyses_summary をステートに書き込み（ログ/診断用）
        summary_lines = []
        for lang in meaningful_named:
            lang_name = get_scholar_config(lang)["language_name"]
            summary_lines.append(f"- {lang_name} ({lang})")
        if has_meaningful_multilingual:
            ml_names = ", ".join(get_language_name(l) for l in other_langs)
            summary_lines.append(f"- Multilingual ({ml_names})")

        total_meaningful = len(meaningful_named) + (1 if has_meaningful_multilingual else 0)
        total_agents = len(named_langs) + (1 if other_langs else 0)

        if summary_lines:
            analyses_summary = (
                f"Scholar analyses available for {total_meaningful} source(s):\n"
                + "\n".join(summary_lines)
            )
        else:
            analyses_summary = "No meaningful Scholar analyses were produced."

        yield Event(
            invocation_id=ctx.invocation_id,
            author=self.name,
            branch=ctx.branch,
            content=types.Content(
                role="model",
                parts=[types.Part(
                    text=f"Analysis phase complete. {total_meaningful}/{total_agents} "
                    f"sources produced meaningful results."
                )],
            ),
            actions=EventActions(
                state_delta={"active_analyses_summary": analyses_summary},
            ),
        )

        # === Phase 2: 討論（有意な分析が2件以上の場合） ===
        if total_meaningful < 2:
            logger.info(
                "DynamicScholarBlock: 有意な分析 %d 件 — 討論スキップ",
                total_meaningful,
            )
            return

        # 討論参加リスト: Named の meaningful_langs + multilingual
        # debate の active_langs には Named + "multilingual" を含める
        debate_active_langs = list(meaningful_named)
        if has_meaningful_multilingual:
            debate_active_langs.append("multilingual")

        logger.info(
            "DynamicScholarBlock: 討論フェーズ開始 — %d 参加者: %s",
            len(debate_active_langs),
            ", ".join(debate_active_langs),
        )

        for iteration in range(MAX_DEBATE_ITERATIONS):
            debate_agents = [
                create_scholar(
                    lang,
                    mode="debate",
                    active_langs=debate_active_langs,
                )
                for lang in meaningful_named
            ]
            if has_meaningful_multilingual:
                debate_agents.append(
                    create_multilingual_scholar(
                        other_langs,
                        mode="debate",
                        active_named_langs=meaningful_named,
                    )
                )

            parallel_debate = ParallelAgent(
                name=f"dynamic_debate_{iteration}",
                sub_agents=debate_agents,
            )
            async for event in parallel_debate.run_async(ctx):
                yield event

            # 収束判定（LLM を介さず直接チェック）
            whiteboard = state.get("debate_whiteboard", "")
            if is_debate_converged(whiteboard):
                logger.info(
                    "DynamicScholarBlock: 討論収束 — ラウンド %d で終了",
                    iteration + 1,
                )
                break
        else:
            logger.info(
                "DynamicScholarBlock: 討論 — 最大 %d ラウンド完了",
                MAX_DEBATE_ITERATIONS,
            )


def create_dynamic_scholar_block() -> DynamicScholarBlock:
    """DynamicScholarBlock を新規生成する。"""
    return DynamicScholarBlock(
        name="dynamic_scholar_block",
        description=(
            "Dynamically creates and runs Scholar agents based on Aggregator's "
            "active_languages. Uses 2-layer architecture: Named Scholars for "
            "major languages + Multilingual Scholar for peripheral languages. "
            "Convergence checked directly without LLM."
        ),
    )
