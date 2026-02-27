"""証拠の妥当性検証テスト。

多層防御（Librarian フィルタ → Scholar ツール検証 → Publisher 監査ログ）
による false positive 排除をテストする。
"""

import json
import logging

import pytest

from tests.fakes import make_archive_doc, make_tool_context


# ---------------------------------------------------------------------------
# Layer 1: Librarian ハードフィルタ
# ---------------------------------------------------------------------------


class TestFilterIrrelevantDocuments:
    """_filter_irrelevant_documents のテスト。"""

    def test_filter_removes_zero_match_docs(self):
        """keywords_matched が空のドキュメントを除外する。"""
        from mystery_agents.tools.search_orchestration import _filter_irrelevant_documents

        docs = [
            make_archive_doc(url="https://example.com/1", keywords_matched=["key1"]),
            make_archive_doc(url="https://example.com/2", keywords_matched=[]),
        ]
        result, removed = _filter_irrelevant_documents(docs)
        assert len(result) == 1
        assert result[0].source_url == "https://example.com/1"
        assert removed == 1

    def test_filter_keeps_positive_match_docs(self):
        """1つ以上のキーワード一致があるドキュメントを保持する。"""
        from mystery_agents.tools.search_orchestration import _filter_irrelevant_documents

        docs = [
            make_archive_doc(url="https://example.com/1", keywords_matched=["a"]),
            make_archive_doc(url="https://example.com/2", keywords_matched=["a", "b"]),
        ]
        result, removed = _filter_irrelevant_documents(docs)
        assert len(result) == 2
        assert removed == 0

    def test_filter_empty_input(self):
        """空リスト → 空リスト。"""
        from mystery_agents.tools.search_orchestration import _filter_irrelevant_documents

        result, removed = _filter_irrelevant_documents([])
        assert result == []
        assert removed == 0

    def test_filter_all_zero_match(self):
        """全件0一致 → 空リスト。"""
        from mystery_agents.tools.search_orchestration import _filter_irrelevant_documents

        docs = [
            make_archive_doc(url="https://example.com/1", keywords_matched=[]),
            make_archive_doc(url="https://example.com/2", keywords_matched=[]),
        ]
        result, removed = _filter_irrelevant_documents(docs)
        assert result == []
        assert removed == 2


class TestRankDocumentsExcludesZeroMatch:
    """_rank_documents 経由での0一致ドキュメント排除テスト。"""

    def test_rank_documents_excludes_zero_match(self):
        """_rank_documents 経由で0一致 doc が結果に含まれない。"""
        from mystery_agents.tools.search_orchestration import _rank_documents

        docs = [
            make_archive_doc(url="https://example.com/1", keywords_matched=["key"]),
            make_archive_doc(url="https://example.com/2", keywords_matched=[]),
            make_archive_doc(url="https://example.com/3", keywords_matched=["a", "b"]),
        ]
        result = _rank_documents(docs)
        urls = [d.source_url for d in result]
        assert "https://example.com/2" not in urls
        assert len(result) == 2


class TestAccumulateImagesExcludesZeroMatch:
    """_accumulate_archive_images の0一致フィルタテスト。"""

    def test_accumulate_images_excludes_zero_match(self):
        """keywords_matched が空のドキュメントの画像は蓄積されない。"""
        from mystery_agents.tools.librarian_tools import _accumulate_archive_images

        ctx = make_tool_context()
        docs_dicts = [
            {
                "title": "Relevant",
                "source_url": "https://example.com/1",
                "source_type": "loc_digital",
                "thumbnail_url": "https://example.com/thumb1.jpg",
                "keywords_matched": ["key1"],
            },
            {
                "title": "Irrelevant",
                "source_url": "https://example.com/2",
                "source_type": "europeana",
                "thumbnail_url": "https://example.com/thumb2.jpg",
                "keywords_matched": [],
            },
        ]
        _accumulate_archive_images(ctx, docs_dicts)
        images = ctx.state.get("archive_images", [])
        assert len(images) == 1
        assert images[0]["title"] == "Relevant"


# ---------------------------------------------------------------------------
# Layer 3: Scholar ツール検証 + Polymath インベントリ
# ---------------------------------------------------------------------------


class TestGroundingWarnsZeroKeywordMatch:
    """_validate_evidence_grounding のキーワード検証テスト。"""

    def test_grounding_warns_zero_keyword_match(self):
        """0一致 evidence に警告が生成される。"""
        from mystery_agents.tools.scholar_tools import _validate_evidence_grounding

        ctx = make_tool_context(state={
            "raw_search_results": [
                {
                    "documents": [
                        {
                            "source_url": "https://example.com/1",
                            "title": "Irrelevant French Textile",
                            "keywords_matched": [],
                        },
                    ],
                },
            ],
        })
        report_data = {
            "evidence_a": {"source_url": "https://example.com/1"},
        }
        warnings = _validate_evidence_grounding(report_data, ctx)
        assert any("キーワード無一致" in w for w in warnings)

    def test_grounding_no_warn_positive_match(self):
        """1+一致 evidence に警告なし。"""
        from mystery_agents.tools.scholar_tools import _validate_evidence_grounding

        ctx = make_tool_context(state={
            "raw_search_results": [
                {
                    "documents": [
                        {
                            "source_url": "https://example.com/1",
                            "title": "Relevant Document",
                            "keywords_matched": ["tichborne"],
                        },
                    ],
                },
            ],
        })
        report_data = {
            "evidence_a": {"source_url": "https://example.com/1"},
        }
        warnings = _validate_evidence_grounding(report_data, ctx)
        assert not any("キーワード無一致" in w for w in warnings)


