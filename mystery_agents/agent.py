"""Ghost in the Archive - ADK Agent Definition

Defines root_agent (ghost_commander) as a SequentialAgent that orchestrates
the multilingual investigation pipeline:

  ParallelAPILibrarians → Aggregator → DynamicScholarBlock
    → PolymathBlock → StorytellerBlock → PostStoryBlock

API ベース Librarian（7グループ）が並列で検索し、AggregatorAgent が
検索結果を言語別に集約。DynamicScholarBlock が active_languages に基づき
Scholar を動的に生成・実行し、分析→討論を一貫制御する。
PostStoryBlock では Illustrator と3言語翻訳が並列実行される。

DynamicScholarBlock 内部:
  Phase 1: 並列分析（active_languages から Scholar を動的生成）
  Phase 2: 討論ループ（有意な分析 ≧ 2 言語、最大2ラウンド、収束判定で早期終了）
収束判定は LLM を介さず純粋関数で直接実行する。

build_pipeline() は全エージェントを毎回新規生成するファクトリ関数。
ADK の単一親制約に違反しないよう、同一インスタンスを複数の親に割り当てない。
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from google.adk.agents import ParallelAgent, SequentialAgent
from google.genai import types

from .agents.aggregator import create_aggregator
from .agents.language_scholars import SCHOLAR_CONFIGS
from .agents.api_librarians import create_all_api_librarians
from .agents.armchair_polymath import create_armchair_polymath
from .agents.dynamic_scholar_block import create_dynamic_scholar_block
from .agents.illustrator import create_illustrator
from .agents.pipeline_gate import (
    make_polymath_gate,
    make_post_story_gate,
    make_storyteller_gate,
)
from .agents.publisher import create_publisher
from .agents.storyteller import create_storyteller
from .agents.translator import create_all_translators
from shared.model_config import DEFAULT_STORYTELLER

if TYPE_CHECKING:
    from google.adk.agents.callback_context import CallbackContext

# パイプライン説明文（build_pipeline 内で共有）
_PIPELINE_DESCRIPTION = (
    "Ghost in the Archive multilingual blog creation pipeline. "
    "Executes ParallelAPILibrarians(7 API groups) → Aggregator "
    "→ DynamicScholarBlock(analysis + debate) → PolymathBlock "
    "→ StorytellerBlock → PostStoryBlock "
    "to research, analyze, debate, create content, generate images, "
    "translate to 3 languages (ja/es/de) in parallel, "
    "and publish historical mysteries and folkloric anomalies. "
    "DynamicScholarBlock dynamically creates Scholars for active languages only. "
    "Pipeline gates skip downstream agents when upstream stages fail."
)

# オーケストレーター/パラレルエージェントはログ対象外
# 実際にテキストを生成するリーフエージェントのみ進捗表示する
SKIP_AUTHORS = {
    "ghost_commander",
    "parallel_api_librarians",
    "aggregator",
    # DynamicScholarBlock 内部のオーケストレーターエージェント
    "dynamic_scholar_block",
    "dynamic_analysis",
    "dynamic_debate_0",
    "dynamic_debate_1",
    # 並列翻訳・後処理ブロック
    "parallel_translators",
    "polymath_block",
    "storyteller_block",
    "post_story_block",
    "post_story_parallel",
}


def _initialize_pipeline_state(
    callback_context: CallbackContext,
) -> Optional[types.Content]:
    """パイプライン状態を初期化する。

    API ベース Librarian は言語選択不要（テーマから自律判断）。
    selected_languages は AggregatorAgent が検索結果から動的に設定するため、
    ここでは空リストで初期化する。
    """
    callback_context.state["selected_languages"] = []
    callback_context.state["debate_whiteboard"] = ""
    callback_context.state["structured_report"] = {}
    # Armchair Polymath の instruction が全言語の {scholar_analysis_{lang}} を
    # 参照するため、未実行言語でも ADK のプレースホルダー解決が失敗しないよう
    # 全言語キーを空文字列で初期化する
    for lang in SCHOLAR_CONFIGS:
        callback_context.state[f"scholar_analysis_{lang}"] = ""
    callback_context.state["active_analyses_summary"] = ""
    return None  # 実行続行


def build_pipeline(storyteller: str = DEFAULT_STORYTELLER) -> SequentialAgent:
    """パイプラインを新規構築する。毎回新しいエージェントインスタンスを生成。

    ADK の単一親制約（Agent already has a parent agent）を回避するため、
    全エージェントを毎回新規生成する。同一インスタンスを複数の親に追加しない。

    Args:
        storyteller: ストーリーテラー名（STORYTELLER_MODELS のキー）

    Returns:
        構築済みパイプライン（SequentialAgent）
    """
    # リーフエージェント（毎回新規生成）
    ap = create_armchair_polymath()
    il = create_illustrator()
    pub = create_publisher()
    st = create_storyteller(storyteller)
    agg = create_aggregator()

    # ファクトリエージェント（既に毎回新規生成）
    api_libs = create_all_api_librarians()
    translators = create_all_translators()

    # DynamicScholarBlock: 分析 + 討論を一貫制御
    # active_languages に基づき Scholar を動的生成、
    # 有意な分析が2言語以上なら討論ループ（収束判定付き）
    dsb = create_dynamic_scholar_block()

    # ArmchairPolymath ブロック（全 Scholar 失敗時にスキップ）
    polymath_block = SequentialAgent(
        name="polymath_block",
        sub_agents=[ap],
        before_agent_callback=make_polymath_gate(),
    )

    # Storyteller ブロック（mystery_report 空ならスキップ）
    storyteller_block = SequentialAgent(
        name="storyteller_block",
        sub_agents=[st],
        before_agent_callback=make_storyteller_gate(),
    )

    # Illustrator と翻訳を並列実行（どちらも creative_content を読むだけで独立）
    post_story_parallel = ParallelAgent(
        name="post_story_parallel",
        sub_agents=[
            il,
            ParallelAgent(
                name="parallel_translators",
                sub_agents=list(translators.values()),
            ),
        ],
    )

    # PostStoryBlock: 並列処理 → Publisher（creative_content 空ならスキップ）
    post_story_block = SequentialAgent(
        name="post_story_block",
        sub_agents=[
            post_story_parallel,
            pub,
        ],
        before_agent_callback=make_post_story_gate(),
    )

    # メインパイプライン
    return SequentialAgent(
        name="ghost_commander",
        description=_PIPELINE_DESCRIPTION,
        sub_agents=[
            ParallelAgent(
                name="parallel_api_librarians",
                sub_agents=api_libs,
            ),
            agg,
            dsb,
            polymath_block,
            storyteller_block,
            post_story_block,
        ],
        before_agent_callback=_initialize_pipeline_state,
    )


# モジュールレベル（1回だけ構築 — ADK CLI / adk web 用）
ghost_commander = build_pipeline()
root_agent = ghost_commander
