"""Podcast Pipeline - ADK Agent Definition

Defines root_agent (podcast_commander) as a SequentialAgent that orchestrates
Scriptwriter → Producer for on-demand podcast generation.
"""

from google.adk.agents import SequentialAgent

from .agents.scriptwriter import scriptwriter_agent
from .agents.producer import producer_agent

podcast_commander = SequentialAgent(
    name="podcast_commander",
    description=(
        "Podcast 作成パイプライン。"
        "Scriptwriter → Producer の順で実行し、"
        "ブログ記事からポッドキャスト脚本を作成し、音声を生成する。"
    ),
    sub_agents=[scriptwriter_agent, producer_agent],
)

root_agent = podcast_commander
