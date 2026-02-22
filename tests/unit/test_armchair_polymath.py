"""Unit tests for Armchair Polymath agent instruction and configuration."""

from mystery_agents.agents.armchair_polymath import (
    ARMCHAIR_POLYMATH_INSTRUCTION,
    armchair_polymath_agent,
)
from mystery_agents.tools.search_metadata import get_search_metadata


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

    def test_instruction_includes_source_coverage_in_json(self):
        """instruction の JSON 例に source_coverage フィールドが含まれる。"""
        assert '"source_coverage"' in ARMCHAIR_POLYMATH_INSTRUCTION

    def test_instruction_includes_confidence_rationale_in_json(self):
        """instruction の JSON 例に confidence_rationale フィールドが含まれる。"""
        assert '"confidence_rationale"' in ARMCHAIR_POLYMATH_INSTRUCTION

    def test_instruction_includes_get_search_metadata(self):
        """instruction に get_search_metadata ツールの説明が含まれる。"""
        assert "get_search_metadata" in ARMCHAIR_POLYMATH_INSTRUCTION


class TestArmchairPolymathTools:
    def test_tools_include_get_search_metadata(self):
        """armchair_polymath_agent の tools に get_search_metadata が含まれる。"""
        tool_functions = [t for t in armchair_polymath_agent.tools if callable(t)]
        tool_names = [t.__name__ for t in tool_functions]
        assert "get_search_metadata" in tool_names
