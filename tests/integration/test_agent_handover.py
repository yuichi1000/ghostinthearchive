"""Integration tests for agent-to-agent session state handover.

Tests verify that session state is correctly passed between agents
in the multilingual pipeline:
  ThemeAnalyzer → ParallelLibrarians → ParallelScholars → ParallelDebaters
    → CrossReferenceScholar → Storyteller → Illustrator → Translator → Publisher
"""


class TestSessionStateKeys:
    """Tests for session state key conventions."""

    def test_librarian_output_keys(self):
        """Language-specific Librarian agents should use 'collected_documents_{lang}' output keys."""
        from mystery_agents.agents.language_librarians import create_all_librarians

        librarians = create_all_librarians()
        for lang, agent in librarians.items():
            assert agent.output_key == f"collected_documents_{lang}"

    def test_scholar_output_keys(self):
        """Language-specific Scholar agents should use 'scholar_analysis_{lang}' output keys."""
        from mystery_agents.agents.language_scholars import create_all_scholars

        scholars = create_all_scholars()
        for lang, agent in scholars.items():
            assert agent.output_key == f"scholar_analysis_{lang}"

    def test_debater_output_keys(self):
        """Language-specific Debater agents should use 'scholar_debate_{lang}' output keys."""
        from mystery_agents.agents.language_scholars import create_all_debaters

        debaters = create_all_debaters()
        for lang, agent in debaters.items():
            assert agent.output_key == f"scholar_debate_{lang}"

    def test_cross_reference_scholar_output_key(self):
        """CrossReferenceScholar should use 'mystery_report' output key."""
        from mystery_agents.agents.cross_reference_scholar import (
            cross_reference_scholar_agent,
        )

        assert cross_reference_scholar_agent.output_key == "mystery_report"

    def test_storyteller_output_key(self):
        """Storyteller agent should use 'creative_content' output key."""
        from mystery_agents.agents.storyteller import storyteller_agent

        assert storyteller_agent.output_key == "creative_content"

    def test_illustrator_output_key(self):
        """Illustrator agent should use 'visual_assets' output key."""
        from mystery_agents.agents.illustrator import illustrator_agent

        assert illustrator_agent.output_key == "visual_assets"

    def test_publisher_output_key(self):
        """Publisher agent should use 'published_episode' output key."""
        from mystery_agents.agents.publisher import publisher_agent

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
        """Scholar instruction should reference {collected_documents_<lang>}."""
        from mystery_agents.agents.language_scholars import create_scholar

        scholar_en = create_scholar("en")
        assert "{collected_documents_en}" in scholar_en.instruction

    def test_cross_reference_references_analyses(self):
        """CrossReferenceScholar should reference all scholar_analysis keys."""
        from mystery_agents.agents.cross_reference_scholar import (
            cross_reference_scholar_agent,
        )

        instruction = cross_reference_scholar_agent.instruction
        assert "{scholar_analysis_en}" in instruction
        assert "{scholar_analysis_de}" in instruction
        assert "{scholar_analysis_es}" in instruction

    def test_cross_reference_references_debates(self):
        """CrossReferenceScholar should reference debate result keys."""
        from mystery_agents.agents.cross_reference_scholar import (
            cross_reference_scholar_agent,
        )

        instruction = cross_reference_scholar_agent.instruction
        assert "{scholar_debate_en}" in instruction
        assert "{scholar_debate_de}" in instruction

    def test_storyteller_references_mystery_report(self):
        """Storyteller instruction should reference {mystery_report}."""
        from mystery_agents.agents.storyteller import storyteller_agent

        assert "{mystery_report}" in storyteller_agent.instruction

    def test_illustrator_references_creative_content(self):
        """Illustrator instruction should reference {creative_content}."""
        from mystery_agents.agents.illustrator import illustrator_agent

        assert "{creative_content}" in illustrator_agent.instruction

    def test_publisher_references_required_keys(self):
        """Publisher instruction should reference all required session state keys."""
        from mystery_agents.agents.publisher import publisher_agent

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

    def test_librarians_use_flash(self):
        """Language Librarians should use gemini-2.5-flash model."""
        from mystery_agents.agents.language_librarians import create_all_librarians

        librarians = create_all_librarians()
        for lang, agent in librarians.items():
            assert agent.model == "gemini-2.5-flash", (
                f"librarian_{lang} should use gemini-2.5-flash"
            )

    def test_scholars_use_gemini_3_pro(self):
        """Language Scholars should use gemini-3-pro-preview model."""
        from mystery_agents.agents.language_scholars import create_all_scholars

        scholars = create_all_scholars()
        for lang, agent in scholars.items():
            assert agent.model == "gemini-3-pro-preview", (
                f"scholar_{lang} should use gemini-3-pro-preview"
            )

    def test_debaters_use_gemini_3_pro(self):
        """Debaters should use gemini-3-pro-preview model."""
        from mystery_agents.agents.language_scholars import create_all_debaters

        debaters = create_all_debaters()
        for lang, agent in debaters.items():
            assert agent.model == "gemini-3-pro-preview", (
                f"debater_{lang} should use gemini-3-pro-preview"
            )

    def test_core_agents_use_expected_models(self):
        """Core pipeline agents should use expected models."""
        from mystery_agents.agents.cross_reference_scholar import (
            cross_reference_scholar_agent,
        )
        from mystery_agents.agents.illustrator import illustrator_agent
        from mystery_agents.agents.publisher import publisher_agent
        from mystery_agents.agents.storyteller import storyteller_agent

        # LLM 重視のエージェントは Pro、軽量処理は Flash
        assert cross_reference_scholar_agent.model == "gemini-3-pro-preview"
        assert storyteller_agent.model == "gemini-3-pro-preview"
        assert illustrator_agent.model == "gemini-3-pro-preview"
        assert publisher_agent.model == "gemini-2.5-flash"

    def test_podcast_agents_use_gemini_3_pro(self):
        """Podcast agents should use gemini-3-pro-preview model."""
        from podcast_agents.agents.producer import producer_agent
        from podcast_agents.agents.scriptwriter import scriptwriter_agent

        expected_model = "gemini-3-pro-preview"

        assert scriptwriter_agent.model == expected_model
        assert producer_agent.model == expected_model


