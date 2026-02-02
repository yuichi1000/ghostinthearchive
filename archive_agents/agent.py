"""Ghost in the Archive - ADK Agent Definition

Defines root_agent (ghost_commander) as a SequentialAgent that orchestrates
Librarian → Scholar → Storyteller → Visualizer → Publisher.
Scriptwriter と Producer は podcast_agents パッケージに分離。
"""

from google.adk.agents import SequentialAgent

from .agents.librarian import librarian_agent
from .agents.scholar import scholar_agent
from .agents.storyteller import storyteller_agent
from .agents.visualizer import visualizer_agent
from .agents.publisher import publisher_agent

ghost_commander = SequentialAgent(
    name="ghost_commander",
    description=(
        "Ghost in the Archive ブログ作成パイプライン。"
        "Librarian → Scholar → Storyteller → Visualizer → Publisher の順で実行し、"
        "歴史的ミステリーと民俗学的怪異を調査・分析・コンテンツ化・画像生成・公開する。"
    ),
    sub_agents=[librarian_agent, scholar_agent, storyteller_agent, visualizer_agent, publisher_agent],
)

root_agent = ghost_commander
