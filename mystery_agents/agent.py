"""Ghost in the Archive - ADK Agent Definition

Defines root_agent (ghost_commander) as a SequentialAgent that orchestrates
the multilingual investigation pipeline:

  BatchedAPILibrarians → Aggregator → DynamicScholarBlock
    → DynamicPolymathBlock → StorytellerBlock → PostStoryBlock

API ベース Librarian（6グループ）を2バッチ（3+2）に分割して逐次実行し、
Vertex AI QPM レートリミットを回避する。AggregatorAgent が検索結果を
言語別に集約。DynamicScholarBlock が active_languages に基づき
Scholar を動的に生成・実行し、分析→討論を一貫制御する。
DynamicPolymathBlock がアクティブ言語のみの instruction で Polymath を実行。
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
from .agents.api_librarians import create_all_api_librarians
from .agents.dynamic_polymath_block import create_dynamic_polymath_block
from .agents.dynamic_scholar_block import create_dynamic_scholar_block
from .agents.illustrator import create_illustrator
from .agents.pipeline_gate import (
    make_post_story_gate,
    make_storyteller_gate,
)
from .agents.publisher import create_publisher
from .agents.storyteller import create_storyteller
from .agents.translator import create_all_translators
from shared.model_config import DEFAULT_STORYTELLER
from shared.state_keys import (
    APPROVED_ARCHIVE_IMAGES,
    DEBATE_WHITEBOARD,
    SELECTED_LANGUAGES,
    STRUCTURED_REPORT,
)

if TYPE_CHECKING:
    from google.adk.agents.callback_context import CallbackContext

# パイプライン説明文（build_pipeline 内で共有）
_PIPELINE_DESCRIPTION = (
    "Ghost in the Archive multilingual blog creation pipeline. "
    "Executes BatchedAPILibrarians(6 API groups in 2 batches) → Aggregator "
    "→ DynamicScholarBlock(analysis + debate) → DynamicPolymathBlock "
    "→ StorytellerBlock → PostStoryBlock "
    "to research, analyze, debate, create content, generate images, "
    "translate to 3 languages (ja/es/de) in parallel, "
    "and publish historical mysteries and folkloric anomalies. "
    "DynamicScholarBlock dynamically creates Scholars for active languages only. "
    "DynamicPolymathBlock builds Polymath instruction with active languages only. "
    "Pipeline gates skip downstream agents when upstream stages fail."
)

# Vertex AI QPM 対策: 6並列 → 2バッチに分割して逐次実行
# ParallelAgent は全 sub_agents を同時起動するため、5 Librarian が同時に
# gemini-2.5-flash を呼び出すと QPM を超過する。SequentialAgent で
# 2バッチに分けることで同時リクエスト数を半減させる。
_LIBRARIAN_BATCH_SIZE = 3

# オーケストレーター/パラレルエージェントはログ対象外
# 実際にテキストを生成するリーフエージェントのみ進捗表示する
SKIP_AUTHORS = {
    "ghost_commander",
    "batched_api_librarians",
    "parallel_api_librarians_batch_1",
    "parallel_api_librarians_batch_2",
    "aggregator",
    # Librarian SequentialAgent ブロック（Round 1 + Round 2 のラッパー）
    "librarian_us_archives_block",
    "librarian_europeana_block",
    "librarian_internet_archive_block",
    "librarian_ndl_block",
    "librarian_delpher_block",
    "librarian_trove_block",
    # DynamicScholarBlock / DynamicPolymathBlock 内部のオーケストレーターエージェント
    "dynamic_scholar_block",
    "dynamic_analysis",
    "dynamic_debate_0",
    "dynamic_debate_1",
    "dynamic_polymath_block",
    # 並列翻訳・後処理ブロック
    "parallel_translators",
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
    callback_context.state[SELECTED_LANGUAGES] = []
    callback_context.state[DEBATE_WHITEBOARD] = ""
    callback_context.state[STRUCTURED_REPORT] = {}
    # Polymath が save_structured_report を呼ばなかった場合のフォールバック
    callback_context.state[APPROVED_ARCHIVE_IMAGES] = []
    # scholar_analysis_* は DynamicPolymathBlock が動的に参照するため初期化不要
    # active_analyses_summary は DynamicScholarBlock が設定するため初期化不要
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
    il = create_illustrator()
    pub = create_publisher()
    st = create_storyteller(storyteller)
    agg = create_aggregator()

    # ファクトリエージェント（既に毎回新規生成）
    api_libs = create_all_api_librarians()  # 6 SequentialAgent（各 R1+R2）
    translators = create_all_translators()

    # DynamicScholarBlock: 分析 + 討論を一貫制御
    # active_languages に基づき Scholar を動的生成、
    # 有意な分析が2言語以上なら討論ループ（収束判定付き）
    dsb = create_dynamic_scholar_block()

    # DynamicPolymathBlock: アクティブ言語のみの instruction で Polymath 実行
    # ゲート機能内包（全 Scholar 失敗時にスキップ）
    dpb = create_dynamic_polymath_block()

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

    # Librarian バッチ分割: 6並列 → 2バッチ（3+2）逐次実行
    # Vertex AI QPM 超過を回避するため SequentialAgent でバッチを順番に実行
    batched_librarians = SequentialAgent(
        name="batched_api_librarians",
        sub_agents=[
            ParallelAgent(
                name="parallel_api_librarians_batch_1",
                sub_agents=api_libs[:_LIBRARIAN_BATCH_SIZE],
            ),
            ParallelAgent(
                name="parallel_api_librarians_batch_2",
                sub_agents=api_libs[_LIBRARIAN_BATCH_SIZE:],
            ),
        ],
    )

    # メインパイプライン
    return SequentialAgent(
        name="ghost_commander",
        description=_PIPELINE_DESCRIPTION,
        sub_agents=[
            batched_librarians,
            agg,
            dsb,
            dpb,
            storyteller_block,
            post_story_block,
        ],
        before_agent_callback=_initialize_pipeline_state,
    )


# モジュールレベル（1回だけ構築 — ADK CLI / adk web 用）
ghost_commander = build_pipeline()
root_agent = ghost_commander
