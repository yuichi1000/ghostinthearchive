"""Ghost in the Archive - ADK Agent Definition

Defines root_agent (ghost_commander) as a SequentialAgent that orchestrates
Librarian → Historian → Storyteller → Scriptwriter → Visualizer → Producer → Publisher.
"""

from google.adk.agents import SequentialAgent

from .agents.librarian import librarian_agent
from .agents.historian import historian_agent
from .agents.storyteller import storyteller_agent
from .agents.scriptwriter import scriptwriter_agent
from .agents.visualizer import visualizer_agent
from .agents.producer import producer_agent
from .agents.publisher import publisher_agent

ghost_commander = SequentialAgent(
    name="ghost_commander",
    description=(
        "Ghost in the Archive パイプライン。"
        "Librarian → Historian → Storyteller → Scriptwriter → Visualizer → Producer → Publisher の順で実行し、"
        "歴史的ミステリーと民俗学的怪異を調査・分析・コンテンツ化・脚本化・画像生成・音声生成・公開する。"
    ),
    sub_agents=[librarian_agent, historian_agent, storyteller_agent, scriptwriter_agent, visualizer_agent, producer_agent, publisher_agent],
)

root_agent = ghost_commander
