"""Unit tests for mystery_agents/tools/archive_source_base.py"""

import time
from unittest.mock import patch

import pytest
import responses

from mystery_agents.tools.archive_source_base import ArchiveSearchResult, ArchiveSource
from mystery_agents.schemas.document import ArchiveDocument, SourceLanguage


class ConcreteSource(ArchiveSource):
    """テスト用の具象ソース。"""

    source_key = "test"
    source_name = "Test Source"
    source_type = "test"
    min_request_delay = 0.0  # テストではレートリミット無効
    supported_languages = {"en", "de"}
    env_var_key = None

    def _search_impl(self, keywords, date_start, date_end, max_results, language):
        doc = ArchiveDocument(
            title="Test Doc",
            source_url="https://example.com/1",
            summary="A test",
            language=SourceLanguage.EN,
            location="Test",
            source_type=self.source_type,
        )
        return ArchiveSearchResult(documents=[doc], total_hits=1)


class FailingSource(ArchiveSource):
    """例外を投げるテスト用ソース。"""

    source_key = "failing"
    source_name = "Failing Source"
    source_type = "failing"
    min_request_delay = 0.0
    env_var_key = None

    def _search_impl(self, keywords, date_start, date_end, max_results, language):
        raise ConnectionError("API unreachable")


class ApiKeySource(ArchiveSource):
    """API キーが必要なテスト用ソース。"""

    source_key = "apikey"
    source_name = "API Key Source"
    source_type = "apikey"
    min_request_delay = 0.0
    env_var_key = "TEST_API_KEY"

    def _search_impl(self, keywords, date_start, date_end, max_results, language):
        return ArchiveSearchResult(documents=[], total_hits=0)


class TestArchiveSourceSearch:
    """ArchiveSource.search() の共通ラッパーテスト。"""

    def test_successful_search(self):
        """正常な検索が ArchiveSearchResult を返す。"""
        source = ConcreteSource()
        result = source.search(keywords=["test"], date_start="1800", date_end="1899")

        assert len(result.documents) == 1
        assert result.documents[0].title == "Test Doc"
        assert result.total_hits == 1
        assert result.error is None

    def test_empty_keywords_returns_error(self):
        """空のキーワードリストはエラーを返す。"""
        source = ConcreteSource()
        result = source.search(keywords=[], date_start="1800", date_end="1899")

        assert len(result.documents) == 0
        assert result.error == "No keywords provided"

    def test_exception_caught_and_returned(self):
        """_search_impl の例外がキャッチされエラーとして返される。"""
        source = FailingSource()
        result = source.search(keywords=["test"])

        assert len(result.documents) == 0
        assert "API unreachable" in result.error

    def test_api_key_missing_returns_error(self):
        """API キーが未設定の場合エラーを返す。"""
        source = ApiKeySource()
        with patch.dict("os.environ", {}, clear=True):
            result = source.search(keywords=["test"])

        assert result.error == "TEST_API_KEY not set"
        assert len(result.documents) == 0

    def test_api_key_present_proceeds(self):
        """API キーが設定されていれば検索が進む。"""
        source = ApiKeySource()
        with patch.dict("os.environ", {"TEST_API_KEY": "dummy"}):
            result = source.search(keywords=["test"])

        assert result.error is None

    def test_no_api_key_required(self):
        """env_var_key = None のソースは API キーチェックをスキップする。"""
        source = ConcreteSource()
        assert source.env_var_key is None
        result = source.search(keywords=["test"])

        assert result.error is None


