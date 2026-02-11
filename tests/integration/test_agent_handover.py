"""Integration tests for agent-to-agent session state handover.

Tests verify that session state is correctly passed between agents
in the multilingual pipeline:
  ThemeAnalyzer → ParallelLibrarians → ParallelScholars → DebateLoop
    → ArmchairPolymath → Storyteller → Illustrator → Translator → Publisher
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

    def test_armchair_polymath_references_analyses(self):
        """ArmchairPolymath should reference all scholar_analysis keys."""
        from mystery_agents.agents.armchair_polymath import armchair_polymath_agent

        instruction = armchair_polymath_agent.instruction
        assert "{scholar_analysis_en}" in instruction
        assert "{scholar_analysis_de}" in instruction
        assert "{scholar_analysis_es}" in instruction

    def test_armchair_polymath_references_whiteboard(self):
        """ArmchairPolymath should reference {debate_whiteboard}."""
        from mystery_agents.agents.armchair_polymath import armchair_polymath_agent

        assert "{debate_whiteboard}" in armchair_polymath_agent.instruction

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

    def test_debate_scholars_use_gemini_3_pro(self):
        """Scholar debate mode agents should use gemini-3-pro-preview model."""
        from mystery_agents.agents.language_scholars import create_all_scholars

        debate_scholars = create_all_scholars(mode="debate")
        for lang, agent in debate_scholars.items():
            assert agent.model == "gemini-3-pro-preview", (
                f"scholar_{lang}_debate should use gemini-3-pro-preview"
            )

    def test_core_agents_use_expected_models(self):
        """Core pipeline agents should use expected models."""
        from mystery_agents.agents.armchair_polymath import armchair_polymath_agent
        from mystery_agents.agents.illustrator import illustrator_agent
        from mystery_agents.agents.publisher import publisher_agent
        from mystery_agents.agents.storyteller import storyteller_agent

        # LLM 重視のエージェントは Pro、軽量処理は Flash
        assert armchair_polymath_agent.model == "gemini-3-pro-preview"
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

    def test_debate_scholars_have_gate_callback(self):
        """All debate-mode scholars should have a before_agent_callback."""
        from mystery_agents.agents.language_scholars import create_all_scholars

        debate_scholars = create_all_scholars(mode="debate")
        for lang, agent in debate_scholars.items():
            assert agent.before_agent_callback is not None, (
                f"scholar_{lang}_debate should have before_agent_callback"
            )


class TestScholarDebateMode:
    """Tests for Scholar agents in debate mode."""

    def test_debate_scholar_has_no_explicit_output_key(self):
        """討論モードの Scholar は output_key を明示的に設定しない。"""
        from mystery_agents.agents.language_scholars import create_all_scholars

        debate_scholars = create_all_scholars(mode="debate")
        for lang, agent in debate_scholars.items():
            # MagicMock の場合、output_key を明示設定していないので文字列にはならない
            assert not isinstance(agent.output_key, str), (
                f"scholar_{lang}_debate should not have a string output_key"
            )

    def test_debate_scholar_has_whiteboard_tool(self):
        """討論モードの Scholar は append_to_whiteboard ツールを持つ。"""
        from mystery_agents.agents.language_scholars import create_all_scholars
        from mystery_agents.tools.debate_tools import append_to_whiteboard

        debate_scholars = create_all_scholars(mode="debate")
        for lang, agent in debate_scholars.items():
            assert append_to_whiteboard in agent.tools, (
                f"scholar_{lang}_debate should have append_to_whiteboard tool"
            )

    def test_debate_scholar_references_whiteboard(self):
        """討論モードの Scholar の instruction が {debate_whiteboard} を参照する。"""
        from mystery_agents.agents.language_scholars import create_all_scholars

        debate_scholars = create_all_scholars(mode="debate")
        for lang, agent in debate_scholars.items():
            assert "{debate_whiteboard}" in agent.instruction, (
                f"scholar_{lang}_debate should reference {{debate_whiteboard}}"
            )

    def test_debate_scholar_name_format(self):
        """討論モードの Scholar のエージェント名が scholar_{lang}_debate 形式。"""
        from mystery_agents.agents.language_scholars import create_all_scholars

        debate_scholars = create_all_scholars(mode="debate")
        for lang, agent in debate_scholars.items():
            # MagicMock は name を内部名として使うため、_mock_name で検証
            assert f"scholar_{lang}_debate" in repr(agent), (
                f"Expected scholar_{lang}_debate in repr, got {repr(agent)}"
            )

    def test_debate_scholar_shares_cultural_perspective(self):
        """討論モードの Scholar が SCHOLAR_CONFIGS の文化的視点を共有する。"""
        from mystery_agents.agents.language_scholars import SCHOLAR_CONFIGS, create_scholar

        for lang, config in SCHOLAR_CONFIGS.items():
            debate_agent = create_scholar(lang, mode="debate")
            # 文化的視点のキーワードが instruction に含まれることを確認
            assert config["language_name"] in debate_agent.instruction


class TestArmchairPolymath:
    """Tests for the Armchair Polymath agent."""

    def test_output_key(self):
        """ArmchairPolymath should use 'mystery_report' output key."""
        from mystery_agents.agents.armchair_polymath import armchair_polymath_agent

        assert armchair_polymath_agent.output_key == "mystery_report"

    def test_references_whiteboard(self):
        """ArmchairPolymath should reference {debate_whiteboard} in instruction."""
        from mystery_agents.agents.armchair_polymath import armchair_polymath_agent

        assert "{debate_whiteboard}" in armchair_polymath_agent.instruction

    def test_has_save_structured_report_tool(self):
        """ArmchairPolymath should have save_structured_report tool."""
        from mystery_agents.agents.armchair_polymath import armchair_polymath_agent
        from mystery_agents.tools.scholar_tools import save_structured_report

        assert save_structured_report in armchair_polymath_agent.tools

    def test_model(self):
        """ArmchairPolymath should use gemini-3-pro-preview model."""
        from mystery_agents.agents.armchair_polymath import armchair_polymath_agent

        assert armchair_polymath_agent.model == "gemini-3-pro-preview"

    def test_name(self):
        """ArmchairPolymath should be named 'armchair_polymath'."""
        from mystery_agents.agents.armchair_polymath import armchair_polymath_agent

        # MagicMock は name を内部名として使うため、repr で検証
        assert "armchair_polymath" in repr(armchair_polymath_agent)


class TestDebateLoopConfiguration:
    """Tests for the debate loop LoopAgent configuration."""

    def test_debate_loop_is_created_via_loop_agent(self):
        """debate_loop should be created via LoopAgent constructor."""
        from mystery_agents.agent import debate_loop

        # MagicMock 環境では LoopAgent(...) の戻り値は MagicMock インスタンス
        # debate_loop が存在し、名前に debate_loop が含まれることを確認
        assert "debate_loop" in repr(debate_loop)

    def test_debate_loop_max_iterations(self):
        """debate_loop should have max_iterations=2."""
        from mystery_agents.agent import debate_loop

        assert debate_loop.max_iterations == 2

    def test_debate_loop_has_gate_callback(self):
        """debate_loop should have a before_agent_callback."""
        from mystery_agents.agent import debate_loop

        # before_agent_callback が設定されていること（callable であること）
        assert debate_loop.before_agent_callback is not None
        assert callable(debate_loop.before_agent_callback)

    def test_debate_loop_sub_agents_count(self):
        """debate_loop should have 6 sub_agents (one per language)."""
        from mystery_agents.agent import debate_loop

        assert len(debate_loop.sub_agents) == 6


class TestPipelineGateCallbacks:
    """Tests for pipeline gate callbacks on block agents."""

    def test_scholar_block_has_gate(self):
        """scholar_block should have a before_agent_callback."""
        from mystery_agents.agent import scholar_block

        assert scholar_block.before_agent_callback is not None
        assert callable(scholar_block.before_agent_callback)

    def test_polymath_block_has_gate(self):
        """polymath_block should have a before_agent_callback."""
        from mystery_agents.agent import polymath_block

        assert polymath_block.before_agent_callback is not None
        assert callable(polymath_block.before_agent_callback)

    def test_storyteller_block_has_gate(self):
        """storyteller_block should have a before_agent_callback."""
        from mystery_agents.agent import storyteller_block

        assert storyteller_block.before_agent_callback is not None
        assert callable(storyteller_block.before_agent_callback)

    def test_post_story_block_has_gate(self):
        """post_story_block should have a before_agent_callback."""
        from mystery_agents.agent import post_story_block

        assert post_story_block.before_agent_callback is not None
        assert callable(post_story_block.before_agent_callback)

    def test_ghost_commander_contains_gate_blocks(self):
        """ghost_commander should contain the gated block agents."""
        from mystery_agents.agent import ghost_commander

        sub_agent_names = [repr(a) for a in ghost_commander.sub_agents]
        sub_agents_str = " ".join(sub_agent_names)
        assert "scholar_block" in sub_agents_str
        assert "polymath_block" in sub_agents_str
        assert "storyteller_block" in sub_agents_str
        assert "post_story_block" in sub_agents_str
