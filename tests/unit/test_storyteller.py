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
