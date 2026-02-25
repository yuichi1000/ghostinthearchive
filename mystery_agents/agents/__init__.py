"""Ghost in the Archive - Agent Module

This module exports all specialized agents for the blog creation pipeline.
Scriptwriter and Producer have been moved to podcast_agents package.
"""

from .aggregator import create_aggregator
from .api_librarians import create_all_api_librarians, create_api_librarian
from .armchair_polymath import armchair_polymath_agent, create_armchair_polymath
from .convergence_checker import convergence_checker_agent, create_convergence_checker
from .dynamic_scholar_block import create_dynamic_scholar_block
from .illustrator import create_illustrator, illustrator_agent
from .language_scholars import create_all_scholars, create_scholar
from .publisher import create_publisher, publisher_agent
from .storyteller import create_storyteller, storyteller_agent
from .translator import create_all_translators, create_translator, translator_agent

__all__ = [
    "create_api_librarian",
    "create_all_api_librarians",
    "create_aggregator",
    "create_dynamic_scholar_block",
    "create_scholar",
    "create_all_scholars",
    "create_armchair_polymath",
    "armchair_polymath_agent",
    "create_storyteller",
    "storyteller_agent",
    "create_illustrator",
    "illustrator_agent",
    "create_publisher",
    "publisher_agent",
    "create_convergence_checker",
    "convergence_checker_agent",
    "create_translator",
    "create_all_translators",
    "translator_agent",
]
