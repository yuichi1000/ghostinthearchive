"""Unit tests for mystery_agents/tools/librarian_tools.py"""

import json
from unittest.mock import patch

from mystery_agents.schemas.document import ArchiveDocument, SourceLanguage, SourceType


def _make_doc(url="https://www.loc.gov/item/test/", title="Test Doc"):
    return ArchiveDocument(
        title=title,
        source_url=url,
        summary="A test document",
        language=SourceLanguage.EN,
        location="Test",
        source_type=SourceType.LOC_DIGITAL,
    )


class TestSearchNewspapersValidationFallback:
    """search_newspapers の validate_documents 例外時フォールバック"""

    @patch("mystery_agents.tools.librarian_tools.validate_documents")
    @patch("mystery_agents.tools.librarian_tools.search_chronicling_america")
    def test_validate_documents_exception_preserves_all_docs(
        self, mock_search, mock_validate
    ):
        """validate_documents が例外を投げても全ドキュメントが保持される。"""
        doc = _make_doc()
        mock_search.return_value = {
            "total_hits": 1,
            "documents": [doc],
            "error": None,
        }
        mock_validate.side_effect = RuntimeError("unexpected error in validation")

        from mystery_agents.tools.librarian_tools import search_newspapers

        result_json = search_newspapers(keywords="test keyword")
        result = json.loads(result_json)

        assert result["documents_returned"] == 1
        assert result["documents"][0]["title"] == "Test Doc"
        # リンク検証はスキップされる
        assert result["link_validation"]["total_checked"] == 0


class TestSearchArchivesValidationFallback:
    """search_archives の validate_documents 例外時フォールバック"""

    @patch("mystery_agents.tools.librarian_tools.validate_documents")
    def test_validate_documents_exception_preserves_all_docs(
        self, mock_validate
    ):
        """validate_documents が例外を投げても全ドキュメントが保持される。"""
        doc = _make_doc()

        def fake_search_fn(**kwargs):
            return {
                "total_hits": 1,
                "documents": [doc],
                "error": None,
            }

        mock_validate.side_effect = RuntimeError("unexpected error in validation")

        from mystery_agents.tools.librarian_tools import _ARCHIVE_SOURCES, search_archives

        original = _ARCHIVE_SOURCES["loc"]
        _ARCHIVE_SOURCES["loc"] = ("LOC Digital Collections", fake_search_fn)
        try:
            result_json = search_archives(keywords="test keyword", sources="loc")
        finally:
            _ARCHIVE_SOURCES["loc"] = original

        result = json.loads(result_json)

        assert result["total_documents"] == 1
        assert result["documents"][0]["title"] == "Test Doc"
        # リンク検証はスキップされる
        assert result["link_validation"]["total_checked"] == 0


class TestSearchAndCollectFallback:
    """_search_and_collect 内部関数の例外時フォールバック"""

    @patch("mystery_agents.tools.librarian_tools.validate_documents")
    @patch("mystery_agents.tools.librarian_tools.search_chronicling_america")
    def test_search_exception_captured_as_error(
        self, mock_search, mock_validate
    ):
        """search_chronicling_america が例外を投げるとエラーメッセージが記録される。"""
        mock_search.side_effect = ConnectionError("API unreachable")
        # validate_documents は呼ばれないはずだが念のためモック
        mock_validate.return_value = type("Summary", (), {
            "total_checked": 0, "reachable": 0, "unreachable": 0,
            "removed_urls": [], "duration_ms": 0, "verified_documents": [],
        })()

        from mystery_agents.tools.librarian_tools import search_newspapers

        result_json = search_newspapers(keywords="test keyword")
        result = json.loads(result_json)

        assert result["error"] == "API unreachable"
        assert result["documents_returned"] == 0
