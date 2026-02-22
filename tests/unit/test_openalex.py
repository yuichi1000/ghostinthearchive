"""Unit tests for OpenAlex academic search tool."""

import json
import os

import responses

from mystery_agents.tools.openalex import (
    OPENALEX_BASE_URL,
    _aggregate_temporal,
    _extract_key_concepts,
    search_academic_papers,
)


# === テスト用レスポンスデータ ===

_LANG_RESPONSE = {
    "group_by": [
        {"key": "en", "count": 35},
        {"key": "de", "count": 5},
        {"key": "ja", "count": 2},
    ]
}

_YEAR_RESPONSE = {
    "group_by": [
        {"key": "1890", "count": 1},
        {"key": "1945", "count": 2},
        {"key": "1960", "count": 5},
        {"key": "1985", "count": 10},
        {"key": "2005", "count": 15},
        {"key": "2020", "count": 9},
    ]
}

_TOP_PAPERS_RESPONSE = {
    "results": [
        {
            "title": "Salem Witch Trials: A Cultural History",
            "publication_year": 2018,
            "cited_by_count": 250,
            "doi": "https://doi.org/10.1000/test1",
            "language": "en",
            "topics": [
                {"display_name": "folklore"},
                {"display_name": "cultural anthropology"},
            ],
            "keywords": [
                {"display_name": "witch trials"},
                {"display_name": "oral tradition"},
            ],
        },
        {
            "title": "Hexenprozesse und Volksglauben",
            "publication_year": 2015,
            "cited_by_count": 120,
            "doi": "https://doi.org/10.1000/test2",
            "language": "de",
            "topics": [
                {"display_name": "folklore"},
                {"display_name": "social history"},
            ],
            "keywords": [
                {"display_name": "witch trials"},
            ],
        },
        {
            "title": "Puritan Society and Spectral Evidence",
            "publication_year": 2020,
            "cited_by_count": 95,
            "doi": "https://doi.org/10.1000/test3",
            "language": "en",
            "topics": [
                {"display_name": "cultural anthropology"},
            ],
            "keywords": [
                {"display_name": "spectral evidence"},
                {"display_name": "oral tradition"},
            ],
        },
    ]
}

_EMPTY_LANG_RESPONSE = {"group_by": []}
_EMPTY_YEAR_RESPONSE = {"group_by": []}
_EMPTY_TOP_RESPONSE = {"results": []}


def _register_standard_responses():
    """3つの標準 API レスポンスを登録する。"""
    responses.add(
        responses.GET,
        f"{OPENALEX_BASE_URL}/works",
        json=_LANG_RESPONSE,
        status=200,
    )
    responses.add(
        responses.GET,
        f"{OPENALEX_BASE_URL}/works",
        json=_YEAR_RESPONSE,
        status=200,
    )
    responses.add(
        responses.GET,
        f"{OPENALEX_BASE_URL}/works",
        json=_TOP_PAPERS_RESPONSE,
        status=200,
    )


