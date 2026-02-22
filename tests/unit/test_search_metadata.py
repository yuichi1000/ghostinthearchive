"""Unit tests for get_search_metadata tool."""

import json
from unittest.mock import MagicMock

from mystery_agents.tools.search_metadata import get_search_metadata


class TestGetSearchMetadataNoData:
    """raw_search_results がない場合のテスト。"""

    def test_no_tool_context_returns_no_data(self):
        """tool_context が None → no_data を返す。"""
        result = json.loads(get_search_metadata(None))
        assert result["status"] == "no_data"
        assert result["apis_searched"] == []

    def test_empty_state_returns_no_data(self):
        """state にキーがない → no_data を返す。"""
        ctx = MagicMock()
        ctx.state = {}
        result = json.loads(get_search_metadata(ctx))
        assert result["status"] == "no_data"

    def test_empty_list_returns_no_data(self):
        """raw_search_results が空リスト → no_data を返す。"""
        ctx = MagicMock()
        ctx.state = {"raw_search_results": []}
        result = json.loads(get_search_metadata(ctx))
        assert result["status"] == "no_data"


class TestGetSearchMetadataNewspapers:
    """search_newspapers 形式の結果からの抽出テスト。"""

    def test_extracts_newspaper_source(self):
        """chronicling_america の検索結果が正しく抽出される。"""
        ctx = MagicMock()
        ctx.state = {
            "raw_search_results": [
                {
                    "source": "chronicling_america",
                    "keywords_used": ["ghost", "ship"],
                    "total_hits": 42,
                    "documents_returned": 10,
                    "documents": [],
                    "error": None,
                }
            ]
        }
        result = json.loads(get_search_metadata(ctx))
        assert result["status"] == "ok"
        assert "chronicling_america" in result["apis_searched"]
        assert "chronicling_america" in result["apis_with_results"]
        assert result["per_api_stats"]["chronicling_america"]["total_hits"] == 42
        assert result["per_api_stats"]["chronicling_america"]["documents_returned"] == 10

    def test_zero_results_in_without_results(self):
        """documents_returned が 0 → apis_without_results に含まれる。"""
        ctx = MagicMock()
        ctx.state = {
            "raw_search_results": [
                {
                    "source": "chronicling_america",
                    "total_hits": 0,
                    "documents_returned": 0,
                    "documents": [],
                    "error": None,
                }
            ]
        }
        result = json.loads(get_search_metadata(ctx))
        assert "chronicling_america" in result["apis_without_results"]
        assert result["apis_with_results"] == []


class TestGetSearchMetadataArchives:
    """search_archives 形式の sources_searched dict からの抽出テスト。"""

    def test_extracts_sources_searched(self):
        """sources_searched dict の各 API 統計が抽出される。"""
        ctx = MagicMock()
        ctx.state = {
            "raw_search_results": [
                {
                    "sources_searched": {
                        "loc": {"name": "Library of Congress", "total_hits": 15, "documents_returned": 5},
                        "dpla": {"name": "DPLA", "total_hits": 0, "documents_returned": 0},
                        "europeana": {"name": "Europeana", "total_hits": 3, "documents_returned": 2},
                    },
                    "total_documents": 7,
                    "documents": [],
                }
            ]
        }
        result = json.loads(get_search_metadata(ctx))
        assert result["status"] == "ok"
        assert sorted(result["apis_searched"]) == ["dpla", "europeana", "loc"]
        assert sorted(result["apis_with_results"]) == ["europeana", "loc"]
        assert result["apis_without_results"] == ["dpla"]

    def test_errors_propagated(self):
        """search_archives の errors dict が伝搬される。"""
        ctx = MagicMock()
        ctx.state = {
            "raw_search_results": [
                {
                    "sources_searched": {
                        "loc": {"name": "LOC", "total_hits": 5, "documents_returned": 3},
                    },
                    "errors": {"dpla": "Connection timeout"},
                    "documents": [],
                }
            ]
        }
        result = json.loads(get_search_metadata(ctx))
        assert result["errors"]["dpla"] == "Connection timeout"

    def test_fallback_used_propagated(self):
        """fallback_used フラグが伝搬される。"""
        ctx = MagicMock()
        ctx.state = {
            "raw_search_results": [
                {
                    "sources_searched": {
                        "loc": {"name": "LOC", "total_hits": 1, "documents_returned": 1},
                    },
                    "fallback_used": True,
                    "documents": [],
                }
            ]
        }
        result = json.loads(get_search_metadata(ctx))
        assert result["fallback_used"] is True


class TestGetSearchMetadataLanguageKeys:
    """言語別キー（raw_search_results_de 等）の読み取りテスト。"""

    def test_reads_language_specific_keys(self):
        """raw_search_results_de / raw_search_results_ja が読み取られる。"""
        ctx = MagicMock()
        ctx.state = {
            "raw_search_results_de": [
                {
                    "sources_searched": {
                        "ddb": {"name": "Deutsche Digitale Bibliothek", "total_hits": 8, "documents_returned": 3},
                    },
                    "documents": [],
                }
            ],
            "raw_search_results_ja": [
                {
                    "sources_searched": {
                        "ndl": {"name": "National Diet Library", "total_hits": 12, "documents_returned": 7},
                    },
                    "documents": [],
                }
            ],
        }
        # MagicMock.keys() はデフォルトで空なので、dict を使う代わりに state をプレーン dict にする
        ctx.state = dict(ctx.state)
        result = json.loads(get_search_metadata(ctx))
        assert result["status"] == "ok"
        assert sorted(result["languages_searched"]) == ["de", "ja"]
        assert "ddb" in result["apis_searched"]
        assert "ndl" in result["apis_searched"]

    def test_aggregates_same_api_across_languages(self):
        """同じ API が複数言語で使用された場合、統計が加算される。"""
        ctx = MagicMock()
        ctx.state = {
            "raw_search_results": [
                {
                    "sources_searched": {
                        "europeana": {"name": "Europeana", "total_hits": 10, "documents_returned": 5},
                    },
                    "documents": [],
                }
            ],
            "raw_search_results_de": [
                {
                    "sources_searched": {
                        "europeana": {"name": "Europeana", "total_hits": 8, "documents_returned": 3},
                    },
                    "documents": [],
                }
            ],
        }
        ctx.state = dict(ctx.state)
        result = json.loads(get_search_metadata(ctx))
        assert result["per_api_stats"]["europeana"]["total_hits"] == 18
        assert result["per_api_stats"]["europeana"]["documents_returned"] == 8


class TestGetSearchMetadataMixed:
    """newspaper + archives が混在するケースのテスト。"""

    def test_mixed_sources(self):
        """search_newspapers + search_archives の結果が両方抽出される。"""
        ctx = MagicMock()
        ctx.state = {
            "raw_search_results": [
                {
                    "source": "chronicling_america",
                    "total_hits": 20,
                    "documents_returned": 8,
                    "documents": [],
                    "error": None,
                },
                {
                    "sources_searched": {
                        "loc": {"name": "LOC", "total_hits": 5, "documents_returned": 2},
                        "dpla": {"name": "DPLA", "total_hits": 0, "documents_returned": 0},
                    },
                    "documents": [],
                },
            ]
        }
        result = json.loads(get_search_metadata(ctx))
        assert sorted(result["apis_searched"]) == ["chronicling_america", "dpla", "loc"]
        assert sorted(result["apis_with_results"]) == ["chronicling_america", "loc"]
        assert result["apis_without_results"] == ["dpla"]
