"""Unit tests for LOC Digital Collections API tool."""

from unittest.mock import patch

import responses

from mystery_agents.tools.loc_digital import (
    BASE_URL,
    LOCDigitalSource,
)


class TestEmptyDates:
    """空文字日付のテスト。"""

    @responses.activate
    def test_empty_dates_omits_date_filter(self):
        """date_start/date_end が空文字の場合、dates パラメータが省略される。"""
        mock_response = {
            "results": [],
            "pagination": {"total": 0},
        }
        responses.add(responses.GET, BASE_URL, json=mock_response, status=200)

        source = LOCDigitalSource()
        result = source.search(keywords=["test"], date_start="", date_end="")

        request = responses.calls[0].request
        # dates パラメータが URL に含まれないことを確認
        assert "dates=" not in request.url
        assert result.error is None
