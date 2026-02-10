"""Translator Pipeline - ADK Agent Definition

Defines root_agent (translator_commander) as a SequentialAgent that orchestrates
the translation of mystery content from English to Japanese.
"""

from google.adk.agents import SequentialAgent

from .agents.translator import translator_agent

translator_commander = SequentialAgent(
    name="translator_commander",
    description=(
        "Translation pipeline. "
        "Translates English mystery articles and theme suggestions into Japanese, "
        "maintaining historical terminology accuracy and Fact × Folklore nuance."
    ),
    sub_agents=[translator_agent],
)

root_agent = translator_commander