class TestSearchAcademicPapers:
    """search_academic_papers 関数のテスト。"""

    @responses.activate
    def test_normal_search(self, monkeypatch):
        """正常な検索 — 3つの API レスポンスから正しい JSON が返ること。"""
        monkeypatch.setenv("OPENALEX_API_KEY", "test-key")
        _register_standard_responses()

        result = json.loads(search_academic_papers("Salem witch trials folklore"))

        assert result["status"] == "ok"
        assert result["papers_found"] == 42
        assert result["language_distribution"]["en"] == 35
        assert result["language_distribution"]["de"] == 5
        assert result["language_distribution"]["ja"] == 2
        assert result["temporal_distribution"]["pre-1950"] == 3
        assert result["temporal_distribution"]["1950-1999"] == 15
        assert result["temporal_distribution"]["2000-present"] == 24
        assert len(result["key_concepts"]) > 0
        assert len(result["top_papers"]) == 3
        assert result["top_papers"][0]["title"] == "Salem Witch Trials: A Cultural History"

    def test_api_key_not_set(self, monkeypatch):
        """OPENALEX_API_KEY 未設定時のエラーメッセージ。"""
        monkeypatch.delenv("OPENALEX_API_KEY", raising=False)

        result = json.loads(search_academic_papers("test query"))

        assert result["status"] == "error"
        assert "OPENALEX_API_KEY" in result["error"]

    @responses.activate
    def test_empty_results(self, monkeypatch):
        """空の検索結果 — papers_found=0。"""
        monkeypatch.setenv("OPENALEX_API_KEY", "test-key")
        responses.add(
            responses.GET,
            f"{OPENALEX_BASE_URL}/works",
            json=_EMPTY_LANG_RESPONSE,
            status=200,
        )
        responses.add(
            responses.GET,
            f"{OPENALEX_BASE_URL}/works",
            json=_EMPTY_YEAR_RESPONSE,
            status=200,
        )
        responses.add(
            responses.GET,
            f"{OPENALEX_BASE_URL}/works",
            json=_EMPTY_TOP_RESPONSE,
            status=200,
        )

        result = json.loads(search_academic_papers("nonexistent topic xyz"))

        assert result["status"] == "ok"
        assert result["papers_found"] == 0
        assert result["language_distribution"] == {}
        assert result["key_concepts"] == []
        assert result["top_papers"] == []

    @responses.activate
    def test_http_500_error(self, monkeypatch):
        """HTTP 500 エラー時のエラーハンドリング。"""
        monkeypatch.setenv("OPENALEX_API_KEY", "test-key")
        # リトライセッションが 500 を複数回リトライした後にエラーを返す
        responses.add(
            responses.GET,
            f"{OPENALEX_BASE_URL}/works",
            json={"error": "Internal Server Error"},
            status=500,
        )

        result = json.loads(search_academic_papers("test query"))

        assert result["status"] == "error"
        assert "500" in result["error"]

    @responses.activate
    def test_language_and_year_filters(self, monkeypatch):
        """言語・年代フィルタが API リクエストに反映されること。"""
        monkeypatch.setenv("OPENALEX_API_KEY", "test-key")
        _register_standard_responses()

        search_academic_papers(
            "Salem witch trials",
            language="en",
            year_from="1900",
            year_to="2020",
        )

        # 最初のリクエストのパラメータを検証（URL エンコードされている）
        from urllib.parse import unquote
        first_url = unquote(responses.calls[0].request.url)
        assert "language:en" in first_url
        assert "publication_year:1900-2020" in first_url

    @responses.activate
    def test_api_key_in_request(self, monkeypatch):
        """API キーがリクエストパラメータに含まれること。"""
        monkeypatch.setenv("OPENALEX_API_KEY", "my-secret-key")
        _register_standard_responses()

        search_academic_papers("test query")

        for call in responses.calls:
            assert "api_key=my-secret-key" in call.request.url


class TestAggregateTemporalDistribution:
    """_aggregate_temporal 関数のテスト。"""

    def test_three_ranges(self):
        """個別年が3つの時代区分に正しく集約されること。"""
        year_counts = {
            "1800": 2, "1920": 3, "1949": 1,
            "1950": 4, "1975": 6, "1999": 2,
            "2000": 8, "2015": 10, "2025": 5,
        }
        result = _aggregate_temporal(year_counts)

        assert result["pre-1950"] == 6
        assert result["1950-1999"] == 12
        assert result["2000-present"] == 23

    def test_empty_input(self):
        """空の入力に対して全レンジが0。"""
        result = _aggregate_temporal({})

        assert result["pre-1950"] == 0
        assert result["1950-1999"] == 0
        assert result["2000-present"] == 0

    def test_invalid_year_ignored(self):
        """数値に変換できない年は無視される。"""
        result = _aggregate_temporal({"unknown": 5, "2020": 3})

        assert result["2000-present"] == 3
        assert result["pre-1950"] == 0
        assert result["1950-1999"] == 0


class TestExtractKeyConcepts:
    """_extract_key_concepts 関数のテスト。"""

    def test_frequency_ordering(self):
        """頻出概念が正しく抽出されること。"""
        works = _TOP_PAPERS_RESPONSE["results"]
        concepts = _extract_key_concepts(works)

        # "folklore" は 2 回、"witch trials" は 2 回、"cultural anthropology" は 2 回
        assert len(concepts) <= 5
        assert "folklore" in concepts
        assert "witch trials" in concepts

    def test_empty_works(self):
        """論文がない場合は空リスト。"""
        concepts = _extract_key_concepts([])
        assert concepts == []

    def test_max_concepts_limit(self):
        """max_concepts パラメータが制限として機能すること。"""
        works = _TOP_PAPERS_RESPONSE["results"]
        concepts = _extract_key_concepts(works, max_concepts=2)
        assert len(concepts) <= 2
