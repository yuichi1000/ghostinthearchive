"""Unit tests for podcast_agents/agent.py — build_pipeline() + SKIP_AUTHORS."""

from podcast_agents.agent import build_pipeline, SKIP_AUTHORS


class TestBuildPipeline:
    """build_pipeline() ファクトリ関数のテスト。"""

    def test_returns_sequential_agent(self):
        """build_pipeline() は SequentialAgent を返す。"""
        from google.adk.agents import SequentialAgent

        pipeline = build_pipeline()
        assert isinstance(pipeline, SequentialAgent)

    def test_returns_fresh_instance_each_call(self):
        """毎回フレッシュなインスタンスを返す（ADK 単一親制約回避）。"""
        a = build_pipeline()
        b = build_pipeline()
        assert a is not b

    def test_pipeline_has_before_agent_callback(self):
        """パイプラインに before_agent_callback が設定されている。"""
        pipeline = build_pipeline()
        assert pipeline.before_agent_callback is not None
        assert callable(pipeline.before_agent_callback)

    def test_pipeline_has_three_sub_agents(self):
        """サブエージェントが 3 つ（planner, writer, translator）。"""
        pipeline = build_pipeline()
        assert len(pipeline.sub_agents) == 3


class TestSkipAuthors:
    """SKIP_AUTHORS 定数のテスト。"""

    def test_contains_commander_name(self):
        """podcast_script_commander が SKIP_AUTHORS に含まれる。"""
        assert "podcast_script_commander" in SKIP_AUTHORS

    def test_is_frozenset_or_set(self):
        """SKIP_AUTHORS は set 型。"""
        assert isinstance(SKIP_AUTHORS, (set, frozenset))


class TestFactoryFunctions:
    """各エージェントのファクトリ関数が独立インスタンスを返す。"""

    def test_create_script_planner_returns_new_instance(self):
        """create_script_planner() は毎回新しいインスタンスを返す。"""
        from podcast_agents.agents.script_planner import create_script_planner

        a = create_script_planner()
        b = create_script_planner()
        assert a is not b

    def test_create_scriptwriter_returns_new_instance(self):
        """create_scriptwriter() は毎回新しいインスタンスを返す。"""
        from podcast_agents.agents.scriptwriter import create_scriptwriter

        a = create_scriptwriter()
        b = create_scriptwriter()
        assert a is not b

    def test_create_podcast_translator_returns_new_instance(self):
        """create_podcast_translator() は毎回新しいインスタンスを返す。"""
        from podcast_agents.agents.podcast_translator import create_podcast_translator

        a = create_podcast_translator()
        b = create_podcast_translator()
        assert a is not b
