"""DynamicPolymathBlock — Armchair Polymath の動的 instruction 構築。

アクティブ言語の Scholar 分析のみを instruction に含め、
非アクティブ言語の空プレースホルダーを排除する。
DynamicScholarBlock と同じ BaseAgent パターン。

Named Scholar + Multilingual Scholar の両方の分析結果を動的に参照。

ゲート機能を内包: 全 Scholar 分析が空なら INSUFFICIENT_DATA を返す。
語数ティア: ソース素材の豊富さに応じて語数要件を動的に決定する。
"""

import logging
from collections.abc import AsyncGenerator
from typing import Any, NamedTuple

from google.adk.agents import BaseAgent, LlmAgent
from google.adk.agents.invocation_context import InvocationContext
from google.adk.events.event import Event
from google.genai import types

from shared.constants import is_meaningful
from shared.model_config import create_pro_model
from shared.state_keys import (
    ACTIVE_LANGUAGES,
    RAW_SEARCH_RESULTS,
    WORD_COUNT_TIER,
    scholar_analysis_key,
)

from .armchair_polymath import (
    INSTRUCTION_BODY,
    INSTRUCTION_PREAMBLE,
    POLYMATH_DESCRIPTION,
    POLYMATH_MAX_OUTPUT_TOKENS,
    POLYMATH_TOOLS,
    log_polymath_tool_call,
)
from .language_scholars import get_scholar_config
from .pipeline_gate import _log_and_record_failure

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# 語数ティア定義
# ---------------------------------------------------------------------------
class WordCountTier(NamedTuple):
    """語数ティア（min_words, max_words）。"""

    min_words: int
    max_words: int


TIER_NORMAL = WordCountTier(5000, 10000)
TIER_REDUCED = WordCountTier(2500, 5000)

# ティア判定閾値
QUALITY_DOC_THRESHOLD = 10  # keywords_matched 非空の文書数
SCHOLAR_WORDS_THRESHOLD = 3000  # Scholar 分析合計語数


def _count_quality_documents(state: dict[str, Any]) -> int:
    """raw_search_results から keywords_matched 非空の文書数をカウントする（URL 重複排除）。"""
    seen_urls: set[str] = set()

    def _scan_results(results: list) -> None:
        for result in results:
            if not isinstance(result, dict):
                continue
            for doc in result.get("documents", []):
                if not isinstance(doc, dict):
                    continue
                url = doc.get("source_url", "")
                if not url or url in seen_urls:
                    continue
                if doc.get("keywords_matched"):
                    seen_urls.add(url)

    # ベースキー
    base = state.get(RAW_SEARCH_RESULTS)
    if base and isinstance(base, list):
        _scan_results(base)

    # 言語別キー（raw_search_results_{identifier}）
    for key in list(state.keys()):
        if key.startswith(RAW_SEARCH_RESULTS + "_") and key != RAW_SEARCH_RESULTS:
            lang_results = state.get(key)
            if lang_results and isinstance(lang_results, list):
                _scan_results(lang_results)

    return len(seen_urls)


def _count_scholar_words(
    state: dict[str, Any],
    meaningful_langs: list[str],
    has_multilingual: bool,
) -> int:
    """有意な Scholar 分析テキストの合計語数を返す。"""
    total = 0
    langs = list(meaningful_langs)
    if has_multilingual:
        langs.append("multilingual")

    for lang in langs:
        text = state.get(scholar_analysis_key(lang), "")
        if not text or not is_meaningful(str(text)):
            continue
        total += len(str(text).split())

    return total


def assess_source_richness(
    state: dict[str, Any],
    meaningful_langs: list[str],
    has_multilingual: bool,
) -> WordCountTier:
    """ソース素材の豊富さに応じて語数ティアを決定する。

    A（質の高い文書数）< QUALITY_DOC_THRESHOLD **かつ**
    B（Scholar 分析語数）< SCHOLAR_WORDS_THRESHOLD の場合のみ Reduced。
    """
    quality_docs = _count_quality_documents(state)
    scholar_words = _count_scholar_words(state, meaningful_langs, has_multilingual)

    if quality_docs < QUALITY_DOC_THRESHOLD and scholar_words < SCHOLAR_WORDS_THRESHOLD:
        logger.info(
            "語数ティア: Reduced（quality_docs=%d, scholar_words=%d）",
            quality_docs,
            scholar_words,
        )
        return TIER_REDUCED

    logger.info(
        "語数ティア: Normal（quality_docs=%d, scholar_words=%d）",
        quality_docs,
        scholar_words,
    )
    return TIER_NORMAL


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
        active_langs = state.get(ACTIVE_LANGUAGES, [])
        meaningful_langs = [
            lang
            for lang in active_langs
            if is_meaningful(state.get(scholar_analysis_key(lang), ""))
        ]

        # Multilingual Scholar の有意性チェック
        has_multilingual = is_meaningful(
            state.get(scholar_analysis_key("multilingual"), "")
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

        # ティア決定 + セッション状態に保存
        tier = assess_source_richness(state, meaningful_langs, has_multilingual)
        state[WORD_COUNT_TIER] = {
            "min_words": tier.min_words,
            "max_words": tier.max_words,
        }

        # アクティブ言語のみの instruction を動的に組み立て（ティアを注入）
        analyses_section = _build_analyses_section(meaningful_langs, has_multilingual)
        body = INSTRUCTION_BODY.replace(
            "{__WORD_COUNT_MIN__}", str(tier.min_words)
        ).replace("{__WORD_COUNT_MAX__}", str(tier.max_words))
        instruction = INSTRUCTION_PREAMBLE + "\n" + analyses_section + "\n" + body

        # LlmAgent を生成・実行
        polymath = LlmAgent(
            name="armchair_polymath",
            model=create_pro_model(),
            description=POLYMATH_DESCRIPTION,
            instruction=instruction,
            tools=POLYMATH_TOOLS,
            output_key="mystery_report",
            generate_content_config=types.GenerateContentConfig(
                temperature=0.5,
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
