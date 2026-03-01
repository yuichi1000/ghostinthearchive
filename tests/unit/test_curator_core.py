"""Unit tests for curator_agents/core.py — テーマ提案共通ロジック。"""

import json
from unittest.mock import AsyncMock, patch

import pytest


def _identity_probe(themes):
    """プローブをモックするヘルパー: テーマにダミーのカバレッジフィールドを付与。"""
    for t in themes:
        t["coverage_score"] = "HIGH"
        t["primary_apis"] = ["us_archives"]
        t["probe_hits"] = {"us_archives": {"has_content": True, "total_hits": 5}}
    return themes


def _varied_score_probe(themes):
    """テーマごとに異なるスコアを付与するプローブモック。"""
    scores = ["LOW", "HIGH", "MEDIUM"]
    for i, t in enumerate(themes):
        t["coverage_score"] = scores[i % len(scores)]
        t["primary_apis"] = []
        t["probe_hits"] = {}
    return themes


@pytest.fixture
def mock_firestore_queries():
    """Firestore クエリ3つ + プローブをモック。"""
    with patch("curator_agents.core.get_existing_titles", return_value=["Theme A"]), \
         patch("curator_agents.core.get_recent_failures", return_value=[]), \
         patch("curator_agents.core.get_category_distribution", return_value={"HIS": 2}), \
         patch("curator_agents.core.format_category_distribution", return_value="HIS: 2"), \
         patch("curator_agents.core.probe_all_themes", side_effect=_identity_probe):
        yield


@pytest.fixture
def valid_agent_output():
    """Curator エージェントの正常な JSON 出力。"""
    return json.dumps([
        {"theme": "Theme X", "description": "Desc X", "category": "OCC"},
        {"theme": "Theme Y", "description": "Desc Y", "category": "FLK"},
    ])


class TestSuggestThemes:
    """suggest_themes() のテスト。"""

    @pytest.mark.asyncio
    async def test_returns_validated_suggestions(
        self, mock_firestore_queries, valid_agent_output
    ):
        """Should return validated suggestion dicts on success."""
        with patch(
            "curator_agents.core.run_single_agent",
            new_callable=AsyncMock,
            return_value=valid_agent_output,
        ):
            from curator_agents.core import suggest_themes

            result = await suggest_themes()

        assert len(result) == 2
        assert result[0]["theme"] == "Theme X"
        assert result[0]["category"] == "OCC"
        assert result[1]["theme"] == "Theme Y"

    @pytest.mark.asyncio
    async def test_raises_json_decode_error_on_invalid_json(
        self, mock_firestore_queries
    ):
        """Should raise JSONDecodeError when agent output is not valid JSON."""
        with patch(
            "curator_agents.core.run_single_agent",
            new_callable=AsyncMock,
            return_value="not valid json at all",
        ):
            from curator_agents.core import suggest_themes

            with pytest.raises(json.JSONDecodeError):
                await suggest_themes()

    @pytest.mark.asyncio
    async def test_raises_value_error_when_all_fail_validation(
        self, mock_firestore_queries
    ):
        """Should raise ValueError when all suggestions fail schema validation."""
        # category が不正 → 全件バリデーション失敗
        invalid_output = json.dumps([
            {"theme": "T", "description": "D", "category": "INVALID"},
        ])
        with patch(
            "curator_agents.core.run_single_agent",
            new_callable=AsyncMock,
            return_value=invalid_output,
        ):
            from curator_agents.core import suggest_themes

            with pytest.raises(ValueError, match="All suggestions failed"):
                await suggest_themes()

    @pytest.mark.asyncio
    async def test_passes_custom_user_message(self, mock_firestore_queries, valid_agent_output):
        """Should pass user_message and empty_titles_text to agent."""
        with patch(
            "curator_agents.core.run_single_agent",
            new_callable=AsyncMock,
            return_value=valid_agent_output,
        ) as mock_runner:
            from curator_agents.core import suggest_themes

            await suggest_themes(
                user_message="テーマを提案",
                empty_titles_text="(なし)",
            )

        # run_single_agent の呼び出し引数を検証
        call_kwargs = mock_runner.call_args.kwargs
        assert call_kwargs["user_message"] == "テーマを提案"

    @pytest.mark.asyncio
    async def test_strips_markdown_codeblock(self, mock_firestore_queries):
        """Should handle agent output wrapped in markdown code blocks."""
        wrapped = '```json\n[{"theme": "T", "description": "D", "category": "HIS"}]\n```'
        with patch(
            "curator_agents.core.run_single_agent",
            new_callable=AsyncMock,
            return_value=wrapped,
        ):
            from curator_agents.core import suggest_themes

            result = await suggest_themes()

        assert len(result) == 1
        assert result[0]["theme"] == "T"

    @pytest.mark.asyncio
    async def test_raises_value_error_on_failure_marker(self, mock_firestore_queries):
        """Should raise ValueError when agent returns a failure marker."""
        with patch(
            "curator_agents.core.run_single_agent",
            new_callable=AsyncMock,
            return_value="INSUFFICIENT_DATA: No suitable themes could be generated",
        ):
            from curator_agents.core import suggest_themes

            with pytest.raises(ValueError, match="failure marker"):
                await suggest_themes()

    @pytest.mark.asyncio
    async def test_raises_value_error_on_empty_output(self, mock_firestore_queries):
        """Should raise ValueError when agent returns empty output."""
        with patch(
            "curator_agents.core.run_single_agent",
            new_callable=AsyncMock,
            return_value="",
        ):
            from curator_agents.core import suggest_themes

            with pytest.raises(ValueError, match="failure marker"):
                await suggest_themes()

    @pytest.mark.asyncio
    async def test_includes_coverage_score_after_probe(self, mock_firestore_queries, valid_agent_output):
        """Should include coverage_score from probe in results."""
        with patch(
            "curator_agents.core.run_single_agent",
            new_callable=AsyncMock,
            return_value=valid_agent_output,
        ):
            from curator_agents.core import suggest_themes

            result = await suggest_themes()

        assert result[0]["coverage_score"] == "HIGH"
        assert result[0]["primary_apis"] == ["us_archives"]
        assert result[0]["probe_hits"] == {"us_archives": {"has_content": True, "total_hits": 5}}

    @pytest.mark.asyncio
    async def test_results_sorted_by_coverage_score(self):
        """結果が HIGH → MEDIUM → LOW 順にソートされること。"""
        agent_output = json.dumps([
            {"theme": "Low Theme", "description": "D", "category": "HIS"},
            {"theme": "High Theme", "description": "D", "category": "FLK"},
            {"theme": "Medium Theme", "description": "D", "category": "OCC"},
        ])
        with patch("curator_agents.core.get_existing_titles", return_value=[]), \
             patch("curator_agents.core.get_recent_failures", return_value=[]), \
             patch("curator_agents.core.get_category_distribution", return_value={}), \
             patch("curator_agents.core.format_category_distribution", return_value=""), \
             patch("curator_agents.core.probe_all_themes", side_effect=_varied_score_probe), \
             patch(
                 "curator_agents.core.run_single_agent",
                 new_callable=AsyncMock,
                 return_value=agent_output,
             ):
            from curator_agents.core import suggest_themes

            result = await suggest_themes()

        scores = [r["coverage_score"] for r in result]
        assert scores == ["HIGH", "MEDIUM", "LOW"]
