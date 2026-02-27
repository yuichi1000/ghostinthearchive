"""Unit tests for DynamicPolymathBlock."""

from mystery_agents.agents.dynamic_polymath_block import (
    _build_analyses_section,
    create_dynamic_polymath_block,
)


class TestDynamicPolymathBlockCreation:
    """DynamicPolymathBlock ファクトリのテスト。"""

    def test_creates_base_agent(self):
        """BaseAgent を継承していること。"""
        from google.adk.agents import BaseAgent

        dpb = create_dynamic_polymath_block()
        assert isinstance(dpb, BaseAgent)

    def test_agent_name(self):
        dpb = create_dynamic_polymath_block()
        assert "dynamic_polymath_block" in repr(dpb)

    def test_has_description(self):
        dpb = create_dynamic_polymath_block()
        assert dpb.description
        assert "dynamically" in dpb.description.lower()


class TestBuildAnalysesSection:
    """_build_analyses_section のテスト。"""

    def test_contains_only_active_langs(self):
        """2言語アクティブ時にその2言語のプレースホルダーのみ含まれること。"""
        section = _build_analyses_section(["en", "ja"])
        assert "{scholar_analysis_en}" in section
        assert "{scholar_analysis_ja}" in section
        assert "{scholar_analysis_de}" not in section
        assert "{scholar_analysis_es}" not in section

    def test_single_language(self):
        """1言語のみの場合でも正しくセクションを構築すること。"""
        section = _build_analyses_section(["de"])
        assert "{scholar_analysis_de}" in section
        assert "1 source(s)" in section
        assert "{scholar_analysis_en}" not in section

    def test_includes_language_names(self):
        """言語名がセクションに含まれること。"""
        section = _build_analyses_section(["en", "de"])
        assert "English" in section
        assert "German" in section

    def test_with_multilingual(self):
        """has_multilingual=True で multilingual プレースホルダーが含まれること。"""
        section = _build_analyses_section(["en", "de"], has_multilingual=True)
        assert "{scholar_analysis_en}" in section
        assert "{scholar_analysis_de}" in section
        assert "{scholar_analysis_multilingual}" in section
        assert "Multilingual" in section
        assert "3 source(s)" in section

    def test_without_multilingual(self):
        """has_multilingual=False で multilingual プレースホルダーが含まれないこと。"""
        section = _build_analyses_section(["en", "de"], has_multilingual=False)
        assert "{scholar_analysis_multilingual}" not in section
        assert "2 source(s)" in section

    def test_all_named_languages(self):
        """Named Scholar 全6言語を指定した場合のテスト。"""
        all_langs = ["en", "de", "es", "fr", "ja", "it"]
        section = _build_analyses_section(all_langs)
        for lang in all_langs:
            assert f"{{scholar_analysis_{lang}}}" in section
        assert "6 source(s)" in section


class TestInstructionComposition:
    """動的 instruction 構築の結合テスト。"""

    def test_composed_instruction_contains_debate_whiteboard(self):
        """組み立てた instruction が {debate_whiteboard} を常に含むこと。"""
        from mystery_agents.agents.armchair_polymath import (
            INSTRUCTION_BODY,
            INSTRUCTION_PREAMBLE,
        )

        section = _build_analyses_section(["en"])
        instruction = INSTRUCTION_PREAMBLE + "\n" + section + "\n" + INSTRUCTION_BODY
        assert "{debate_whiteboard}" in instruction

    def test_composed_instruction_contains_preamble(self):
        """組み立てた instruction がペルソナ紹介を含むこと。"""
        from mystery_agents.agents.armchair_polymath import (
            INSTRUCTION_BODY,
            INSTRUCTION_PREAMBLE,
        )

        section = _build_analyses_section(["en"])
        instruction = INSTRUCTION_PREAMBLE + "\n" + section + "\n" + INSTRUCTION_BODY
        assert "Armchair Polymath" in instruction
        assert "sardonic" in instruction
