"""Ghost in the Archive - Agent Module

This module exports all specialized agents for the blog creation pipeline.
Scriptwriter and Producer have been moved to podcast_agents package.
"""

from .armchair_polymath import armchair_polymath_agent
from .illustrator import illustrator_agent
from .language_librarians import create_all_librarians, create_librarian
from .language_scholars import create_all_scholars, create_scholar
from .publisher import publisher_agent
from .storyteller import storyteller_agent

__all__ = [
    "create_librarian",
    "create_all_librarians",
    "create_scholar",
    "create_all_scholars",
    "armchair_polymath_agent",
    "storyteller_agent",
    "illustrator_agent",
    "publisher_agent",
]
