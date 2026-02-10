"""Ghost in the Archive - ADK Agent Definition

Defines root_agent (ghost_commander) as a SequentialAgent that orchestrates
Librarian → Scholar → Storyteller → Illustrator → Translator → Publisher.
Translator is integrated into the blog pipeline to produce Japanese translations
before publishing. Scriptwriter and Producer are in the podcast_agents package.
"""

from google.adk.agents import SequentialAgent

from .agents.librarian import librarian_agent
from .agents.scholar import scholar_agent
from .agents.storyteller import storyteller_agent
from .agents.illustrator import illustrator_agent
from .agents.publisher import publisher_agent

from translator_agents.agents.translator import translator_agent

ghost_commander = SequentialAgent(
    name="ghost_commander",
    description=(
        "Ghost in the Archive blog creation pipeline. "
        "Executes Librarian → Scholar → Storyteller → Illustrator → Translator → Publisher "
        "in sequence to research, analyze, create content, generate images, translate to Japanese, "
        "and publish historical mysteries and folkloric anomalies."
    ),
    sub_agents=[
        librarian_agent,
        scholar_agent,
        storyteller_agent,
        illustrator_agent,
        translator_agent,
        publisher_agent,
    ],
)

root_agent = ghost_commander