class TestParseYear:
    """ArchiveSource.parse_year() のテスト。"""

    def test_iso_date(self):
        assert ArchiveSource.parse_year("1850-03-15") == "1850-01-01"

    def test_year_only(self):
        assert ArchiveSource.parse_year("1776") == "1776-01-01"

    def test_embedded_year(self):
        assert ArchiveSource.parse_year("Circa 1888 AD") == "1888-01-01"

    def test_empty_string(self):
        assert ArchiveSource.parse_year("") is None

    def test_long_string_fallback(self):
        long_date = "Some unknown date format that is very long"
        result = ArchiveSource.parse_year(long_date)
        assert result == long_date[:10]

    def test_twentieth_century(self):
        assert ArchiveSource.parse_year("2024") == "2024-01-01"

    def test_min_century_parameter(self):
        # min_century=15 なら 1300 年代はマッチしない
        assert ArchiveSource.parse_year("1350", min_century=15) == "1350"


class TestRateLimit:
    """レートリミッターのテスト。"""

    def test_rate_limit_delays_requests(self):
        """連続呼び出しで最小遅延が適用される。"""
        source = ConcreteSource()
        source.min_request_delay = 0.1  # 100ms

        source._rate_limit()
        start = time.monotonic()
        source._rate_limit()
        elapsed = time.monotonic() - start

        # 少なくとも遅延の一部が適用されている
        assert elapsed >= 0.05  # 50ms 以上（マージン込み）

    def test_no_delay_when_enough_time_passed(self):
        """十分な時間が経過していれば遅延なし。"""
        source = ConcreteSource()
        source.min_request_delay = 0.01
        source._last_request_time = time.time() - 1.0  # 1秒前

        start = time.monotonic()
        source._rate_limit()
        elapsed = time.monotonic() - start

        assert elapsed < 0.05  # 実質遅延なし


# === 空日付テスト（旧 test_dpla / test_loc_digital / test_internet_archive / test_nypl_digital） ===


from mystery_agents.tools.dpla import BASE_URL as DPLA_BASE_URL, DPLASource
from mystery_agents.tools.internet_archive import (
    BASE_URL as IA_BASE_URL,
    InternetArchiveSource,
)
from mystery_agents.tools.loc_digital import (
    BASE_URL as LOC_BASE_URL,
    LOCDigitalSource,
)
from mystery_agents.tools.nypl_digital import (
    BASE_URL as NYPL_BASE_URL,
    NYPLSource,
)


class TestEmptyDatesPerSource:
    """date_start/date_end が空文字の場合、日付パラメータが省略されるテスト。"""

    @responses.activate
    @pytest.mark.parametrize(
        "source_cls,base_url,mock_response,env_vars,date_check,keywords",
        [
            (
                DPLASource,
                DPLA_BASE_URL,
                {"count": 0, "docs": []},
                {"DPLA_API_KEY": "test_key"},
                lambda url: "date.after" not in url and "date.before" not in url,
                ["test"],
            ),
            (
                LOCDigitalSource,
                LOC_BASE_URL,
                {"results": [], "pagination": {"total": 0}},
                {},
                lambda url: "dates=" not in url,
                ["test"],
            ),
            (
                InternetArchiveSource,
                IA_BASE_URL,
                {"response": {"numFound": 0, "docs": []}},
                {},
                lambda url: "date%3A%5B" not in url and "date:[" not in url,
                ["ghost"],
            ),
            (
                NYPLSource,
                NYPL_BASE_URL,
                {"nyplAPI": {"response": {"numResults": "0", "result": []}}},
                {"NYPL_API_TOKEN": "test_token"},
                lambda url: "1500" not in url,
                ["ghost"],
            ),
        ],
        ids=["dpla", "loc_digital", "internet_archive", "nypl_digital"],
    )
    def test_empty_dates_omits_date_filter(
        self, source_cls, base_url, mock_response, env_vars, date_check, keywords
    ):
        """date_start/date_end が空文字の場合、日付パラメータが省略される。"""
        responses.add(responses.GET, base_url, json=mock_response, status=200)

        source = source_cls()
        with patch.dict("os.environ", env_vars):
            result = source.search(keywords=keywords, date_start="", date_end="")

        request = responses.calls[0].request
        assert date_check(request.url), f"日付パラメータが URL に含まれている: {request.url}"
        assert result.error is None
