"""Unit tests for NYPL Digital Collections API tool."""

from unittest.mock import patch

import responses

from mystery_agents.tools.nypl_digital import (
    BASE_URL,
    NYPLSource,
)


class TestEmptyDates:
    """空文字日付のテスト。"""

    @responses.activate
    def test_empty_dates_omits_date_filter(self):
        """date_start/date_end が空文字の場合、日付範囲がクエリに付加されない。"""
        mock_response = {
            "nyplAPI": {
                "response": {
                    "numResults": "0",
                    "result": [],
                },
            },
        }
        responses.add(responses.GET, BASE_URL, json=mock_response, status=200)

        source = NYPLSource()
        with patch.dict("os.environ", {"NYPL_API_TOKEN": "test_token"}):
            result = source.search(keywords=["ghost"], date_start="", date_end="")

        request = responses.calls[0].request
        # クエリに年範囲が付加されず、キーワードのみ
        # "ghost" は含まれるが "1500-1899" のような日付範囲は含まれない
        assert "ghost" in request.url
        assert "1500" not in request.url
        assert result.error is None
