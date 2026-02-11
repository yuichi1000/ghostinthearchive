"""Ghost in the Archive - ADK Agent Definition

Defines root_agent (ghost_commander) as a SequentialAgent that orchestrates
the multilingual investigation pipeline:

  ThemeAnalyzer → ParallelLibrarians → ParallelScholars → ParallelDebaters
    → CrossReferenceScholar → Storyteller → Illustrator → Translator → Publisher

各言語エージェントは before_agent_callback で selected_languages をチェックし、
未選択の言語はスキップされる。Debater は2言語以上選択時のみ実行される。
"""

from google.adk.agents import ParallelAgent, SequentialAgent

from .agents.cross_reference_scholar import cross_reference_scholar_agent
from .agents.illustrator import illustrator_agent
from .agents.language_librarians import create_all_librarians
from .agents.language_scholars import create_all_debaters, create_all_scholars
from .agents.publisher import publisher_agent
from .agents.storyteller import storyteller_agent
from .agents.theme_analyzer import theme_analyzer_agent

from translator_agents.agents.translator import translator_agent

# 言語別エージェントを生成
all_librarians = create_all_librarians()
all_scholars = create_all_scholars()
all_debaters = create_all_debaters()

# メインパイプライン（フラット構造: before_agent_callback でゲート）
ghost_commander = SequentialAgent(
    name="ghost_commander",
    description=(
        "Ghost in the Archive multilingual blog creation pipeline. "
        "Executes ThemeAnalyzer → ParallelLibrarians → ParallelScholars → ParallelDebaters "
        "→ CrossReferenceScholar → Storyteller → Illustrator → Translator → Publisher "
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
        ParallelAgent(
            name="parallel_debaters",
            sub_agents=list(all_debaters.values()),
        ),
        cross_reference_scholar_agent,
        storyteller_agent,
        illustrator_agent,
        translator_agent,
        publisher_agent,
    ],
)

root_agent = ghost_commander
