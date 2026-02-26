"""DynamicScholarBlock — Librarian 結果に基づき Scholar を動的に生成・実行する。

AggregatorAgent が書き込む active_languages を読み取り、
ドキュメントが存在する言語のみ Scholar を生成する。

Phase 1: 分析 — 各言語の Scholar を並列実行
Phase 2: 討論 — 有意な分析が2言語以上ある場合、討論ループを実行
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

from ..tools.debate_tools import is_debate_converged
from .language_scholars import SCHOLAR_CONFIGS, create_scholar

logger = logging.getLogger(__name__)

# 失敗マーカー（pipeline_gate.py と同じ判定基準）
_FAILURE_MARKERS = frozenset({
    "NO_DOCUMENTS_FOUND",
    "INSUFFICIENT_DATA",
    "NO_CONTENT",
    "Not available",
})

# 上限値
MAX_LANGUAGES = 7
MAX_DEBATE_ITERATIONS = 2


def _is_meaningful(value: str) -> bool:
    """セッション状態の値が有意なデータを含むか判定する。"""
    if not value:
        return False
    text = str(value).strip()
    return not any(text.startswith(marker) for marker in _FAILURE_MARKERS)


class DynamicScholarBlock(BaseAgent):
    """Librarian 結果に基づき Scholar を動的に生成・実行する BaseAgent。

    active_languages から上位 MAX_LANGUAGES 言語を選び、
    SCHOLAR_CONFIGS に定義済みの言語のみ Scholar を生成する。

    分析フェーズ後に有意な結果が2言語以上あれば討論フェーズに進む。
    討論の instruction は参加言語のみ参照（肥大化防止）。
    """

    async def _run_async_impl(
        self, ctx: InvocationContext
    ) -> AsyncGenerator[Event, None]:
        state = ctx.session.state

        # Aggregator が設定した active_languages を取得
        active_langs = state.get("active_languages", [])[:MAX_LANGUAGES]

        # SCHOLAR_CONFIGS に定義がある言語のみ対象
        available_langs = [l for l in active_langs if l in SCHOLAR_CONFIGS]

        if not available_langs:
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

        logger.info(
            "DynamicScholarBlock: 分析フェーズ開始 — %d 言語: %s",
            len(available_langs),
            ", ".join(available_langs),
        )

        # === Phase 1: 分析（並列） ===
        analysis_scholars = [
            create_scholar(lang, mode="analysis") for lang in available_langs
        ]
        parallel_analysis = ParallelAgent(
            name="dynamic_analysis",
            sub_agents=analysis_scholars,
        )
        async for event in parallel_analysis.run_async(ctx):
            yield event

        # 有意な分析を出した言語を特定
        meaningful_langs = [
            lang for lang in available_langs
            if _is_meaningful(state.get(f"scholar_analysis_{lang}", ""))
        ]

        # active_analyses_summary をステートに書き込み（ログ/診断用プレーンテキスト）
        summary_lines = []
        for lang in meaningful_langs:
            lang_name = SCHOLAR_CONFIGS[lang]["language_name"]
            summary_lines.append(f"- {lang_name} ({lang})")

        if summary_lines:
            analyses_summary = (
                f"Scholar analyses available for {len(meaningful_langs)} language(s):\n"
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
                    text=f"Analysis phase complete. {len(meaningful_langs)}/{len(available_langs)} "
                    f"languages produced meaningful results."
                )],
            ),
            actions=EventActions(
                state_delta={"active_analyses_summary": analyses_summary},
            ),
        )

        # === Phase 2: 討論（有意な分析が2言語以上の場合） ===
        if len(meaningful_langs) < 2:
            logger.info(
                "DynamicScholarBlock: 有意な分析 %d 言語 — 討論スキップ",
                len(meaningful_langs),
            )
            return

        logger.info(
            "DynamicScholarBlock: 討論フェーズ開始 — %d 言語: %s",
            len(meaningful_langs),
            ", ".join(meaningful_langs),
        )

        for iteration in range(MAX_DEBATE_ITERATIONS):
            # 参加言語のみの動的 instruction で討論 Scholar を生成
            debate_scholars = [
                create_scholar(
                    lang,
                    mode="debate",
                    active_langs=meaningful_langs,
                )
                for lang in meaningful_langs
            ]
            parallel_debate = ParallelAgent(
                name=f"dynamic_debate_{iteration}",
                sub_agents=debate_scholars,
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
            "active_languages. Runs analysis in parallel, then debate loop "
            "for languages with meaningful results. Convergence checked directly "
            "without LLM."
        ),
    )
