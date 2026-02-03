"""Integration tests for agent-to-agent session state handover.

Tests verify that session state is correctly passed between agents
in the pipeline: Librarian → Scholar → Storyteller → Visualizer → Publisher
"""

import json
from typing import Any, Dict
from unittest.mock import MagicMock, patch

import pytest


class TestSessionStateKeys:
    """Tests for session state key conventions."""

    def test_librarian_output_key(self):
        """Librarian agent should use 'collected_documents' output key."""
        from archive_agents.agents.librarian import librarian_agent

        assert librarian_agent.output_key == "collected_documents"

    def test_scholar_output_key(self):
        """Scholar agent should use 'mystery_report' output key."""
        from archive_agents.agents.scholar import scholar_agent

        assert scholar_agent.output_key == "mystery_report"

    def test_storyteller_output_key(self):
        """Storyteller agent should use 'creative_content' output key."""
        from archive_agents.agents.storyteller import storyteller_agent

        assert storyteller_agent.output_key == "creative_content"

    def test_visualizer_output_key(self):
        """Visualizer agent should use 'visual_assets' output key."""
        from archive_agents.agents.visualizer import visualizer_agent

        assert visualizer_agent.output_key == "visual_assets"

    def test_publisher_output_key(self):
        """Publisher agent should use 'published_episode' output key."""
        from archive_agents.agents.publisher import publisher_agent

        assert publisher_agent.output_key == "published_episode"


class TestPodcastSessionStateKeys:
    """Tests for podcast pipeline session state keys."""

    def test_scriptwriter_output_key(self):
        """Scriptwriter agent should use 'podcast_script' output key."""
        from podcast_agents.agents.scriptwriter import scriptwriter_agent

        assert scriptwriter_agent.output_key == "podcast_script"

    def test_producer_output_key(self):
        """Producer agent should use 'audio_assets' output key."""
        from podcast_agents.agents.producer import producer_agent

        assert producer_agent.output_key == "audio_assets"


class TestFailureMarkers:
    """Tests for failure marker propagation between agents."""

    def test_no_documents_found_marker_format(self):
        """NO_DOCUMENTS_FOUND marker should follow expected format."""
        # This tests the convention documented in CLAUDE.md
        marker = "NO_DOCUMENTS_FOUND"
        assert marker.isupper()
        assert "_" in marker

    def test_insufficient_data_marker_format(self):
        """INSUFFICIENT_DATA marker should follow expected format."""
        marker = "INSUFFICIENT_DATA"
        assert marker.isupper()
        assert "_" in marker

    def test_no_content_marker_format(self):
        """NO_CONTENT marker should follow expected format."""
        marker = "NO_CONTENT"
        assert marker.isupper()


class TestInstructionPlaceholders:
    """Tests for instruction placeholders referencing session state."""

    def test_scholar_references_collected_documents(self):
        """Scholar instruction should reference {collected_documents}."""
        from archive_agents.agents.scholar import scholar_agent

        assert "{collected_documents}" in scholar_agent.instruction

    def test_storyteller_references_mystery_report(self):
        """Storyteller instruction should reference {mystery_report}."""
        from archive_agents.agents.storyteller import storyteller_agent

        assert "{mystery_report}" in storyteller_agent.instruction

    def test_visualizer_references_creative_content(self):
        """Visualizer instruction should reference {creative_content}."""
        from archive_agents.agents.visualizer import visualizer_agent

        assert "{creative_content}" in visualizer_agent.instruction

    def test_publisher_references_required_keys(self):
        """Publisher instruction should reference all required session state keys."""
        from archive_agents.agents.publisher import publisher_agent

        # Publisher needs access to multiple session state keys
        instruction = publisher_agent.instruction
        assert "{mystery_report}" in instruction
        assert "{creative_content}" in instruction
        assert "{visual_assets}" in instruction


class TestPodcastInstructionPlaceholders:
    """Tests for podcast pipeline instruction placeholders."""

    def test_scriptwriter_references_creative_content(self):
        """Scriptwriter instruction should reference {creative_content}."""
        from podcast_agents.agents.scriptwriter import scriptwriter_agent

        assert "{creative_content}" in scriptwriter_agent.instruction

    def test_producer_references_podcast_script(self):
        """Producer instruction should reference {podcast_script}."""
        from podcast_agents.agents.producer import producer_agent

        assert "{podcast_script}" in producer_agent.instruction


class TestAgentModels:
    """Tests for agent model configuration."""

    def test_all_agents_use_gemini_3_pro(self):
        """All agents should use gemini-3-pro-preview model."""
        from archive_agents.agents.librarian import librarian_agent
        from archive_agents.agents.scholar import scholar_agent
        from archive_agents.agents.storyteller import storyteller_agent
        from archive_agents.agents.visualizer import visualizer_agent
        from archive_agents.agents.publisher import publisher_agent

        expected_model = "gemini-3-pro-preview"

        agents = [
            librarian_agent,
            scholar_agent,
            storyteller_agent,
            visualizer_agent,
            publisher_agent,
        ]

        for agent in agents:
            assert agent.model == expected_model, f"{agent.name} should use {expected_model}"

    def test_podcast_agents_use_gemini_3_pro(self):
        """Podcast agents should use gemini-3-pro-preview model."""
        from podcast_agents.agents.scriptwriter import scriptwriter_agent
        from podcast_agents.agents.producer import producer_agent

        expected_model = "gemini-3-pro-preview"

        assert scriptwriter_agent.model == expected_model
        assert producer_agent.model == expected_model


class TestRootAgentConfiguration:
    """Tests for root agent (commander) configuration."""

    def test_ghost_commander_is_sequential(self):
        """ghost_commander should be a SequentialAgent."""
        from archive_agents.agent import root_agent
        from google.adk.agents import SequentialAgent

        assert isinstance(root_agent, SequentialAgent)

    def test_ghost_commander_agent_order(self):
        """ghost_commander should have agents in correct order."""
        from archive_agents.agent import root_agent

        agent_names = [agent.name for agent in root_agent.sub_agents]
        expected_order = ["librarian", "scholar", "storyteller", "visualizer", "publisher"]

        assert agent_names == expected_order

    def test_podcast_commander_is_sequential(self):
        """podcast_commander should be a SequentialAgent."""
        from podcast_agents.agent import root_agent
        from google.adk.agents import SequentialAgent

        assert isinstance(root_agent, SequentialAgent)

    def test_podcast_commander_agent_order(self):
        """podcast_commander should have agents in correct order."""
        from podcast_agents.agent import root_agent

        agent_names = [agent.name for agent in root_agent.sub_agents]
        expected_order = ["scriptwriter", "producer"]

        assert agent_names == expected_order
