"""Ghost in the Archive - ADK Agent Definition

Defines root_agent (ghost_commander) as a SequentialAgent that orchestrates
the multilingual investigation pipeline:

  MultilingualOrchestrator (ThemeAnalyzer → Librarians → Scholars → CrossRef)
    → Storyteller → Illustrator → Translator → Publisher

The MultilingualOrchestrator dynamically selects language-specific Librarian
and Scholar agents based on the investigation theme.
"""

from google.adk.agents import SequentialAgent

from .agents.cross_reference_scholar import cross_reference_scholar_agent
from .agents.illustrator import illustrator_agent
from .agents.language_librarians import create_all_librarians
from .agents.language_scholars import create_all_scholars
from .agents.multilingual_orchestrator import MultilingualOrchestrator
from .agents.publisher import publisher_agent
from .agents.storyteller import storyteller_agent
from .agents.theme_analyzer import theme_analyzer_agent

from translator_agents.agents.translator import translator_agent

# 言語別エージェントを生成
all_librarians = create_all_librarians()  # {"en": ..., "de": ..., "es": ..., ...}
all_scholars = create_all_scholars()      # {"en": ..., "de": ..., "es": ..., ...}

# 多言語オーケストレーター
multilingual_orchestrator = MultilingualOrchestrator(
    name="multilingual_orchestrator",
    description=(
        "Dynamically orchestrates multilingual investigation. "
        "Analyzes theme → selects languages → runs language-specific "
        "Librarians and Scholars in parallel → integrates via CrossReferenceScholar."
    ),
    theme_analyzer=theme_analyzer_agent,
    all_librarians=all_librarians,
    all_scholars=all_scholars,
    cross_reference_scholar=cross_reference_scholar_agent,
)

# メインパイプライン
ghost_commander = SequentialAgent(
    name="ghost_commander",
    description=(
        "Ghost in the Archive multilingual blog creation pipeline. "
        "Executes MultilingualOrchestrator (ThemeAnalyzer → Librarians → Scholars → CrossRef) "
        "→ Storyteller → Illustrator → Translator → Publisher "
        "to research, analyze, create content, generate images, translate to Japanese, "
        "and publish historical mysteries and folkloric anomalies."
    ),
    sub_agents=[
        multilingual_orchestrator,   # ThemeAnalyzer → Librarians → Scholars → CrossRef
        storyteller_agent,           # 英語マスターレポート → 英語ブログ記事
        illustrator_agent,           # トップ画像生成
        translator_agent,            # EN→JA 翻訳
        publisher_agent,             # Firestore 保存
    ],
)

root_agent = ghost_commander
