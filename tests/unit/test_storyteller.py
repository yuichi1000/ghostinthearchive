"""Unit tests for Storyteller agent instruction."""

from mystery_agents.agents.storyteller import STORYTELLER_INSTRUCTION


class TestStorytellerInstruction:
    def test_no_sources_in_output_template(self):
        """Storyteller should not include 'Sources: [引用元リスト]' in the output template."""
        assert "Sources: [引用元リスト]" not in STORYTELLER_INSTRUCTION

    def test_explicit_no_sources_directive(self):
        """Storyteller should have an explicit directive to not include Sources."""
        assert "Do NOT include a Sources (citation list) in the output" in STORYTELLER_INSTRUCTION

    def test_has_epistemic_honesty_guidelines(self):
        assert "Epistemic Honesty" in STORYTELLER_INSTRUCTION

    def test_not_found_not_equals_not_exist(self):
        assert "Does not exist" in STORYTELLER_INSTRUCTION

    def test_api_absence_not_historical_absence(self):
        assert "API absence" in STORYTELLER_INSTRUCTION

    def test_has_hook_technique(self):
        """Introduction にフック技法（provocative question）の指示がある。"""
        assert "provocative question" in STORYTELLER_INSTRUCTION.lower()
        assert "Do NOT open with a dry academic lead-in" in STORYTELLER_INSTRUCTION

    def test_has_sensory_writing_guidelines(self):
        """Sensory Writing セクションが存在し、blockquote 除外ルールを含む。"""
        assert "## Sensory Writing" in STORYTELLER_INSTRUCTION
        assert "regular paragraphs only" in STORYTELLER_INSTRUCTION

    def test_has_rhetoric_of_absence(self):
        """Rhetoric of Absence セクションが存在する。"""
        assert "## Rhetoric of Absence" in STORYTELLER_INSTRUCTION
        assert "gaps, silences, and omissions" in STORYTELLER_INSTRUCTION

    def test_has_abstract_concrete_alternation(self):
        """抽象⇄具体の交互配置指示が Creative Guidelines 内にある。"""
        assert "Abstract" in STORYTELLER_INSTRUCTION
        assert "Concrete Alternation" in STORYTELLER_INSTRUCTION
        assert "three consecutive paragraphs" in STORYTELLER_INSTRUCTION
