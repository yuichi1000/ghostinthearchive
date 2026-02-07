"""Translator Pipeline - ADK Agent Definition

Defines root_agent (translator_commander) as a SequentialAgent that orchestrates
the translation of mystery articles from Japanese to English.
"""

from google.adk.agents import SequentialAgent

from .agents.translator import translator_agent

translator_commander = SequentialAgent(
    name="translator_commander",
    description=(
        "翻訳パイプライン。"
        "日本語のミステリー記事を英語に翻訳し、公開する。"
        "歴史用語の正確性と Fact × Folklore のニュアンスを維持する。"
    ),
    sub_agents=[translator_agent],
)

root_agent = translator_commander
