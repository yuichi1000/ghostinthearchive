"""Ghost in the Archive - ADK Agent Definition

Defines root_agent (ghost_commander) as a SequentialAgent that orchestrates
the multilingual investigation pipeline:

  ThemeAnalyzer → ParallelLibrarians → ScholarBlock → DebateLoop
    → PolymathBlock → StorytellerBlock → PostStoryBlock

各言語エージェントは before_agent_callback で selected_languages をチェックし、
未選択の言語はスキップされる。DebateLoop は有意な分析が2言語以上の場合のみ実行される。
パイプラインゲートにより、前段が失敗した場合は後続をスキップしてトークン消費を抑制する。
PostStoryBlock では Illustrator と6言語翻訳が並列実行される。
"""

from google.adk.agents import LoopAgent, ParallelAgent, SequentialAgent

from .agents.armchair_polymath import armchair_polymath_agent
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
from .agents.storyteller import storyteller_agent
from .agents.theme_analyzer import theme_analyzer_agent
from .agents.translator import create_all_translators

# 言語別エージェントを生成
all_librarians = create_all_librarians()
all_scholars = create_all_scholars(mode="analysis")
all_scholars_debate = create_all_scholars(mode="debate")

# 全6言語の翻訳エージェントを生成
all_translators = create_all_translators()

# 討論ループ（LoopAgent: 最大2ラウンド、有意な分析が2言語未満ならスキップ）
debate_loop = LoopAgent(
    name="debate_loop",
    sub_agents=list(all_scholars_debate.values()),
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

root_agent = ghost_commander
