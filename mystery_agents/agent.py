"""Ghost in the Archive - ADK Agent Definition

Defines root_agent (ghost_commander) as a SequentialAgent that orchestrates
the multilingual investigation pipeline:

  ThemeAnalyzer → ParallelLibrarians → ScholarBlock → DebateLoop
    → PolymathBlock → StorytellerBlock → PostStoryBlock

各言語エージェントは before_agent_callback で selected_languages をチェックし、
未選択の言語はスキップされる。DebateLoop は有意な分析が2言語以上の場合のみ実行される。
パイプラインゲートにより、前段が失敗した場合は後続をスキップしてトークン消費を抑制する。
PostStoryBlock では Illustrator と6言語翻訳が並列実行される。

DebateLoop 内部は SequentialAgent(debate_round) で構成:
  parallel_debate_scholars → convergence_checker
収束判定により新規論点が枯渇した場合、max_iterations 前にループを早期終了する。
"""

from google.adk.agents import LoopAgent, ParallelAgent, SequentialAgent

from .agents.armchair_polymath import armchair_polymath_agent
from .agents.convergence_checker import convergence_checker_agent
from .agents.illustrator import illustrator_agent
from .agents.language_gate import make_debate_loop_gate
from .agents.language_librarians import create_all_librarians
from .agents.language_scholars import create_all_scholars
from .agents.pipeline_gate import (
    make_polymath_gate,
    make_post_story_gate,
    make_scholar_gate,
    make_storyteller_gate,
)
from .agents.publisher import publisher_agent
from .agents.storyteller import create_storyteller, storyteller_agent
from .agents.theme_analyzer import theme_analyzer_agent
from .agents.translator import create_all_translators
from shared.model_config import DEFAULT_STORYTELLER

# 言語別エージェントを生成
all_librarians = create_all_librarians()
all_scholars = create_all_scholars(mode="analysis")
all_scholars_debate = create_all_scholars(mode="debate")

# 全6言語の翻訳エージェントを生成
all_translators = create_all_translators()

# 討論ラウンド: 全 Scholar が並列で議論 → 収束判定
# SequentialAgent でラップし、convergence_checker の escalate で早期終了可能にする
debate_round = SequentialAgent(
    name="debate_round",
    sub_agents=[
        ParallelAgent(
            name="parallel_debate_scholars",
            sub_agents=list(all_scholars_debate.values()),
        ),
        convergence_checker_agent,
    ],
)

# 討論ループ（LoopAgent: 最大2ラウンド、有意な分析が2言語未満ならスキップ）
# 収束判定により max_iterations 前に早期終了する場合がある
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
            sub_agents=list(all_scholars.values()),
        ),
    ],
    before_agent_callback=make_scholar_gate(),
)

# ArmchairPolymath ブロック（全 Scholar 失敗時にスキップ）
polymath_block = SequentialAgent(
    name="polymath_block",
    sub_agents=[armchair_polymath_agent],
    before_agent_callback=make_polymath_gate(),
)

# Storyteller ブロック（mystery_report 空ならスキップ）
storyteller_block = SequentialAgent(
    name="storyteller_block",
    sub_agents=[storyteller_agent],
    before_agent_callback=make_storyteller_gate(),
)

# Illustrator と翻訳を並列実行（どちらも creative_content を読むだけで独立）
post_story_parallel = ParallelAgent(
    name="post_story_parallel",
    sub_agents=[
        illustrator_agent,
        ParallelAgent(
            name="parallel_translators",
            sub_agents=list(all_translators.values()),
        ),
    ],
)

# PostStoryBlock: 並列処理 → Publisher（creative_content 空ならスキップ）
post_story_block = SequentialAgent(
    name="post_story_block",
    sub_agents=[
        post_story_parallel,
        publisher_agent,
    ],
    before_agent_callback=make_post_story_gate(),
)

# メインパイプライン
ghost_commander = SequentialAgent(
    name="ghost_commander",
    description=(
        "Ghost in the Archive multilingual blog creation pipeline. "
        "Executes ThemeAnalyzer → ParallelLibrarians → ScholarBlock → DebateLoop "
        "→ PolymathBlock → StorytellerBlock → PostStoryBlock "
        "to research, analyze, debate, create content, generate images, "
        "translate to 6 languages (ja/es/de/fr/nl/pt) in parallel, "
        "and publish historical mysteries and folkloric anomalies. "
        "Pipeline gates skip downstream agents when upstream stages fail."
    ),
    sub_agents=[
        theme_analyzer_agent,
        ParallelAgent(
            name="parallel_librarians",
            sub_agents=list(all_librarians.values()),
        ),
        scholar_block,
        debate_loop,
        polymath_block,
        storyteller_block,
        post_story_block,
    ],
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

root_agent = ghost_commander


def build_pipeline(storyteller: str = DEFAULT_STORYTELLER) -> SequentialAgent:
    """ストーリーテラー指定でパイプラインを構築する。

    デフォルトストーリーテラー以外が指定された場合のみ Storyteller を再生成する。
    Storyteller 以外のエージェントはステートレスなので共有再利用する。

    Args:
        storyteller: ストーリーテラー名（STORYTELLER_MODELS のキー）

    Returns:
        構築済みパイプライン（SequentialAgent）
    """
    st = create_storyteller(storyteller) if storyteller != DEFAULT_STORYTELLER else storyteller_agent

    custom_storyteller_block = SequentialAgent(
        name="storyteller_block",
        sub_agents=[st],
        before_agent_callback=make_storyteller_gate(),
    )

    custom_post_story_block = SequentialAgent(
        name="post_story_block",
        sub_agents=[
            post_story_parallel,
            publisher_agent,
        ],
        before_agent_callback=make_post_story_gate(),
    )

    return SequentialAgent(
        name="ghost_commander",
        description=ghost_commander.description,
        sub_agents=[
            theme_analyzer_agent,
            ParallelAgent(
                name="parallel_librarians",
                sub_agents=list(all_librarians.values()),
            ),
            scholar_block,
            debate_loop,
            polymath_block,
            custom_storyteller_block,
            custom_post_story_block,
        ],
    )
