"""Unit tests for podcast_agents/agents/script_planner.py - ScriptPlanner エージェント定義。"""

from podcast_agents.agents.script_planner import script_planner_agent
from podcast_agents.tools.script_tools import save_script_outline


class TestScriptPlannerAgent:
    """ScriptPlanner エージェント定義のテスト。"""

    def test_output_key(self):
        """output_key が script_outline。"""
        assert script_planner_agent.output_key == "script_outline"

    def test_tools_include_save_script_outline(self):
        """tools に save_script_outline が含まれる。"""
        tool_funcs = [t.func if hasattr(t, "func") else t for t in script_planner_agent.tools]
        assert save_script_outline in tool_funcs