class TestRootAgentConfiguration:
    """Tests for root agent (commander) configuration."""

    def test_ghost_commander_is_sequential(self):
        """ghost_commander should be a SequentialAgent."""
        from google.adk.agents import SequentialAgent

        from mystery_agents.agent import root_agent

        assert isinstance(root_agent, SequentialAgent)

    def test_ghost_commander_is_root_agent(self):
        """ghost_commander should be exported as root_agent."""
        from mystery_agents.agent import ghost_commander, root_agent

        assert root_agent is ghost_commander

    def test_podcast_commander_is_sequential(self):
        """podcast_commander should be a SequentialAgent."""
        from google.adk.agents import SequentialAgent

        from podcast_agents.agent import root_agent

        assert isinstance(root_agent, SequentialAgent)

    def test_podcast_commander_is_root_agent(self):
        """podcast_commander should be exported as root_agent."""
        from podcast_agents.agent import podcast_commander, root_agent

        assert root_agent is podcast_commander


class TestLanguageGateCallbacks:
    """Tests for before_agent_callback on language agents."""

    def test_librarians_have_gate_callback(self):
        """All librarians should have a before_agent_callback."""
        from mystery_agents.agents.language_librarians import create_all_librarians

        librarians = create_all_librarians()
        for lang, agent in librarians.items():
            assert agent.before_agent_callback is not None, (
                f"librarian_{lang} should have before_agent_callback"
            )

    def test_scholars_have_gate_callback(self):
        """All scholars should have a before_agent_callback."""
        from mystery_agents.agents.language_scholars import create_all_scholars

        scholars = create_all_scholars()
        for lang, agent in scholars.items():
            assert agent.before_agent_callback is not None, (
                f"scholar_{lang} should have before_agent_callback"
            )

    def test_debaters_have_gate_callback(self):
        """All debaters should have a before_agent_callback."""
        from mystery_agents.agents.language_scholars import create_all_debaters

        debaters = create_all_debaters()
        for lang, agent in debaters.items():
            assert agent.before_agent_callback is not None, (
                f"debater_{lang} should have before_agent_callback"
            )
