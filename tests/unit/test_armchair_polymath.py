"""Unit tests for Armchair Polymath agent configuration."""

from mystery_agents.agents.armchair_polymath import (
    armchair_polymath_agent,
)
from mystery_agents.tools.search_metadata import get_search_metadata


class TestArmchairPolymathTools:
    def test_tools_include_get_search_metadata(self):
        """armchair_polymath_agent の tools に get_search_metadata が含まれる。"""
        tool_functions = [t for t in armchair_polymath_agent.tools if callable(t)]
        tool_names = [t.__name__ for t in tool_functions]
        assert "get_search_metadata" in tool_names
