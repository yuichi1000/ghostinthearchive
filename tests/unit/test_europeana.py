"""Unit tests for Europeana API tool."""

from unittest.mock import patch

import responses

from mystery_agents.tools.europeana import (
    BASE_URL,
    EuropeanaSource,
    _detect_language,
    _extract_location,
)
from mystery_agents.tools.archive_source_base import ArchiveSource
from mystery_agents.schemas.document import SourceLanguage


class TestSearchEuropeana:
    """Tests for EuropeanaSource.search()."""

    def test_missing_api_key(self):
        """API Key 未設定時はエラーを返す。"""
        source = EuropeanaSource()
        with patch.dict("os.environ", {}, clear=True):
            result = source.search(keywords=["test"])
        assert result.error == "EUROPEANA_API_KEY not set"
        assert result.documents == []

    def test_empty_keywords(self):
        """空のキーワードリストでエラーを返す。"""
        source = EuropeanaSource()
        with patch.dict("os.environ", {"EUROPEANA_API_KEY": "test_key"}):
            result = source.search(keywords=[])
        assert result.error == "No keywords provided"

    @responses.activate
    def test_successful_search(self):
        """正常なレスポンスでドキュメントを返す。"""
        mock_response = {
            "success": True,
            "totalResults": 1,
            "items": [
                {
                    "title": ["Medieval Manuscript from Paris"],
                    "year": ["1450"],
                    "guid": "https://www.europeana.eu/item/123/abc",
                    "dcDescription": ["A rare medieval manuscript found in Paris archives"],
                    "language": ["fr"],
                    "country": ["France"],
                }
            ],
        }
        responses.add(responses.GET, BASE_URL, json=mock_response, status=200)

        source = EuropeanaSource()
        with patch.dict("os.environ", {"EUROPEANA_API_KEY": "test_key"}):
            result = source.search(keywords=["medieval", "manuscript"])

        assert result.total_hits == 1
        assert len(result.documents) == 1
        doc = result.documents[0]
        assert doc.title == "Medieval Manuscript from Paris"
        assert doc.language == SourceLanguage.FR
        assert doc.source_type == "europeana"
        assert "europeana.eu" in doc.source_url

    @responses.activate
    def test_country_filter(self):
        """language パラメータで qf=COUNTRY:germany が送信される（LANGUAGE ではなく COUNTRY）。"""
        mock_response = {"success": True, "totalResults": 0, "items": []}
        responses.add(responses.GET, BASE_URL, json=mock_response, status=200)

        source = EuropeanaSource()
        with patch.dict("os.environ", {"EUROPEANA_API_KEY": "test_key"}):
            source.search(keywords=["test"], language="de")

        request = responses.calls[0].request
        assert "COUNTRY%3Agermany" in request.url or "COUNTRY:germany" in request.url
        # LANGUAGE フィルタは送信されないことを確認
        assert "LANGUAGE" not in request.url

    @responses.activate
    def test_country_filter_french(self):
        """フランス語 → COUNTRY:france で送信される。"""
        mock_response = {"success": True, "totalResults": 0, "items": []}
        responses.add(responses.GET, BASE_URL, json=mock_response, status=200)

        source = EuropeanaSource()
        with patch.dict("os.environ", {"EUROPEANA_API_KEY": "test_key"}):
            source.search(keywords=["test"], language="fr")

        request = responses.calls[0].request
        assert "COUNTRY%3Afrance" in request.url or "COUNTRY:france" in request.url

    @responses.activate
    def test_unmapped_language_no_country_filter(self):
        """マッピングにない言語（en 等）では COUNTRY フィルタが送信されない。"""
        mock_response = {"success": True, "totalResults": 0, "items": []}
        responses.add(responses.GET, BASE_URL, json=mock_response, status=200)

        source = EuropeanaSource()
        with patch.dict("os.environ", {"EUROPEANA_API_KEY": "test_key"}):
            source.search(keywords=["test"], language="en")

        request = responses.calls[0].request
        assert "COUNTRY" not in request.url
        assert "LANGUAGE" not in request.url

    @responses.activate
    def test_date_filter(self):
        """日付フィルタが qf パラメータで送信される。"""
        mock_response = {"success": True, "totalResults": 0, "items": []}
        responses.add(responses.GET, BASE_URL, json=mock_response, status=200)

        source = EuropeanaSource()
        with patch.dict("os.environ", {"EUROPEANA_API_KEY": "test_key"}):
            source.search(keywords=["test"], date_start="1800", date_end="1899")

        request = responses.calls[0].request
        assert "1800" in request.url
        assert "1899" in request.url

    @responses.activate
    def test_api_error_handling(self):
        """API エラー時はエラーメッセージを返す。"""
        responses.add(responses.GET, BASE_URL, json={"error": "forbidden"}, status=403)

        source = EuropeanaSource()
        with patch.dict("os.environ", {"EUROPEANA_API_KEY": "bad_key"}):
            result = source.search(keywords=["test"])

        assert result.error is not None
        assert "API error" in result.error
        assert result.documents == []

    @responses.activate
    def test_empty_results(self):
        """結果が0件の場合。"""
        mock_response = {"success": True, "totalResults": 0, "items": []}
        responses.add(responses.GET, BASE_URL, json=mock_response, status=200)

        source = EuropeanaSource()
        with patch.dict("os.environ", {"EUROPEANA_API_KEY": "test_key"}):
            result = source.search(keywords=["nonexistent"])

        assert result.total_hits == 0
        assert result.documents == []
        assert result.error is None

    @responses.activate
    def test_wskey_parameter(self):
        """wskey パラメータがリクエストに含まれることを確認。"""
        mock_response = {"success": True, "totalResults": 0, "items": []}
        responses.add(responses.GET, BASE_URL, json=mock_response, status=200)

        source = EuropeanaSource()
        with patch.dict("os.environ", {"EUROPEANA_API_KEY": "my_secret_key"}):
            source.search(keywords=["test"])

        request = responses.calls[0].request
        assert "wskey=my_secret_key" in request.url

    @responses.activate
    def test_edmIsShownAt_fallback(self):
        """guid がない場合は edmIsShownAt にフォールバックする。"""
        mock_response = {
            "success": True,
            "totalResults": 1,
            "items": [
                {
                    "title": ["Test Document"],
                    "edmIsShownAt": ["https://example.europeana.eu/item/456"],
                    "language": ["en"],
                    "country": ["United Kingdom"],
                }
            ],
        }
        responses.add(responses.GET, BASE_URL, json=mock_response, status=200)

        source = EuropeanaSource()
        with patch.dict("os.environ", {"EUROPEANA_API_KEY": "test_key"}):
            result = source.search(keywords=["test"])

        assert len(result.documents) == 1
        assert result.documents[0].source_url == "https://example.europeana.eu/item/456"


