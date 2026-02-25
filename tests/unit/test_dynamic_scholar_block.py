"""Unit tests for DynamicScholarBlock."""

import pytest

from mystery_agents.agents.dynamic_scholar_block import (
    MAX_DEBATE_ITERATIONS,
    MAX_LANGUAGES,
    DynamicScholarBlock,
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

    def test_max_languages(self):
        assert MAX_LANGUAGES == 7

    def test_max_debate_iterations(self):
        assert MAX_DEBATE_ITERATIONS == 2


class TestDynamicDebateInstruction:
    """動的討論 instruction のテスト。"""

    def test_dynamic_debate_only_includes_active_langs(self):
        """active_langs 指定時は参加言語のみ instruction に含まれること。"""
        from mystery_agents.agents.language_scholars import create_scholar

        scholar = create_scholar("en", mode="debate", active_langs=["en", "de", "ja"])
        # 自分以外の2言語が参照されていること
        assert "{scholar_analysis_de}" in scholar.instruction
        assert "{scholar_analysis_ja}" in scholar.instruction
        # 不参加言語は参照されていないこと
        assert "{scholar_analysis_es}" not in scholar.instruction
        assert "{scholar_analysis_fr}" not in scholar.instruction
        assert "{scholar_analysis_nl}" not in scholar.instruction
        assert "{scholar_analysis_pt}" not in scholar.instruction

    def test_dynamic_debate_excludes_self(self):
        """自分自身の分析結果は instruction に含まれないこと。"""
        from mystery_agents.agents.language_scholars import create_scholar

        scholar = create_scholar("de", mode="debate", active_langs=["en", "de"])
        assert "{scholar_analysis_en}" in scholar.instruction
        assert "{scholar_analysis_de}" not in scholar.instruction

    def test_dynamic_debate_uses_dynamic_template(self):
        """active_langs 指定時は動的テンプレートが使用されること。"""
        from mystery_agents.agents.language_scholars import create_scholar

        scholar = create_scholar("en", mode="debate", active_langs=["en", "de"])
        # 動的テンプレートは全7言語のハードコード参照を含まない
        # 静的テンプレートにのみ存在する French/Dutch/Portuguese の参照がないことを確認
        assert "{scholar_analysis_fr}" not in scholar.instruction
        assert "{scholar_analysis_nl}" not in scholar.instruction
        assert "{scholar_analysis_pt}" not in scholar.instruction

    def test_static_debate_uses_static_template(self):
        """active_langs 未指定時は静的テンプレート（全7言語参照）が使用されること。"""
        from mystery_agents.agents.language_scholars import create_scholar

        scholar = create_scholar("en", mode="debate")
        # 静的テンプレートは全7言語の参照をハードコードで含む
        assert "{scholar_analysis_fr}" in scholar.instruction
        assert "{scholar_analysis_nl}" in scholar.instruction
        assert "{scholar_analysis_pt}" in scholar.instruction

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
