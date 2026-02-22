"""Unit tests for Armchair Polymath agent instruction."""

from mystery_agents.agents.armchair_polymath import ARMCHAIR_POLYMATH_INSTRUCTION


class TestArmchairPolymathInstruction:
    def test_has_source_coverage_assessment(self):
        assert "Source Coverage Assessment" in ARMCHAIR_POLYMATH_INSTRUCTION

    def test_has_confidence_level_checklist(self):
        assert "Confidence Level Checklist" in ARMCHAIR_POLYMATH_INSTRUCTION

    def test_has_confirmed_ghost_criteria(self):
        assert "Confirmed Ghost" in ARMCHAIR_POLYMATH_INSTRUCTION

    def test_has_suspected_ghost_criteria(self):
        assert "Suspected Ghost" in ARMCHAIR_POLYMATH_INSTRUCTION

    def test_has_archival_echo_criteria(self):
        assert "Archival Echo" in ARMCHAIR_POLYMATH_INSTRUCTION

    def test_absence_not_nonexistence(self):
        assert "non-existence" in ARMCHAIR_POLYMATH_INSTRUCTION

    def test_has_academic_coverage_section(self):
        assert "Academic Coverage and Blind Spots" in ARMCHAIR_POLYMATH_INSTRUCTION

    def test_source_coverage_before_confidence(self):
        """Source Coverage Assessment は Confidence Level Checklist より前に記述されていること。"""
        sca_pos = ARMCHAIR_POLYMATH_INSTRUCTION.index("Source Coverage Assessment")
        clc_pos = ARMCHAIR_POLYMATH_INSTRUCTION.index("Confidence Level Checklist")
        assert sca_pos < clc_pos
