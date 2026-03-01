"""Unit tests for mystery_agents/tools/internet_archive.py fulltext retrieval."""

import responses

from mystery_agents.tools.internet_archive import (
    BASE_URL,
    InternetArchiveSource,
    _DJVU_TEXT_URL,
    _fetch_djvu_text,
)
from shared.http_retry import create_retry_session


class TestFetchDjvuText:
    """_fetch_djvu_text のテスト。"""

    @responses.activate
    def test_returns_text(self):
        """djvu.txt が取得できる場合にテキストを返す。"""
        identifier = "test_book_1893"
        url = _DJVU_TEXT_URL.format(identifier=identifier)
        responses.add(responses.GET, url, body="Full text of the book.", status=200)

        session = create_retry_session()
        result = _fetch_djvu_text(session, identifier)

        assert result == "Full text of the book."

    @responses.activate
    def test_returns_none_on_404(self):
        """djvu.txt が存在しない場合（404）は None を返す。"""
        identifier = "no_text_item"
        url = _DJVU_TEXT_URL.format(identifier=identifier)
        responses.add(responses.GET, url, status=404)

        session = create_retry_session()
        result = _fetch_djvu_text(session, identifier)

        assert result is None

    @responses.activate
    def test_returns_full_text_under_raw_limit(self):
        """安全上限以下のテキストはそのまま返す（キーワード抽出は呼び出し側で行う）。"""
        identifier = "long_book"
        url = _DJVU_TEXT_URL.format(identifier=identifier)
        responses.add(responses.GET, url, body="B" * 6000, status=200)

        session = create_retry_session()
        result = _fetch_djvu_text(session, identifier)

        assert len(result) == 6000

    @responses.activate
    def test_returns_none_on_empty_text(self):
        """空のレスポンスは None を返す。"""
        identifier = "empty_book"
        url = _DJVU_TEXT_URL.format(identifier=identifier)
        responses.add(responses.GET, url, body="   ", status=200)

        session = create_retry_session()
        result = _fetch_djvu_text(session, identifier)

        assert result is None


class TestInternetArchiveFulltextFilter:
    """Internet Archive 検索の全文フィルタリングテスト。"""

    @responses.activate
    def test_filters_docs_without_fulltext(self):
        """djvu.txt 取得に失敗したドキュメントは除外される。"""
        # 検索 API モック（2件返す）
        responses.add(
            responses.GET,
            BASE_URL,
            json={
                "response": {
                    "numFound": 2,
                    "docs": [
                        {
                            "identifier": "has_text",
                            "title": "Book With Text",
                            "description": "desc",
                            "date": "1893",
                        },
                        {
                            "identifier": "no_text",
                            "title": "Book Without Text",
                            "description": "desc",
                            "date": "1893",
                        },
                    ],
                }
            },
            status=200,
        )
        # djvu.txt: 1件目は成功、2件目は 404
        responses.add(
            responses.GET,
            _DJVU_TEXT_URL.format(identifier="has_text"),
            body="OCR text content",
            status=200,
        )
        responses.add(
            responses.GET,
            _DJVU_TEXT_URL.format(identifier="no_text"),
            status=404,
        )

        source = InternetArchiveSource()
        result = source.search(keywords=["test"], date_start="1800", date_end="1899")

        assert len(result.documents) == 1
        assert result.documents[0].title == "Book With Text"
        assert result.documents[0].raw_text == "OCR text content"

    @responses.activate
    def test_keeps_all_docs_with_fulltext(self):
        """全ドキュメントの djvu.txt 取得に成功した場合、全件保持される。"""
        responses.add(
            responses.GET,
            BASE_URL,
            json={
                "response": {
                    "numFound": 1,
                    "docs": [
                        {
                            "identifier": "good_book",
                            "title": "Good Book",
                            "description": "desc",
                            "date": "1850",
                        },
                    ],
                }
            },
            status=200,
        )
        responses.add(
            responses.GET,
            _DJVU_TEXT_URL.format(identifier="good_book"),
            body="Full text here",
            status=200,
        )

        source = InternetArchiveSource()
        result = source.search(keywords=["test"], date_start="1800", date_end="1899")

        assert len(result.documents) == 1
        assert result.documents[0].raw_text == "Full text here"
