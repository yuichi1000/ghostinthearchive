"""Unit tests for mystery_agents/tools/chronicling_america.py fulltext retrieval."""

import responses

from mystery_agents.tools.chronicling_america import (
    _fetch_item_fulltext,
    _fetch_page_fulltext,
)
from shared.http_retry import create_retry_session


class TestFetchPageFulltext:
    """_fetch_page_fulltext のテスト。"""

    @responses.activate
    def test_returns_fulltext(self):
        """full_text フィールドがある場合にテキストを返す。"""
        page_url = "https://www.loc.gov/resource/sn83030214/1893-01-15/ed-1/?sp=1"
        responses.add(
            responses.GET,
            "https://www.loc.gov/resource/sn83030214/1893-01-15/ed-1/?sp=1&fo=json",
            json={"full_text": "The quick brown fox jumped over the lazy dog."},
            status=200,
        )

        session = create_retry_session()
        result = _fetch_page_fulltext(session, page_url)

        assert result == "The quick brown fox jumped over the lazy dog."

    @responses.activate
    def test_returns_none_on_404(self):
        """404 の場合は None を返す。"""
        page_url = "https://www.loc.gov/resource/missing"
        responses.add(
            responses.GET,
            "https://www.loc.gov/resource/missing?fo=json",
            status=404,
        )

        session = create_retry_session()
        result = _fetch_page_fulltext(session, page_url)

        assert result is None

    @responses.activate
    def test_returns_none_on_empty_fulltext(self):
        """full_text が空の場合は None を返す。"""
        page_url = "https://www.loc.gov/resource/test"
        responses.add(
            responses.GET,
            "https://www.loc.gov/resource/test?fo=json",
            json={"full_text": ""},
            status=200,
        )

        session = create_retry_session()
        result = _fetch_page_fulltext(session, page_url)

        assert result is None

    @responses.activate
    def test_truncates_long_text(self):
        """5000文字を超えるテキストは切り詰める。"""
        page_url = "https://www.loc.gov/resource/test"
        long_text = "A" * 6000
        responses.add(
            responses.GET,
            "https://www.loc.gov/resource/test?fo=json",
            json={"full_text": long_text},
            status=200,
        )

        session = create_retry_session()
        result = _fetch_page_fulltext(session, page_url)

        assert len(result) == 5000


class TestFetchItemFulltext:
    """_fetch_item_fulltext のテスト。"""

    @responses.activate
    def test_direct_fulltext(self):
        """アイテム JSON に直接 full_text がある場合。"""
        item_url = "https://www.loc.gov/item/sn83030214/"
        responses.add(
            responses.GET,
            "https://www.loc.gov/item/sn83030214/?fo=json",
            json={"full_text": "Direct OCR text from item."},
            status=200,
        )

        session = create_retry_session()
        result = _fetch_item_fulltext(session, item_url)

        assert result == "Direct OCR text from item."

    @responses.activate
    def test_fallback_to_resource_page(self):
        """full_text がなく resources からページを辿る場合。"""
        item_url = "https://www.loc.gov/item/sn83030214/"
        responses.add(
            responses.GET,
            "https://www.loc.gov/item/sn83030214/?fo=json",
            json={
                "resources": [
                    {"url": "https://www.loc.gov/resource/sn83030214/page1"}
                ]
            },
            status=200,
        )
        responses.add(
            responses.GET,
            "https://www.loc.gov/resource/sn83030214/page1?fo=json",
            json={"full_text": "Page OCR text from resource."},
            status=200,
        )

        session = create_retry_session()
        result = _fetch_item_fulltext(session, item_url)

        assert result == "Page OCR text from resource."

    @responses.activate
    def test_returns_none_on_404(self):
        """アイテム URL が 404 の場合は None を返す。"""
        item_url = "https://www.loc.gov/item/missing/"
        responses.add(
            responses.GET,
            "https://www.loc.gov/item/missing/?fo=json",
            status=404,
        )

        session = create_retry_session()
        result = _fetch_item_fulltext(session, item_url)

        assert result is None

    @responses.activate
    def test_returns_none_when_no_fulltext_or_resources(self):
        """full_text も resources もない場合は None を返す。"""
        item_url = "https://www.loc.gov/item/empty/"
        responses.add(
            responses.GET,
            "https://www.loc.gov/item/empty/?fo=json",
            json={"title": "Some item without text"},
            status=200,
        )

        session = create_retry_session()
        result = _fetch_item_fulltext(session, item_url)

        assert result is None

    @responses.activate
    def test_handles_url_with_query_params(self):
        """既にクエリパラメータを含む URL を正しく処理する。"""
        item_url = "https://www.loc.gov/resource/sn83030214/1893-01-15/ed-1/?sp=1"
        responses.add(
            responses.GET,
            "https://www.loc.gov/resource/sn83030214/1893-01-15/ed-1/?sp=1&fo=json",
            json={"full_text": "Text with query params."},
            status=200,
        )

        session = create_retry_session()
        result = _fetch_item_fulltext(session, item_url)

        assert result == "Text with query params."
