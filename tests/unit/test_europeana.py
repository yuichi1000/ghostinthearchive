"""Unit tests for Europeana API tool."""

from unittest.mock import patch

import responses

from mystery_agents.tools.europeana import (
    BASE_URL,
    _detect_europeana_language,
    _parse_year,
    search_europeana,
)
from mystery_agents.schemas.document import SourceLanguage, SourceType


class TestSearchEuropeana:
    """Tests for search_europeana function."""

    def test_missing_api_key(self):
        """API キー未設定時はエラーを返す。"""
        with patch.dict("os.environ", {}, clear=True):
            result = search_europeana(keywords=["test"])
        assert result["error"] == "EUROPEANA_API_KEY not set"
        assert result["documents"] == []

    def test_empty_keywords(self):
        """空のキーワードリストでエラーを返す。"""
        with patch.dict("os.environ", {"EUROPEANA_API_KEY": "test_key"}):
            result = search_europeana(keywords=[])
        assert result["error"] == "No keywords provided"

    @responses.activate
    def test_successful_search(self):
        """正常なレスポンスでドキュメントを返す。"""
        mock_response = {
            "totalResults": 1,
            "items": [
                {
                    "title": ["German Colonial Record"],
                    "dcDescription": ["A historical document from 1850"],
                    "guid": "https://europeana.eu/item/123",
                    "year": ["1850"],
                    "dcLanguage": ["de"],
                }
            ],
        }
        responses.add(responses.GET, BASE_URL, json=mock_response, status=200)

        with patch.dict("os.environ", {"EUROPEANA_API_KEY": "test_key"}):
            result = search_europeana(keywords=["colonial"])

        assert result["total_hits"] == 1
        assert len(result["documents"]) == 1
        doc = result["documents"][0]
        assert doc.title == "German Colonial Record"
        assert doc.language == SourceLanguage.DE
        assert doc.source_type == SourceType.EUROPEANA

    @responses.activate
    def test_language_filter_applied(self):
        """言語フィルタがクエリパラメータに反映される。"""
        responses.add(responses.GET, BASE_URL, json={"totalResults": 0, "items": []}, status=200)

        with patch.dict("os.environ", {"EUROPEANA_API_KEY": "test_key"}):
            search_europeana(keywords=["test"], language="de")

        request = responses.calls[0].request
        assert "LANGUAGE:de" in request.url or "LANGUAGE%3Ade" in request.url

    @responses.activate
    def test_api_error_handling(self):
        """API エラー時はエラーメッセージを返す。"""
        responses.add(responses.GET, BASE_URL, json={"error": "unauthorized"}, status=401)

        with patch.dict("os.environ", {"EUROPEANA_API_KEY": "bad_key"}):
            result = search_europeana(keywords=["test"])

        assert result["error"] is not None
        assert "Europeana API error" in result["error"]
        assert result["documents"] == []


class TestDetectEuropeanaLanguage:
    """Tests for _detect_europeana_language helper."""

    def test_detect_german(self):
        assert _detect_europeana_language("de") == SourceLanguage.DE

    def test_detect_french(self):
        assert _detect_europeana_language("fr") == SourceLanguage.FR

    def test_detect_dutch(self):
        assert _detect_europeana_language("nl") == SourceLanguage.NL

    def test_detect_unknown_defaults_to_en(self):
        assert _detect_europeana_language("unknown") == SourceLanguage.EN

    def test_detect_empty_defaults_to_en(self):
        assert _detect_europeana_language("") == SourceLanguage.EN


class TestParseYear:
    """Tests for _parse_year helper."""

    def test_parse_year_from_string(self):
        assert _parse_year("1850") == "1850-01-01"

    def test_parse_empty_string(self):
        assert _parse_year("") is None

    def test_parse_full_date(self):
        assert _parse_year("1850-06-15") == "1850-01-01"
