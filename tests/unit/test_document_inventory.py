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
                        "source_type": "nypl",
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
                        "source_type": "nypl",
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
        assert "NYPL Digital Collections" in result["by_archive"]
        assert "Internet Archive" in result["by_archive"]
        assert len(result["by_archive"]["NYPL Digital Collections"]) == 2
        assert len(result["by_archive"]["Internet Archive"]) == 1

    def test_excludes_summary_and_raw_text(self):
        """summary と raw_text が出力に含まれない。"""
        ctx = make_tool_context(state={
            "raw_search_results_en": [{
                "documents": [{
                    "title": "Test Doc",
                    "source_url": "https://loc.gov/item/1",
                    "source_type": "nypl",
                    "date": "1893-01-01",
                    "language": "en",
                    "summary": "This should NOT appear",
                    "raw_text": "This should NOT appear either",
                }],
            }],
        })

        result = json.loads(get_document_inventory(ctx))

        doc = result["by_archive"]["NYPL Digital Collections"][0]
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
                        "source_type": "nypl",
                        "language": "en",
                    },
                ],
            }],
            "raw_search_results_ja": [{
                "documents": [
                    {
                        "title": "Doc A (ja)",
                        "source_url": "https://loc.gov/item/same",
                        "source_type": "nypl",
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
                    "source_type": "nypl",
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
        assert "NYPL Digital Collections" in result["by_archive"]
        assert "NDL (National Diet Library, Japan)" in result["by_archive"]

    def test_archive_summary_format(self):
        """archive_summary が件数降順でフォーマットされる。"""
        ctx = make_tool_context(state={
            "raw_search_results_en": [{
                "documents": [
                    {"title": "IA 1", "source_url": "https://ia.org/1", "source_type": "internet_archive", "language": "en"},
                    {"title": "IA 2", "source_url": "https://ia.org/2", "source_type": "internet_archive", "language": "en"},
                    {"title": "IA 3", "source_url": "https://ia.org/3", "source_type": "internet_archive", "language": "en"},
                    {"title": "LOC 1", "source_url": "https://loc.gov/1", "source_type": "nypl", "language": "en"},
                ],
            }],
        })

        result = json.loads(get_document_inventory(ctx))

        # IA 3件 > LOC 1件 の順
        assert result["archive_summary"].startswith("Internet Archive: 3 docs")
        assert "NYPL Digital Collections: 1 docs" in result["archive_summary"]

    def test_base_key_raw_search_results(self):
        """ベースキー raw_search_results からも文書を取得する。"""
        ctx = make_tool_context(state={
            "raw_search_results": [{
                "documents": [{
                    "title": "Base Doc",
                    "source_url": "https://example.com/base/1",
                    "source_type": "europeana",
                    "language": "en",
                }],
            }],
        })

        result = json.loads(get_document_inventory(ctx))

        assert result["total_documents"] == 1
        assert "Europeana" in result["by_archive"]

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
                    {"title": "No URL", "source_url": "", "source_type": "nypl", "language": "en"},
                    {"title": "Good", "source_url": "https://loc.gov/1", "source_type": "nypl", "language": "en"},
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
                    "source_type": "nypl",
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


class TestDocumentInventoryReferenceKeywords:
    """reference_keywords_matched のインベントリ表示テスト。"""

    def test_inventory_includes_reference_keywords_matched_count(self):
        """インベントリの各エントリに reference_keywords_matched 数が含まれるべき。"""
        ctx = make_tool_context(state={
            "raw_search_results_en": [{
                "documents": [
                    {
                        "title": "Watseka Wonder",
                        "source_url": "https://loc.gov/item/1",
                        "source_type": "nypl",
                        "date": "1877-01-01",
                        "language": "en",
                        "keywords_matched": ["spirit"],
                        "reference_keywords_matched": ["Watseka", "Vennum"],
                    },
                    {
                        "title": "Spirit Phenomena",
                        "source_url": "https://archive.org/details/1",
                        "source_type": "internet_archive",
                        "date": "1880-06-15",
                        "language": "en",
                        "keywords_matched": ["spirit", "identity"],
                        "reference_keywords_matched": [],
                    },
                ],
            }],
        })

        result = json.loads(get_document_inventory(ctx))

        assert result["status"] == "ok"
        nypl_docs = result["by_archive"]["NYPL Digital Collections"]
        ia_docs = result["by_archive"]["Internet Archive"]
        assert nypl_docs[0]["reference_keywords_matched"] == 2
        assert ia_docs[0]["reference_keywords_matched"] == 0


class TestArchiveImagesInInventory:
    """archive_images セクションのテスト。"""

    def test_returns_archive_images_metadata(self):
        """archive_images のメタデータ（title, source_url, source_type）が返される。"""
        ctx = make_tool_context(state={
            "raw_search_results_en": [{
                "documents": [{
                    "title": "Doc",
                    "source_url": "https://loc.gov/1",
                    "source_type": "nypl",
                    "language": "en",
                }],
            }],
            "archive_images": [
                {
                    "title": "Historical Photo",
                    "source_url": "https://loc.gov/img/1",
                    "thumbnail_url": "https://loc.gov/img/1/thumb",
                    "image_url": "https://loc.gov/img/1/full",
                    "source_type": "nypl",
                    "date": "1893-01-01",
                },
                {
                    "title": "Map of Boston",
                    "source_url": "https://europeana.eu/img/2",
                    "thumbnail_url": "https://europeana.eu/img/2/thumb",
                    "image_url": "https://europeana.eu/img/2/full",
                    "source_type": "europeana",
                    "date": "1850-06-15",
                },
            ],
        })

        result = json.loads(get_document_inventory(ctx))

        assert result["status"] == "ok"
        assert len(result["archive_images"]) == 2
        img0 = result["archive_images"][0]
        assert img0["index"] == 0
        assert img0["title"] == "Historical Photo"
        assert img0["source_url"] == "https://loc.gov/img/1"
        assert img0["source_type"] == "nypl"
        # thumbnail_url, image_url, date は含まれない（審査に不要）
        assert "thumbnail_url" not in img0
        assert "image_url" not in img0
        assert "date" not in img0

    def test_empty_archive_images_returns_empty_list(self):
        """archive_images が空リストの場合は空リストを返す。"""
        ctx = make_tool_context(state={
            "raw_search_results_en": [{
                "documents": [{
                    "title": "Doc",
                    "source_url": "https://loc.gov/1",
                    "source_type": "nypl",
                    "language": "en",
                }],
            }],
            "archive_images": [],
        })

        result = json.loads(get_document_inventory(ctx))

        assert result["archive_images"] == []

    def test_no_archive_images_key_returns_empty_list(self):
        """archive_images キーがない場合は空リストを返す。"""
        ctx = make_tool_context(state={
            "raw_search_results_en": [{
                "documents": [{
                    "title": "Doc",
                    "source_url": "https://loc.gov/1",
                    "source_type": "nypl",
                    "language": "en",
                }],
            }],
        })

        result = json.loads(get_document_inventory(ctx))

        assert result["archive_images"] == []
