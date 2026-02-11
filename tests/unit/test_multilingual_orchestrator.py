"""Unit tests for MultilingualOrchestrator CustomAgent.

動的オーケストレーションのフロー制御をテストする。
ADK の BaseAgent/ParallelAgent はモックして、ロジック部分のみ検証。
"""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from mystery_agents.agents.multilingual_orchestrator import MultilingualOrchestrator


def _make_mock_agent(name: str):
    """最小限の BaseAgent モックを作成する。"""
    agent = MagicMock()
    agent.name = name

    async def mock_run_async(ctx):
        # 空のイベントストリーム
        return
        yield  # noqa: unreachable — AsyncGenerator として認識させる

    agent.run_async = mock_run_async
    return agent


def _make_session_state(selected_languages=None):
    """InvocationContext モックを作成する。"""
    ctx = MagicMock()
    state = {}
    if selected_languages is not None:
        state["selected_languages"] = selected_languages
    ctx.session.state = state
    return ctx


class TestMultilingualOrchestratorInit:
    """初期化テスト。"""

    def test_sub_agents_registered(self):
        """全エージェントが sub_agents に登録される。"""
        theme = _make_mock_agent("theme_analyzer")
        libs = {"en": _make_mock_agent("librarian_en"), "de": _make_mock_agent("librarian_de")}
        schs = {"en": _make_mock_agent("scholar_en"), "de": _make_mock_agent("scholar_de")}
        cross = _make_mock_agent("cross_reference_scholar")

        orchestrator = MultilingualOrchestrator(
            name="test_orchestrator",
            theme_analyzer=theme,
            all_librarians=libs,
            all_scholars=schs,
            cross_reference_scholar=cross,
        )

        # sub_agents に全エージェントが含まれる
        sub_names = [a.name for a in orchestrator.sub_agents]
        assert "theme_analyzer" in sub_names
        assert "cross_reference_scholar" in sub_names
        assert "librarian_en" in sub_names
        assert "librarian_de" in sub_names
        assert "scholar_en" in sub_names
        assert "scholar_de" in sub_names


class TestMultilingualOrchestratorFlow:
    """フロー制御テスト。"""

    def test_default_fallback_to_en(self):
        """selected_languages がない場合、en のみ実行。"""
        theme = _make_mock_agent("theme_analyzer")
        libs = {
            "en": _make_mock_agent("librarian_en"),
            "de": _make_mock_agent("librarian_de"),
        }
        schs = {
            "en": _make_mock_agent("scholar_en"),
            "de": _make_mock_agent("scholar_de"),
        }
        cross = _make_mock_agent("cross_reference_scholar")

        orchestrator = MultilingualOrchestrator(
            name="test_orchestrator",
            theme_analyzer=theme,
            all_librarians=libs,
            all_scholars=schs,
            cross_reference_scholar=cross,
        )

        ctx = _make_session_state()  # selected_languages なし

        # _run_async_impl は AsyncGenerator なので collect する
        async def run():
            events = []
            async for event in orchestrator._run_async_impl(ctx):
                events.append(event)
            return events

        with patch("mystery_agents.agents.multilingual_orchestrator.ParallelAgent") as MockParallel:
            # ParallelAgent.run_async もモック

            async def mock_parallel_run(ctx_arg):
                return
                yield

            mock_instance = MagicMock()
            mock_instance.run_async = mock_parallel_run
            MockParallel.return_value = mock_instance

            asyncio.run(run())

            # ParallelAgent が2回呼ばれる（Librarian用、Scholar用）
            assert MockParallel.call_count == 2

            # Librarian ParallelAgent の sub_agents に en のみ含まれる
            lib_call_args = MockParallel.call_args_list[0]
            lib_sub_agents = lib_call_args[1]["sub_agents"]
            assert len(lib_sub_agents) == 1
            assert lib_sub_agents[0].name == "librarian_en"

    def test_selected_languages_respected(self):
        """selected_languages に基づいて正しいエージェントが選択される。"""
        theme = _make_mock_agent("theme_analyzer")
        libs = {
            "en": _make_mock_agent("librarian_en"),
            "de": _make_mock_agent("librarian_de"),
            "es": _make_mock_agent("librarian_es"),
        }
        schs = {
            "en": _make_mock_agent("scholar_en"),
            "de": _make_mock_agent("scholar_de"),
            "es": _make_mock_agent("scholar_es"),
        }
        cross = _make_mock_agent("cross_reference_scholar")

        orchestrator = MultilingualOrchestrator(
            name="test_orchestrator",
            theme_analyzer=theme,
            all_librarians=libs,
            all_scholars=schs,
            cross_reference_scholar=cross,
        )

        # ThemeAnalyzer が selected_languages を設定するのをシミュレート
        ctx = _make_session_state(selected_languages=["en", "de"])

        async def run():
            events = []
            async for event in orchestrator._run_async_impl(ctx):
                events.append(event)
            return events

        with patch("mystery_agents.agents.multilingual_orchestrator.ParallelAgent") as MockParallel:
            async def mock_parallel_run(ctx_arg):
                return
                yield

            mock_instance = MagicMock()
            mock_instance.run_async = mock_parallel_run
            MockParallel.return_value = mock_instance

            asyncio.run(run())

            # Librarian: en + de の2つ
            lib_call = MockParallel.call_args_list[0]
            lib_names = [a.name for a in lib_call[1]["sub_agents"]]
            assert "librarian_en" in lib_names
            assert "librarian_de" in lib_names
            assert "librarian_es" not in lib_names

            # Scholar: en + de の2つ
            sch_call = MockParallel.call_args_list[1]
            sch_names = [a.name for a in sch_call[1]["sub_agents"]]
            assert "scholar_en" in sch_names
            assert "scholar_de" in sch_names
            assert "scholar_es" not in sch_names

    def test_invalid_selected_languages_fallback(self):
        """selected_languages が不正な場合はフォールバック。"""
        theme = _make_mock_agent("theme_analyzer")
        libs = {"en": _make_mock_agent("librarian_en")}
        schs = {"en": _make_mock_agent("scholar_en")}
        cross = _make_mock_agent("cross_reference_scholar")

        orchestrator = MultilingualOrchestrator(
            name="test_orchestrator",
            theme_analyzer=theme,
            all_librarians=libs,
            all_scholars=schs,
            cross_reference_scholar=cross,
        )

        # 不正な型
        ctx = _make_session_state()
        ctx.session.state["selected_languages"] = "not a list"

        async def run():
            events = []
            async for event in orchestrator._run_async_impl(ctx):
                events.append(event)
            return events

        with patch("mystery_agents.agents.multilingual_orchestrator.ParallelAgent") as MockParallel:
            async def mock_parallel_run(ctx_arg):
                return
                yield

            mock_instance = MagicMock()
            mock_instance.run_async = mock_parallel_run
            MockParallel.return_value = mock_instance

            asyncio.run(run())

            # フォールバックで en のみ
            lib_call = MockParallel.call_args_list[0]
            lib_sub = lib_call[1]["sub_agents"]
            assert len(lib_sub) == 1
            assert lib_sub[0].name == "librarian_en"
