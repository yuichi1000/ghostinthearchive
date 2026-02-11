"""Unit tests for DDB API tool."""

from unittest.mock import patch

import responses

from mystery_agents.tools.ddb import (
    BASE_URL,
    _parse_year,
    search_ddb,
)
from mystery_agents.schemas.document import SourceLanguage, SourceType


class TestSearchDDB:
    """Tests for search_ddb function."""

    def test_missing_api_key(self):
        """API キー未設定時はエラーを返す。"""
        with patch.dict("os.environ", {}, clear=True):
            result = search_ddb(keywords=["test"])
        assert result["error"] == "DDB_API_KEY not set"
        assert result["documents"] == []

    def test_empty_keywords(self):
        """空のキーワードリストでエラーを返す。"""
        with patch.dict("os.environ", {"DDB_API_KEY": "test_key"}):
            result = search_ddb(keywords=[])
        assert result["error"] == "No keywords provided"

    @responses.activate
    def test_successful_search(self):
        """正常なレスポンスでドキュメントを返す。"""
        mock_response = {
            "numberOfResults": 1,
            "results": [
                {
                    "id": "abc123",
                    "title": "Deutsches Kolonialarchiv",
                    "subtitle": "Ein historisches Dokument",
                    "date": "1850",
                    "place": ["Berlin"],
                }
            ],
        }
        responses.add(responses.GET, BASE_URL, json=mock_response, status=200)

        with patch.dict("os.environ", {"DDB_API_KEY": "test_key"}):
            result = search_ddb(keywords=["Kolonial"])

        assert result["total_hits"] == 1
        assert len(result["documents"]) == 1
        doc = result["documents"][0]
        assert doc.title == "Deutsches Kolonialarchiv"
        assert doc.language == SourceLanguage.DE
        assert doc.source_type == SourceType.DDB
        assert "abc123" in doc.source_url

    @responses.activate
    def test_oauth_header_sent(self):
        """OAuth 認証ヘッダーが送信される。"""
        responses.add(responses.GET, BASE_URL, json={"numberOfResults": 0, "results": []}, status=200)

        with patch.dict("os.environ", {"DDB_API_KEY": "my_secret_key"}):
            search_ddb(keywords=["test"])

        request = responses.calls[0].request
        assert "OAuth" in request.headers.get("Authorization", "")
        assert "my_secret_key" in request.headers.get("Authorization", "")

    @responses.activate
    def test_api_error_handling(self):
        """API エラー時はエラーメッセージを返す。"""
        responses.add(responses.GET, BASE_URL, json={"error": "forbidden"}, status=403)

        with patch.dict("os.environ", {"DDB_API_KEY": "bad_key"}):
            result = search_ddb(keywords=["test"])

        assert result["error"] is not None
        assert "DDB API error" in result["error"]
        assert result["documents"] == []

    @responses.activate
    def test_empty_results(self):
        """結果が0件の場合。"""
        responses.add(responses.GET, BASE_URL, json={"numberOfResults": 0, "results": []}, status=200)

        with patch.dict("os.environ", {"DDB_API_KEY": "test_key"}):
            result = search_ddb(keywords=["nonexistent"])

        assert result["total_hits"] == 0
        assert result["documents"] == []
        assert result["error"] is None


class TestParseYear:
    """Tests for _parse_year helper."""

    def test_parse_year(self):
        assert _parse_year("1850") == "1850-01-01"

    def test_parse_empty(self):
        assert _parse_year("") is None

    def test_parse_full_date(self):
        assert _parse_year("1850-03-15") == "1850-01-01"
