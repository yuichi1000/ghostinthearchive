"""Unit tests for mystery_agents/tools/search_orchestration.py

reference_keywords_matched の算出・ランキングロジックのテスト。
"""

from mystery_agents.tools.search_orchestration import (
    _rank_documents,
    _search_single_source,
)
from tests.fakes import make_archive_doc as _make_doc

from mystery_agents.tools.archive_source_base import ArchiveSearchResult


def _make_mock_source(
    source_key="mock",
    docs=None,
    total_hits=0,
    error=None,
    supports_language_filter=False,
):
    """テスト用のモック ArchiveSource を作成する。"""

    class MockSource:
        pass

    s = MockSource()
    s.source_key = source_key
    s.source_name = f"Mock {source_key}"
    s.supports_language_filter = supports_language_filter

    def _search(**kwargs):
        return ArchiveSearchResult(
            documents=list(docs or []),
            total_hits=total_hits,
            error=error,
        )

    s.search = _search
    return s


class TestReferenceKeywordsMatched:
    """_search_single_source が reference_keywords_matched を算出すること。"""

    def test_reference_keywords_matched_from_title(self):
        """タイトルに固有名詞が含まれるドキュメントは reference_keywords_matched に含まれるべき。"""
        doc = _make_doc(title="The Watseka Wonder of 1877", url="https://example.com/1")
        source = _make_mock_source(docs=[doc], total_hits=1)

        _, docs, _, _, _ = _search_single_source(
            source,
            [["identity", "spirit"]],
            date_start=None,
            date_end=None,
            per_source_limit=10,
            language=None,
            reference_keywords=["Watseka", "Vennum"],
        )

        assert len(docs) == 1
        assert "Watseka" in docs[0].reference_keywords_matched
        # "Vennum" はタイトル/サマリーに含まれないので無し
        assert "Vennum" not in docs[0].reference_keywords_matched

    def test_no_reference_keywords_leaves_empty(self):
        """reference_keywords が空の場合、全ドキュメントの reference_keywords_matched は空のまま。"""
        doc = _make_doc(title="Some Document", url="https://example.com/2")
        source = _make_mock_source(docs=[doc], total_hits=1)

        _, docs, _, _, _ = _search_single_source(
            source,
            [["ghost"]],
            date_start=None,
            date_end=None,
            per_source_limit=10,
            language=None,
            reference_keywords=None,
        )

        assert docs[0].reference_keywords_matched == []

    def test_reference_keywords_case_insensitive(self):
        """大文字小文字を区別しないマッチング。"""
        doc = _make_doc(
            title="WATSEKA historical records",
            url="https://example.com/3",
        )
        source = _make_mock_source(docs=[doc], total_hits=1)

        _, docs, _, _, _ = _search_single_source(
            source,
            [["spirit"]],
            date_start=None,
            date_end=None,
            per_source_limit=10,
            language=None,
            reference_keywords=["watseka"],
        )

        assert "watseka" in docs[0].reference_keywords_matched

    def test_reference_keywords_matched_from_summary(self):
        """サマリーに固有名詞が含まれるドキュメントもマッチする。"""
        from mystery_agents.schemas.document import ArchiveDocument

        doc = ArchiveDocument(
            title="Spiritual Phenomena Report",
            source_url="https://example.com/4",
            summary="The case of Lurancy Vennum in Watseka, Illinois",
            language="en",
            location="Illinois",
            source_type="nypl",
            keywords_matched=["spirit"],
        )
        source = _make_mock_source(docs=[doc], total_hits=1)

        _, docs, _, _, _ = _search_single_source(
            source,
            [["spirit"]],
            date_start=None,
            date_end=None,
            per_source_limit=10,
            language=None,
            reference_keywords=["Watseka", "Vennum"],
        )

        assert "Watseka" in docs[0].reference_keywords_matched
        assert "Vennum" in docs[0].reference_keywords_matched


class TestRankDocumentsWithReference:
    """reference_keywords_matched 数で優先ソートされること。"""

    def test_reference_match_ranked_higher(self):
        """reference match ありのドキュメントが exploratory match のみより上位にランクされるべき。"""
        doc_ref = _make_doc(
            url="https://a.com/ref",
            source_type="nypl",
            keywords_matched=["spirit"],
        )
        doc_ref.reference_keywords_matched = ["Watseka"]

        doc_exp = _make_doc(
            url="https://a.com/exp",
            source_type="nypl",
            keywords_matched=["spirit", "identity", "possession"],
        )
        doc_exp.reference_keywords_matched = []

        ranked = _rank_documents([doc_exp, doc_ref])

        # reference match ありが先（keywords_matched は少ないが reference が優先）
        assert ranked[0].source_url == "https://a.com/ref"
        assert ranked[1].source_url == "https://a.com/exp"
