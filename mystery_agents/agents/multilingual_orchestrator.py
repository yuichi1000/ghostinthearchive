"""MultilingualOrchestrator - テーマに応じた動的言語エージェント選択・実行

ADK の BaseAgent を継承した CustomAgent。
ThemeAnalyzer の結果に基づいて、必要な言語の Librarian / Scholar のみを
並列実行し、CrossReferenceScholar で統合する。

実行フロー:
1. ThemeAnalyzer → selected_languages を session state に保存
2. 選択された言語の Librarian を ParallelAgent で並列実行
3. 選択された言語の Scholar を ParallelAgent で並列実行
4. CrossReferenceScholar で全言語の分析を統合
"""

import logging
from typing import AsyncGenerator

from google.adk.agents import BaseAgent, ParallelAgent
from google.adk.agents.invocation_context import InvocationContext
from google.adk.events.event import Event

logger = logging.getLogger(__name__)


class MultilingualOrchestrator(BaseAgent):
    """テーマに応じて言語エージェントを動的に選択・実行する。"""

    # Pydantic model_config で任意の属性を許可
    model_config = {"arbitrary_types_allowed": True}

    # カスタム属性（BaseAgent の sub_agents とは別に保持）
    theme_analyzer: BaseAgent
    all_librarians: dict[str, BaseAgent]
    all_scholars: dict[str, BaseAgent]
    cross_reference_scholar: BaseAgent

    def __init__(
        self,
        theme_analyzer: BaseAgent,
        all_librarians: dict[str, BaseAgent],
        all_scholars: dict[str, BaseAgent],
        cross_reference_scholar: BaseAgent,
        **kwargs,
    ):
        # 全エージェントを sub_agents として登録（ADK のエージェント階層管理）
        all_sub = [theme_analyzer, cross_reference_scholar]
        all_sub += list(all_librarians.values())
        all_sub += list(all_scholars.values())

        super().__init__(
            sub_agents=all_sub,
            theme_analyzer=theme_analyzer,
            all_librarians=all_librarians,
            all_scholars=all_scholars,
            cross_reference_scholar=cross_reference_scholar,
            **kwargs,
        )

    async def _run_async_impl(
        self, ctx: InvocationContext
    ) -> AsyncGenerator[Event, None]:
        # 1. ThemeAnalyzer でテーマ分析・言語選択
        logger.info("Starting ThemeAnalyzer...")
        async for event in self.theme_analyzer.run_async(ctx):
            yield event

        # 2. 選択された言語を取得（ガード: フォールバック ["en"]）
        selected = ctx.session.state.get("selected_languages", ["en"])
        if not isinstance(selected, list) or not selected:
            selected = ["en"]
        logger.info(f"Selected languages: {selected}")

        # 3. 選択された言語の Librarian を並列実行
        librarians = [
            self.all_librarians[lang]
            for lang in selected
            if lang in self.all_librarians
        ]
        if librarians:
            logger.info(
                f"Running {len(librarians)} Librarians in parallel: "
                f"{[a.name for a in librarians]}"
            )
            parallel_lib = ParallelAgent(
                name="parallel_librarians",
                sub_agents=librarians,
            )
            async for event in parallel_lib.run_async(ctx):
                yield event

        # 4. 選択された言語の Scholar を並列実行
        scholars = [
            self.all_scholars[lang]
            for lang in selected
            if lang in self.all_scholars
        ]
        if scholars:
            logger.info(
                f"Running {len(scholars)} Scholars in parallel: "
                f"{[a.name for a in scholars]}"
            )
            parallel_sch = ParallelAgent(
                name="parallel_scholars",
                sub_agents=scholars,
            )
            async for event in parallel_sch.run_async(ctx):
                yield event

        # 5. CrossReferenceScholar で統合
        logger.info("Running CrossReferenceScholar...")
        async for event in self.cross_reference_scholar.run_async(ctx):
            yield event
