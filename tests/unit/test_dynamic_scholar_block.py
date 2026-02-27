"""Unit tests for DynamicScholarBlock."""


from mystery_agents.agents.dynamic_scholar_block import (
    MAX_DEBATE_ITERATIONS,
    _is_meaningful,
    create_dynamic_scholar_block,
)


class TestDynamicScholarBlockCreation:
    """DynamicScholarBlock ファクトリのテスト。"""

    def test_creates_base_agent(self):
        """BaseAgent を継承していること。"""
        from google.adk.agents import BaseAgent

        dsb = create_dynamic_scholar_block()
        assert isinstance(dsb, BaseAgent)

    def test_agent_name(self):
        dsb = create_dynamic_scholar_block()
        assert "dynamic_scholar_block" in repr(dsb)

    def test_has_description(self):
        dsb = create_dynamic_scholar_block()
        assert dsb.description
        assert "dynamically" in dsb.description.lower()

    def test_description_mentions_2_layer(self):
        """description が2層構造に言及すること。"""
        dsb = create_dynamic_scholar_block()
        assert "named" in dsb.description.lower() or "multilingual" in dsb.description.lower()


class TestIsMeaningful:
    """_is_meaningful ヘルパー関数のテスト。"""

    def test_empty_string_not_meaningful(self):
        assert not _is_meaningful("")

    def test_none_not_meaningful(self):
        assert not _is_meaningful(None)

    def test_insufficient_data_not_meaningful(self):
        assert not _is_meaningful("INSUFFICIENT_DATA: No documents")

    def test_no_documents_found_not_meaningful(self):
        assert not _is_meaningful("NO_DOCUMENTS_FOUND: Nothing here")

    def test_no_content_not_meaningful(self):
        assert not _is_meaningful("NO_CONTENT: Nothing produced")

    def test_not_available_not_meaningful(self):
        assert not _is_meaningful("Not available")

    def test_normal_text_is_meaningful(self):
        assert _is_meaningful("Analysis of English sources reveals...")

    def test_marker_in_middle_is_meaningful(self):
        """失敗マーカーが中間にある場合は有意と判定。"""
        assert _is_meaningful("Analysis notes that INSUFFICIENT_DATA was found in...")


class TestConstants:
    """定数のテスト。"""

    def test_max_debate_iterations(self):
        assert MAX_DEBATE_ITERATIONS == 2


class TestTwoLayerRouting:
    """2層ルーティング（Named + Multilingual）のテスト。"""

    def test_named_scholar_languages_import(self):
        """NAMED_SCHOLAR_LANGUAGES がインポートできること。"""
        from mystery_agents.agents.language_scholars import NAMED_SCHOLAR_LANGUAGES

        assert "en" in NAMED_SCHOLAR_LANGUAGES
        assert "it" in NAMED_SCHOLAR_LANGUAGES
        assert "nl" not in NAMED_SCHOLAR_LANGUAGES

    def test_named_langs_filtered(self):
        """active_langs から Named と Other が正しく分離される。"""
        from mystery_agents.agents.language_scholars import NAMED_SCHOLAR_LANGUAGES

        active = ["en", "de", "nl", "pt", "pl"]
        named = [lang for lang in active if lang in NAMED_SCHOLAR_LANGUAGES]
        other = [lang for lang in active if lang not in NAMED_SCHOLAR_LANGUAGES]
        assert named == ["en", "de"]
        assert other == ["nl", "pt", "pl"]


class TestDynamicDebateInstruction:
    """動的討論 instruction のテスト。"""

    def test_dynamic_debate_only_includes_active_langs(self):
        """active_langs 指定時は参加言語のみ instruction に含まれること。"""
        from mystery_agents.agents.language_scholars import create_scholar

        scholar = create_scholar("en", mode="debate", active_langs=["en", "de", "ja"])
        assert "{scholar_analysis_de}" in scholar.instruction
        assert "{scholar_analysis_ja}" in scholar.instruction
        assert "{scholar_analysis_es}" not in scholar.instruction
        assert "{scholar_analysis_fr}" not in scholar.instruction

    def test_dynamic_debate_excludes_self(self):
        """自分自身の分析結果は instruction に含まれないこと。"""
        from mystery_agents.agents.language_scholars import create_scholar

        scholar = create_scholar("de", mode="debate", active_langs=["en", "de"])
        assert "{scholar_analysis_en}" in scholar.instruction
        assert "{scholar_analysis_de}" not in scholar.instruction

    def test_dynamic_debate_with_multilingual_reference(self):
        """active_langs に 'multilingual' が含まれる場合、参照される。"""
        from mystery_agents.agents.language_scholars import create_scholar

        scholar = create_scholar(
            "en", mode="debate", active_langs=["en", "de", "multilingual"]
        )
        assert "{scholar_analysis_de}" in scholar.instruction
        assert "{scholar_analysis_multilingual}" in scholar.instruction

    def test_dynamic_debate_has_whiteboard_reference(self):
        """動的討論の instruction が debate_whiteboard を参照すること。"""
        from mystery_agents.agents.language_scholars import create_scholar

        scholar = create_scholar("en", mode="debate", active_langs=["en", "de"])
        assert "{debate_whiteboard}" in scholar.instruction

    def test_dynamic_debate_has_whiteboard_tool(self):
        """動的討論の Scholar が append_to_whiteboard ツールを持つこと。"""
        from mystery_agents.agents.language_scholars import create_scholar
        from mystery_agents.tools.debate_tools import append_to_whiteboard

        scholar = create_scholar("en", mode="debate", active_langs=["en", "de"])
        assert append_to_whiteboard in scholar.tools

    def test_static_debate_uses_static_template(self):
        """active_langs 未指定時は静的テンプレート（全言語参照）が使用されること。"""
        from mystery_agents.agents.language_scholars import create_scholar

        scholar = create_scholar("en", mode="debate")
        assert "{scholar_analysis_fr}" in scholar.instruction
        assert "{scholar_analysis_nl}" in scholar.instruction
        assert "{scholar_analysis_pt}" in scholar.instruction


class TestIsDebateConverged:
    """is_debate_converged 関数のテスト。"""

    def test_empty_whiteboard_not_converged(self):
        from mystery_agents.tools.debate_tools import is_debate_converged

        assert not is_debate_converged("")

    def test_single_round_not_converged(self):
        from mystery_agents.tools.debate_tools import is_debate_converged

        whiteboard = "### [Round 1] English Perspective\n\nSome unique analysis.\n\n"
        assert not is_debate_converged(whiteboard)

    def test_identical_rounds_converged(self):
        """同じ内容のラウンドは収束と判定。"""
        from mystery_agents.tools.debate_tools import is_debate_converged

        whiteboard = (
            "### [Round 1] English Perspective\n\n"
            "The evidence shows anomalies in the historical records.\n\n"
            "### [Round 2] English Perspective\n\n"
            "The evidence shows anomalies in the historical records.\n\n"
        )
        assert is_debate_converged(whiteboard)

    def test_very_different_rounds_not_converged(self):
        """大きく異なるラウンドは収束しないと判定。"""
        from mystery_agents.tools.debate_tools import is_debate_converged

        whiteboard = (
            "### [Round 1] English Perspective\n\n"
            "The primary documents reveal significant discrepancies.\n\n"
            "### [Round 2] German Perspective\n\n"
            "Completely different analysis with entirely new vocabulary and arguments about "
            "folklore traditions cultural anthropology manuscript evidence.\n\n"
        )
        assert not is_debate_converged(whiteboard)