class TestAdditionalEvidenceZeroMatchRemoved:
    """save_structured_report の additional_evidence ポストフィルタテスト。"""

    def test_additional_evidence_zero_match_removed(self):
        """additional_evidence の0一致項目が除外される。"""
        from mystery_agents.tools.scholar_tools import save_structured_report

        ctx = make_tool_context(state={
            "_inventory_consulted": True,
            "_word_count_verified": True,
            "raw_search_results": [
                {
                    "documents": [
                        {
                            "source_url": "https://example.com/relevant",
                            "title": "Relevant Doc",
                            "keywords_matched": ["key1"],
                        },
                        {
                            "source_url": "https://example.com/irrelevant",
                            "title": "Irrelevant Doc",
                            "keywords_matched": [],
                        },
                    ],
                },
            ],
        })
        report = {
            "classification": "HIS",
            "country_code": "GB",
            "region_code": "LHR",
            "title": "Test",
            "summary": "Test",
            "additional_evidence": [
                {
                    "source_url": "https://example.com/relevant",
                    "relevant_excerpt": "Some text",
                },
                {
                    "source_url": "https://example.com/irrelevant",
                    "relevant_excerpt": "Some text",
                },
            ],
        }
        result = json.loads(save_structured_report(json.dumps(report), ctx))
        assert result["status"] == "success"
        # structured_report が保存されていることを確認
        saved = ctx.state.get("structured_report", {})
        assert len(saved["additional_evidence"]) == 1
        assert saved["additional_evidence"][0]["source_url"] == "https://example.com/relevant"

    def test_evidence_ab_zero_match_warned_not_removed(self):
        """evidence_a/b は警告のみ、除外されない。"""
        from mystery_agents.tools.scholar_tools import save_structured_report

        ctx = make_tool_context(state={
            "_inventory_consulted": True,
            "_word_count_verified": True,
            "raw_search_results": [
                {
                    "documents": [
                        {
                            "source_url": "https://example.com/a",
                            "title": "Zero Match A",
                            "keywords_matched": [],
                        },
                    ],
                },
            ],
        })
        report = {
            "classification": "HIS",
            "country_code": "GB",
            "region_code": "LHR",
            "title": "Test",
            "summary": "Test",
            "evidence_a": {
                "source_url": "https://example.com/a",
                "relevant_excerpt": "Some text",
            },
        }
        result = json.loads(save_structured_report(json.dumps(report), ctx))
        assert result["status"] == "success"
        # evidence_a は除外されない
        saved = ctx.state.get("structured_report", {})
        assert saved["evidence_a"]["source_url"] == "https://example.com/a"
        # 警告が生成されている
        assert any("キーワード無一致" in w for w in result["warnings"])


class TestInventoryIncludesKeywordsMatched:
    """document_inventory に keywords_matched カウントが含まれるテスト。"""

    def test_inventory_includes_keywords_matched(self):
        """インベントリに keywords_matched カウントが含まれる。"""
        from mystery_agents.tools.document_inventory import get_document_inventory

        ctx = make_tool_context(state={
            "raw_search_results": [
                {
                    "documents": [
                        {
                            "source_url": "https://example.com/doc1",
                            "title": "Doc 1",
                            "source_type": "loc_digital",
                            "language": "en",
                            "keywords_matched": ["key1", "key2"],
                        },
                        {
                            "source_url": "https://example.com/doc2",
                            "title": "Doc 2",
                            "source_type": "europeana",
                            "language": "de",
                            "keywords_matched": [],
                        },
                    ],
                },
            ],
        })
        result = json.loads(get_document_inventory(ctx))
        assert result["status"] == "ok"
        # 全アーカイブの全文書で keywords_matched カウントを確認
        for archive_docs in result["by_archive"].values():
            for doc in archive_docs:
                assert "keywords_matched" in doc
                assert isinstance(doc["keywords_matched"], int)


# ---------------------------------------------------------------------------
# Layer 4: Publisher 監査ログ
# ---------------------------------------------------------------------------


class TestPublisherAuditLog:
    """Publisher 監査ログのテスト。"""

    def test_publisher_audit_logs_zero_match(self, caplog):
        """Publisher 監査ログが0一致を検出する。"""
        from mystery_agents.tools.publisher_tools import _audit_evidence_relevance

        ctx = make_tool_context(state={
            "raw_search_results": [
                {
                    "documents": [
                        {
                            "source_url": "https://example.com/bad",
                            "title": "Irrelevant French Textile",
                            "keywords_matched": [],
                        },
                    ],
                },
            ],
        })
        data = {
            "evidence_a": {"source_url": "https://example.com/bad"},
            "evidence_b": {"source_url": "https://example.com/missing"},
        }
        with caplog.at_level(logging.WARNING):
            _audit_evidence_relevance(data, ctx)
        assert any("証拠妥当性監査" in r.message for r in caplog.records)
        assert any("evidence_a" in r.message for r in caplog.records)