class TestDetectLanguage:
    """Tests for _detect_language helper."""

    def test_detect_french(self):
        assert _detect_language({"language": ["fr"]}) == SourceLanguage.FR

    def test_detect_german(self):
        assert _detect_language({"language": ["de"]}) == SourceLanguage.DE

    def test_default_to_english(self):
        assert _detect_language({"language": []}) == SourceLanguage.EN

    def test_unknown_language(self):
        assert _detect_language({"language": ["zz"]}) == SourceLanguage.EN

    def test_string_language(self):
        assert _detect_language({"language": "nl"}) == SourceLanguage.NL


class TestExtractLocation:
    """Tests for _extract_location helper."""

    def test_from_country(self):
        assert _extract_location({"country": ["France"]}) == "France"

    def test_from_place_label(self):
        result = _extract_location({"edmPlaceLabelLangAware": {"en": ["Paris"]}})
        assert result == "Paris"

    def test_default_europe(self):
        assert _extract_location({}) == "Europe"


class TestEmptyDates:
    """空文字日付のテスト。"""

    @responses.activate
    def test_empty_dates_omits_date_filter(self):
        """date_start/date_end が空文字の場合、YEAR フィルタが省略される。"""
        mock_response = {"success": True, "totalResults": 0, "items": []}
        responses.add(responses.GET, BASE_URL, json=mock_response, status=200)

        source = EuropeanaSource()
        with patch.dict("os.environ", {"EUROPEANA_API_KEY": "test_key"}):
            source.search(keywords=["test"], date_start="", date_end="")

        request = responses.calls[0].request
        # YEAR フィルタが URL に含まれないことを確認
        assert "YEAR" not in request.url


class TestParseYear:
    """Tests for ArchiveSource.parse_year() (旧 _parse_year)。"""

    def test_parse_year(self):
        assert ArchiveSource.parse_year("1850") == "1850-01-01"

    def test_parse_empty(self):
        assert ArchiveSource.parse_year("") is None

    def test_parse_full_date(self):
        assert ArchiveSource.parse_year("1850-03-15") == "1850-01-01"
