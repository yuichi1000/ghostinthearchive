"""Unit tests for Internet Archive API tool."""

import responses

from mystery_agents.tools.internet_archive import (
    BASE_URL,
    InternetArchiveSource,
)


class TestEmptyDates:
    """空文字日付のテスト。"""

    @responses.activate
    def test_empty_dates_omits_date_filter(self):
        """date_start/date_end が空文字の場合、date:[] 句がクエリに含まれない。"""
        mock_response = {
            "response": {
                "numFound": 0,
                "docs": [],
            },
        }
        responses.add(responses.GET, BASE_URL, json=mock_response, status=200)

        source = InternetArchiveSource()
        result = source.search(keywords=["ghost"], date_start="", date_end="")

        request = responses.calls[0].request
        # date:[ フィルタが含まれないことを確認
        assert "date%3A%5B" not in request.url and "date:[" not in request.url
        assert result.error is None
