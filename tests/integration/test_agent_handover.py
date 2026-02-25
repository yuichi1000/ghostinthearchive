"""Integration tests for agent-to-agent session state handover.

Tests verify that session state is correctly passed between agents
in the multilingual pipeline:
  ThemeAnalyzer → ParallelLibrarians → ParallelScholars → DebateLoop
    → ArmchairPolymath → Storyteller → Illustrator → Translator → Publisher
"""

from shared.state_registry import STATE_KEYS


def _registry_output_keys() -> set[str]:
    """STATE_KEYS から output_key（LLM エージェントの output_key）として
    使用されるキー名パターンを抽出する。{lang} テンプレートは除外。"""
    return {
        sk.name for sk in STATE_KEYS
        if "{lang}" not in sk.name
        and any("tools" not in w for w in sk.written_by)
    }


class TestSessionStateKeys:
    """Tests for session state key conventions."""

    def test_api_librarian_output_keys(self):
        """API-based Librarian agents should use 'collected_documents_{api_key}' output keys."""
        from mystery_agents.agents.api_librarians import API_CONFIGS, create_all_api_librarians

        librarians = create_all_api_librarians()
        expected_keys = [f"collected_documents_{key}" for key in API_CONFIGS]
        actual_keys = [agent.output_key for agent in librarians]
        assert sorted(actual_keys) == sorted(expected_keys)

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

    def test_publisher_is_custom_agent(self):
        """Publisher agent should be a Custom Agent (BaseAgent) named 'publisher'."""
        from mystery_agents.agents.publisher import publisher_agent

        # MagicMock 環境では .name がモックになるため repr で検証
        assert "publisher" in repr(publisher_agent)


    def test_output_keys_registered_in_state_registry(self):
        """主要 output_key が state_registry に登録されていること。"""
        registry_names = {sk.name for sk in STATE_KEYS}

        # テンプレート展開なしで存在を確認するキー
        expected = {"creative_content", "visual_assets", "mystery_report", "published_episode"}
        for key in expected:
            assert key in registry_names, (
                f"output_key '{key}' が state_registry に未登録"
            )

        # テンプレートパターンで存在を確認するキー
        template_keys = {"collected_documents_{lang}", "scholar_analysis_{lang}", "translation_result_{lang}"}
        for key in template_keys:
            assert key in registry_names, (
                f"output_key pattern '{key}' が state_registry に未登録"
            )


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

    def test_publisher_has_no_instruction(self):
        """Publisher Custom Agent は LLM を使わないため instruction を持たない。"""
        from mystery_agents.agents.publisher import publisher_agent

        assert not hasattr(publisher_agent, "instruction") or not isinstance(
            getattr(publisher_agent, "instruction", None), str
        )


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

    def test_api_librarian_count(self):
        """API-based Librarians should match the number of API configs."""
        from mystery_agents.agents.api_librarians import API_CONFIGS, create_all_api_librarians

        librarians = create_all_api_librarians()
        assert len(librarians) == len(API_CONFIGS)

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

    def test_name(self):
        """ArmchairPolymath should be named 'armchair_polymath'."""
        from mystery_agents.agents.armchair_polymath import armchair_polymath_agent

        # MagicMock は name を内部名として使うため、repr で検証
        assert "armchair_polymath" in repr(armchair_polymath_agent)


def _find_sub_agent(pipeline, name: str):
    """パイプライン内のサブエージェントを名前で再帰検索する。"""
    for agent in pipeline.sub_agents:
        if hasattr(agent, "name") and agent.name == name:
            return agent
        # MagicMock 環境では name が内部名として repr に含まれる
        if name in repr(agent):
            return agent
        # 再帰検索
        if hasattr(agent, "sub_agents"):
            found = _find_sub_agent(agent, name)
            if found is not None:
                return found
    return None


class TestDebateLoopConfiguration:
    """Tests for the debate loop LoopAgent configuration."""

    def test_debate_loop_is_created_via_loop_agent(self):
        """debate_loop should be created via LoopAgent constructor."""
        from mystery_agents.agent import ghost_commander

        debate_loop = _find_sub_agent(ghost_commander, "debate_loop")
        assert debate_loop is not None
        assert "debate_loop" in repr(debate_loop)

    def test_debate_loop_max_iterations(self):
        """debate_loop should have max_iterations=2."""
        from mystery_agents.agent import ghost_commander

        debate_loop = _find_sub_agent(ghost_commander, "debate_loop")
        assert debate_loop.max_iterations == 2

    def test_debate_loop_has_gate_callback(self):
        """debate_loop should have a before_agent_callback."""
        from mystery_agents.agent import ghost_commander

        debate_loop = _find_sub_agent(ghost_commander, "debate_loop")
        # before_agent_callback が設定されていること（callable であること）
        assert debate_loop.before_agent_callback is not None
        assert callable(debate_loop.before_agent_callback)

    def test_debate_loop_contains_debate_round(self):
        """debate_loop should contain debate_round as its sub_agent."""
        from mystery_agents.agent import ghost_commander

        debate_loop = _find_sub_agent(ghost_commander, "debate_loop")
        # LoopAgent の直接の sub_agent は debate_round（1つ）
        assert len(debate_loop.sub_agents) == 1
        assert "debate_round" in repr(debate_loop.sub_agents[0])


class TestPipelineGateCallbacks:
    """Tests for pipeline gate callbacks on block agents."""

    def test_scholar_block_has_gate(self):
        """scholar_block should have a before_agent_callback."""
        from mystery_agents.agent import ghost_commander

        scholar_block = _find_sub_agent(ghost_commander, "scholar_block")
        assert scholar_block.before_agent_callback is not None
        assert callable(scholar_block.before_agent_callback)

    def test_polymath_block_has_gate(self):
        """polymath_block should have a before_agent_callback."""
        from mystery_agents.agent import ghost_commander

        polymath_block = _find_sub_agent(ghost_commander, "polymath_block")
        assert polymath_block.before_agent_callback is not None
        assert callable(polymath_block.before_agent_callback)

    def test_storyteller_block_has_gate(self):
        """storyteller_block should have a before_agent_callback."""
        from mystery_agents.agent import ghost_commander

        storyteller_block = _find_sub_agent(ghost_commander, "storyteller_block")
        assert storyteller_block.before_agent_callback is not None
        assert callable(storyteller_block.before_agent_callback)

    def test_post_story_block_has_gate(self):
        """post_story_block should have a before_agent_callback."""
        from mystery_agents.agent import ghost_commander

        post_story_block = _find_sub_agent(ghost_commander, "post_story_block")
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

    def test_ghost_commander_contains_aggregator(self):
        """ghost_commander should contain the aggregator agent after parallel librarians."""
        from mystery_agents.agent import ghost_commander

        sub_agent_names = [repr(a) for a in ghost_commander.sub_agents]
        sub_agents_str = " ".join(sub_agent_names)
        assert "parallel_api_librarians" in sub_agents_str
        assert "aggregator" in sub_agents_str
