"""Unit tests for Storyteller agent instruction."""

from archive_agents.agents.storyteller import STORYTELLER_INSTRUCTION


class TestStorytellerInstruction:
    def test_no_sources_in_output_template(self):
        """Storyteller should not include 'Sources: [引用元リスト]' in the output template."""
        assert "Sources: [引用元リスト]" not in STORYTELLER_INSTRUCTION

    def test_explicit_no_sources_directive(self):
        """Storyteller should have an explicit directive to not include Sources."""
        assert "Sources（引用元リスト）は出力に含めないでください" in STORYTELLER_INSTRUCTION
