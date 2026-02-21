"""Unit tests for Trove API tool."""

from unittest.mock import patch

import responses

from mystery_agents.tools.trove import BASE_URL, TroveSource


class TestSearchTrove:
    """Tests for TroveSource.search()."""

    def test_missing_api_key(self):
        """TROVE_API_KEY 未設定時はエラーを返す。"""
        source = TroveSource()
        with patch.dict("os.environ", {}, clear=True):
            result = source.search(keywords=["test"])
        assert result.error == "TROVE_API_KEY not set"
        assert result.documents == []

    def test_empty_keywords(self):
        """空のキーワードリストでエラーを返す。"""
        source = TroveSource()
        with patch.dict("os.environ", {"TROVE_API_KEY": "test_key"}):
            result = source.search(keywords=[])
        assert result.error == "No keywords provided"

    @responses.activate
    def test_successful_search(self):
        """正常なレスポンスでドキュメントを返す。"""
        mock_response = {
            "category": [
                {
                    "code": "newspaper",
                    "records": {
                        "total": 1,
                        "article": [
                            {
                                "heading": "Convict Ship Wrecked off Coast",
                                "date": "1852-03-15",
                                "troveUrl": "https://trove.nla.gov.au/newspaper/article/123",
                                "snippet": "A convict transport ship was wrecked...",
                                "title": {"value": "The Sydney Morning Herald"},
                            }
                        ],
                    },
                }
            ]
        }
        responses.add(responses.GET, BASE_URL, json=mock_response, status=200)

        source = TroveSource()
        with patch.dict("os.environ", {"TROVE_API_KEY": "test_key"}):
            result = source.search(keywords=["convict", "shipwreck"])

        assert result.total_hits == 1
        assert len(result.documents) == 1
        doc = result.documents[0]
        assert doc.title == "Convict Ship Wrecked off Coast"
        assert doc.source_type == "trove"
        assert "trove.nla.gov.au" in doc.source_url

    @responses.activate
    def test_newspaper_article_with_ocr(self):
        """articleText 付きレスポンスで raw_text を抽出する。"""
        mock_response = {
            "category": [
                {
                    "code": "newspaper",
                    "records": {
                        "total": 1,
                        "article": [
                            {
                                "heading": "Ghost Sighting in Melbourne",
                                "date": "1880",
                                "troveUrl": "https://trove.nla.gov.au/newspaper/article/456",
                                "articleText": "Full OCR text of the ghost sighting article...",
                                "title": {"value": "The Age"},
                            }
                        ],
                    },
                }
            ]
        }
        responses.add(responses.GET, BASE_URL, json=mock_response, status=200)

        source = TroveSource()
        with patch.dict("os.environ", {"TROVE_API_KEY": "test_key"}):
            result = source.search(keywords=["ghost"])

        assert len(result.documents) == 1
        doc = result.documents[0]
        assert doc.raw_text == "Full OCR text of the ghost sighting article..."
        assert doc.location == "The Age"

    @responses.activate
    def test_date_filter(self):
        """同一 decade の場合、l-decade フィルタがリクエストに含まれる。"""
        mock_response = {"category": [{"code": "newspaper", "records": {"total": 0, "article": []}}]}
        responses.add(responses.GET, BASE_URL, json=mock_response, status=200)

        source = TroveSource()
        with patch.dict("os.environ", {"TROVE_API_KEY": "test_key"}):
            source.search(keywords=["test"], date_start="1850", date_end="1859")

        request = responses.calls[0].request
        assert "l-decade=1850" in request.url

    @responses.activate
    def test_api_error_handling(self):
        """API エラー時はエラーメッセージを返す。"""
        responses.add(responses.GET, BASE_URL, json={"error": "forbidden"}, status=403)

        source = TroveSource()
        with patch.dict("os.environ", {"TROVE_API_KEY": "bad_key"}):
            result = source.search(keywords=["test"])

        assert result.error is not None
        assert "API error" in result.error
        assert result.documents == []

    @responses.activate
    def test_empty_results(self):
        """結果が0件の場合。"""
        mock_response = {"category": [{"code": "newspaper", "records": {"total": 0, "article": []}}]}
        responses.add(responses.GET, BASE_URL, json=mock_response, status=200)

        source = TroveSource()
        with patch.dict("os.environ", {"TROVE_API_KEY": "test_key"}):
            result = source.search(keywords=["nonexistent"])

        assert result.total_hits == 0
        assert result.documents == []
        assert result.error is None

    @responses.activate
    def test_api_key_parameter(self):
        """key パラメータがリクエストに含まれることを確認。"""
        mock_response = {"category": [{"code": "newspaper", "records": {"total": 0, "article": []}}]}
        responses.add(responses.GET, BASE_URL, json=mock_response, status=200)

        source = TroveSource()
        with patch.dict("os.environ", {"TROVE_API_KEY": "my_secret_key"}):
            source.search(keywords=["test"])

        request = responses.calls[0].request
        assert "key=my_secret_key" in request.url
