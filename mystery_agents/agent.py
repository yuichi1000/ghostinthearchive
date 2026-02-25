"""Ghost in the Archive - ADK Agent Definition

Defines root_agent (ghost_commander) as a SequentialAgent that orchestrates
the multilingual investigation pipeline:

  ParallelLibrarians → ScholarBlock → DebateLoop
    → PolymathBlock → StorytellerBlock → PostStoryBlock

全7言語の Librarian/Scholar を常時実行し、パイプラインゲートが
結果なしの言語を自動スキップする。DebateLoop は有意な分析が2言語以上の場合のみ実行。
PostStoryBlock では Illustrator と6言語翻訳が並列実行される。

DebateLoop 内部は SequentialAgent(debate_round) で構成:
  parallel_debate_scholars → convergence_checker
収束判定により新規論点が枯渇した場合、max_iterations 前にループを早期終了する。

build_pipeline() は全エージェントを毎回新規生成するファクトリ関数。
ADK の単一親制約に違反しないよう、同一インスタンスを複数の親に割り当てない。
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from google.adk.agents import LoopAgent, ParallelAgent, SequentialAgent
from google.genai import types

from .agents.armchair_polymath import create_armchair_polymath
from .agents.convergence_checker import create_convergence_checker
from .agents.illustrator import create_illustrator
from .agents.language_gate import make_debate_loop_gate
from .agents.language_librarians import create_all_librarians
from .agents.language_scholars import create_all_scholars
from .agents.pipeline_gate import (
    make_polymath_gate,
    make_post_story_gate,
    make_scholar_gate,
    make_storyteller_gate,
)
from .agents.publisher import create_publisher
from .agents.storyteller import create_storyteller
from .agents.translator import create_all_translators
from shared.constants import ALLOWED_LANGUAGES
from shared.model_config import DEFAULT_STORYTELLER

if TYPE_CHECKING:
    from google.adk.agents.callback_context import CallbackContext

# パイプライン説明文（build_pipeline 内で共有）
_PIPELINE_DESCRIPTION = (
    "Ghost in the Archive multilingual blog creation pipeline. "
    "Executes ParallelLibrarians(7 languages) → ScholarBlock → DebateLoop "
    "→ PolymathBlock → StorytellerBlock → PostStoryBlock "
    "to research, analyze, debate, create content, generate images, "
    "translate to 3 languages (ja/es/de) in parallel, "
    "and publish historical mysteries and folkloric anomalies. "
    "Pipeline gates skip downstream agents when upstream stages fail."
)

# オーケストレーター/パラレルエージェントはログ対象外
# 実際にテキストを生成するリーフエージェントのみ進捗表示する
SKIP_AUTHORS = {
    "ghost_commander",
    "parallel_librarians",
    "parallel_scholars",
    "parallel_debate_scholars",
    "debate_loop",
    "debate_round",
    "parallel_translators",
    "scholar_block",
    "polymath_block",
    "storyteller_block",
    "post_story_block",
    "post_story_parallel",
}


def _initialize_pipeline_state(
    callback_context: CallbackContext,
) -> Optional[types.Content]:
    """パイプライン状態を初期化する（ThemeAnalyzer の代替）。

    全7言語を常時実行するため、selected_languages を全言語リストで初期化。
    下流のゲート・討論ロジックとの互換性を維持する。
    """
    callback_context.state["selected_languages"] = sorted(ALLOWED_LANGUAGES)
    callback_context.state["debate_whiteboard"] = ""
    callback_context.state["structured_report"] = {}
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
    cc = create_convergence_checker()
    il = create_illustrator()
    pub = create_publisher()
    st = create_storyteller(storyteller)

    # ファクトリエージェント（既に毎回新規生成）
    libs = create_all_librarians()
    scholars_analysis = create_all_scholars(mode="analysis")
    scholars_debate = create_all_scholars(mode="debate")
    translators = create_all_translators()

    # 討論ラウンド: 全 Scholar が並列で議論 → 収束判定
    debate_round = SequentialAgent(
        name="debate_round",
        sub_agents=[
            ParallelAgent(
                name="parallel_debate_scholars",
                sub_agents=list(scholars_debate.values()),
            ),
            cc,
        ],
    )

    # 討論ループ（LoopAgent: 最大2ラウンド、有意な分析が2言語未満ならスキップ）
    debate_loop = LoopAgent(
        name="debate_loop",
        sub_agents=[debate_round],
        max_iterations=2,
        before_agent_callback=make_debate_loop_gate(),
    )

    # Scholar ブロック（全 Librarian 失敗時にスキップ）
    scholar_block = SequentialAgent(
        name="scholar_block",
        sub_agents=[
            ParallelAgent(
                name="parallel_scholars",
                sub_agents=list(scholars_analysis.values()),
            ),
        ],
        before_agent_callback=make_scholar_gate(),
    )

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
                name="parallel_librarians",
                sub_agents=list(libs.values()),
            ),
            scholar_block,
            debate_loop,
            polymath_block,
            storyteller_block,
            post_story_block,
        ],
        before_agent_callback=_initialize_pipeline_state,
    )


# モジュールレベル（1回だけ構築 — ADK CLI / adk web 用）
ghost_commander = build_pipeline()
root_agent = ghost_commander
