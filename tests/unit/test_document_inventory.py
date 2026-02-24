"""Unit tests for mystery_agents/tools/document_inventory.py"""

import json

from mystery_agents.tools.document_inventory import get_document_inventory
from tests.fakes import make_tool_context


class TestGetDocumentInventory:
    """get_document_inventory のテスト"""

    def test_no_tool_context_returns_no_data(self):
        """tool_context が None の場合は no_data を返す。"""
        result = json.loads(get_document_inventory(None))

        assert result["status"] == "no_data"
        assert result["total_documents"] == 0

    def test_empty_state_returns_no_data(self):
        """セッション状態が空の場合は no_data を返す。"""
        ctx = make_tool_context(state={})

        result = json.loads(get_document_inventory(ctx))

        assert result["status"] == "no_data"

    def test_groups_documents_by_archive(self):
        """文書がアーカイブ別にグループ化される。"""
        ctx = make_tool_context(state={
            "raw_search_results_en": [{
                "documents": [
                    {
                        "title": "LOC Doc 1",
                        "source_url": "https://loc.gov/item/1",
                        "source_type": "loc_digital",
                        "date": "1893-01-01",
                        "language": "en",
                        "summary": "should be excluded",
                    },
                    {
                        "title": "IA Doc 1",
                        "source_url": "https://archive.org/details/1",
                        "source_type": "internet_archive",
                        "date": "1893-06-15",
                        "language": "en",
                        "summary": "should be excluded",
                    },
                    {
                        "title": "LOC Doc 2",
                        "source_url": "https://loc.gov/item/2",
                        "source_type": "loc_digital",
                        "date": "1894-03-20",
                        "language": "en",
                        "summary": "should be excluded",
                    },
                ],
            }],
        })

        result = json.loads(get_document_inventory(ctx))

        assert result["status"] == "ok"
        assert result["total_documents"] == 3
        assert "LOC Digital Collections" in result["by_archive"]
        assert "Internet Archive" in result["by_archive"]
        assert len(result["by_archive"]["LOC Digital Collections"]) == 2
        assert len(result["by_archive"]["Internet Archive"]) == 1

    def test_excludes_summary_and_raw_text(self):
        """summary と raw_text が出力に含まれない。"""
        ctx = make_tool_context(state={
            "raw_search_results_en": [{
                "documents": [{
                    "title": "Test Doc",
                    "source_url": "https://loc.gov/item/1",
                    "source_type": "loc_digital",
                    "date": "1893-01-01",
                    "language": "en",
                    "summary": "This should NOT appear",
                    "raw_text": "This should NOT appear either",
                }],
            }],
        })

        result = json.loads(get_document_inventory(ctx))

        doc = result["by_archive"]["LOC Digital Collections"][0]
        assert "summary" not in doc
        assert "raw_text" not in doc
        assert doc["title"] == "Test Doc"
        assert doc["source_url"] == "https://loc.gov/item/1"
        assert doc["date"] == "1893-01-01"
        assert doc["language"] == "en"

    def test_deduplicates_by_url(self):
        """同一 URL の文書は重複除去される。"""
        ctx = make_tool_context(state={
            "raw_search_results_en": [{
                "documents": [
                    {
                        "title": "Doc A",
                        "source_url": "https://loc.gov/item/same",
                        "source_type": "loc_digital",
                        "language": "en",
                    },
                ],
            }],
            "raw_search_results_ja": [{
                "documents": [
                    {
                        "title": "Doc A (ja)",
                        "source_url": "https://loc.gov/item/same",
                        "source_type": "loc_digital",
                        "language": "ja",
                    },
                ],
            }],
        })

        result = json.loads(get_document_inventory(ctx))

        assert result["total_documents"] == 1

    def test_collects_from_multiple_language_keys(self):
        """複数言語の raw_search_results を集約する。"""
        ctx = make_tool_context(state={
            "raw_search_results_en": [{
                "documents": [{
                    "title": "EN Doc",
                    "source_url": "https://loc.gov/en/1",
                    "source_type": "loc_digital",
                    "language": "en",
                }],
            }],
            "raw_search_results_ja": [{
                "documents": [{
                    "title": "JA Doc",
                    "source_url": "https://ndl.go.jp/ja/1",
                    "source_type": "ndl",
                    "language": "ja",
                }],
            }],
        })

        result = json.loads(get_document_inventory(ctx))

        assert result["total_documents"] == 2
        assert "LOC Digital Collections" in result["by_archive"]
        assert "NDL (National Diet Library, Japan)" in result["by_archive"]

    def test_archive_summary_format(self):
        """archive_summary が件数降順でフォーマットされる。"""
        ctx = make_tool_context(state={
            "raw_search_results_en": [{
                "documents": [
                    {"title": "IA 1", "source_url": "https://ia.org/1", "source_type": "internet_archive", "language": "en"},
                    {"title": "IA 2", "source_url": "https://ia.org/2", "source_type": "internet_archive", "language": "en"},
                    {"title": "IA 3", "source_url": "https://ia.org/3", "source_type": "internet_archive", "language": "en"},
                    {"title": "LOC 1", "source_url": "https://loc.gov/1", "source_type": "loc_digital", "language": "en"},
                ],
            }],
        })

        result = json.loads(get_document_inventory(ctx))

        # IA 3件 > LOC 1件 の順
        assert result["archive_summary"].startswith("Internet Archive: 3 docs")
        assert "LOC Digital Collections: 1 docs" in result["archive_summary"]

    def test_base_key_raw_search_results(self):
        """ベースキー raw_search_results からも文書を取得する。"""
        ctx = make_tool_context(state={
            "raw_search_results": [{
                "documents": [{
                    "title": "Base Doc",
                    "source_url": "https://example.com/base/1",
                    "source_type": "dpla",
                    "language": "en",
                }],
            }],
        })

        result = json.loads(get_document_inventory(ctx))

        assert result["total_documents"] == 1
        assert "DPLA" in result["by_archive"]

    def test_unknown_source_type_uses_key_as_name(self):
        """未知の source_type はキーをそのまま表示名にする。"""
        ctx = make_tool_context(state={
            "raw_search_results_en": [{
                "documents": [{
                    "title": "Unknown",
                    "source_url": "https://unknown.org/1",
                    "source_type": "new_archive",
                    "language": "en",
                }],
            }],
        })

        result = json.loads(get_document_inventory(ctx))

        assert "new_archive" in result["by_archive"]

    def test_skips_documents_without_source_url(self):
        """source_url が空の文書はスキップされる。"""
        ctx = make_tool_context(state={
            "raw_search_results_en": [{
                "documents": [
                    {"title": "No URL", "source_url": "", "source_type": "loc_digital", "language": "en"},
                    {"title": "Good", "source_url": "https://loc.gov/1", "source_type": "loc_digital", "language": "en"},
                ],
            }],
        })

        result = json.loads(get_document_inventory(ctx))

        assert result["total_documents"] == 1

    def test_sets_inventory_consulted_flag(self):
        """正常実行後に _inventory_consulted フラグがセットされる。"""
        ctx = make_tool_context(state={
            "raw_search_results_en": [{
                "documents": [{
                    "title": "Doc",
                    "source_url": "https://loc.gov/1",
                    "source_type": "loc_digital",
                    "language": "en",
                }],
            }],
        })

        get_document_inventory(ctx)

        assert ctx.state["_inventory_consulted"] is True

    def test_no_data_does_not_set_flag(self):
        """no_data の場合はフラグがセットされない。"""
        ctx = make_tool_context(state={})

        get_document_inventory(ctx)

        assert "_inventory_consulted" not in ctx.state
