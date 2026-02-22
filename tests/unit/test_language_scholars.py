"""Unit tests for Language Scholars agent instruction."""

from mystery_agents.agents.language_scholars import (
    _BASE_SCHOLAR_INSTRUCTION,
    create_scholar,
)


class TestScholarInstruction:
    def test_has_source_coverage_framework(self):
        assert "Source Coverage Assessment" in _BASE_SCHOLAR_INSTRUCTION

    def test_has_digitization_scope(self):
        assert "Digitization scope" in _BASE_SCHOLAR_INSTRUCTION

    def test_has_ocr_quality(self):
        assert "OCR" in _BASE_SCHOLAR_INSTRUCTION

    def test_has_selection_bias(self):
        assert "Selection bias" in _BASE_SCHOLAR_INSTRUCTION

    def test_has_absence_caveat(self):
        assert "Absence caveat" in _BASE_SCHOLAR_INSTRUCTION

    def test_five_analysis_frameworks(self):
        """分析フレームワークが5つあること。"""
        count = _BASE_SCHOLAR_INSTRUCTION.count("### ")
        # 5つのフレームワーク + Output Format 等
        assert count >= 5


class TestCreateScholar:
    def test_analysis_mode_has_source_coverage(self):
        scholar = create_scholar("en", mode="analysis")
        assert "Source Coverage Assessment" in scholar.instruction
