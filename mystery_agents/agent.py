"""Ghost in the Archive - ADK Agent Definition

Defines root_agent (ghost_commander) as a SequentialAgent that orchestrates
the multilingual investigation pipeline:

  ThemeAnalyzer → ParallelLibrarians → ParallelScholars → DebateLoop
    → ArmchairPolymath → Storyteller → Illustrator → Translator → Publisher

各言語エージェントは before_agent_callback で selected_languages をチェックし、
未選択の言語はスキップされる。DebateLoop は有意な分析が2言語以上の場合のみ実行される。
"""

from google.adk.agents import LoopAgent, ParallelAgent, SequentialAgent

from .agents.armchair_polymath import armchair_polymath_agent
from .agents.illustrator import illustrator_agent
from .agents.language_gate import make_debate_loop_gate
from .agents.language_librarians import create_all_librarians
from .agents.language_scholars import create_all_scholars
from .agents.publisher import publisher_agent
from .agents.storyteller import storyteller_agent
from .agents.theme_analyzer import theme_analyzer_agent

from translator_agents.agents.translator import translator_agent

# 言語別エージェントを生成
all_librarians = create_all_librarians()
all_scholars = create_all_scholars(mode="analysis")
all_scholars_debate = create_all_scholars(mode="debate")

# 討論ループ（LoopAgent: 最大2ラウンド、有意な分析が2言語未満ならスキップ）
debate_loop = LoopAgent(
    name="debate_loop",
    sub_agents=list(all_scholars_debate.values()),
    max_iterations=2,
    before_agent_callback=make_debate_loop_gate(),
)

# メインパイプライン
ghost_commander = SequentialAgent(
    name="ghost_commander",
    description=(
        "Ghost in the Archive multilingual blog creation pipeline. "
        "Executes ThemeAnalyzer → ParallelLibrarians → ParallelScholars → DebateLoop "
        "→ ArmchairPolymath → Storyteller → Illustrator → Translator → Publisher "
        "to research, analyze, debate, create content, generate images, translate to Japanese, "
        "and publish historical mysteries and folkloric anomalies."
    ),
    sub_agents=[
        theme_analyzer_agent,
        ParallelAgent(
            name="parallel_librarians",
            sub_agents=list(all_librarians.values()),
        ),
        ParallelAgent(
            name="parallel_scholars",
            sub_agents=list(all_scholars.values()),
        ),
        debate_loop,
        armchair_polymath_agent,
        storyteller_agent,
        illustrator_agent,
        translator_agent,
        publisher_agent,
    ],
)

root_agent = ghost_commander
