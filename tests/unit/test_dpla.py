"""Unit tests for DPLA API tool."""

from unittest.mock import patch

import responses

from mystery_agents.tools.dpla import (
    BASE_URL,
    DPLASource,
)


class TestEmptyDates:
    """空文字日付のテスト。"""

    @responses.activate
    def test_empty_dates_omits_date_filter(self):
        """date_start/date_end が空文字の場合、date パラメータが省略される。"""
        mock_response = {
            "count": 0,
            "docs": [],
        }
        responses.add(responses.GET, BASE_URL, json=mock_response, status=200)

        source = DPLASource()
        with patch.dict("os.environ", {"DPLA_API_KEY": "test_key"}):
            result = source.search(keywords=["test"], date_start="", date_end="")

        request = responses.calls[0].request
        # date.after / date.before パラメータが URL に含まれないことを確認
        assert "date.after" not in request.url
        assert "date.before" not in request.url
        assert result.error is None
