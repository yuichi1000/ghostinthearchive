"""Unit tests for NYPL Digital Collections API tool."""

import os

import pytest
import responses

# テスト用ダミートークン
_TEST_TOKEN = "test_nypl_token_12345"


@pytest.fixture(autouse=True)
def _set_nypl_token(monkeypatch):
    """全テストで NYPL_API_TOKEN を設定する。"""
    monkeypatch.setenv("NYPL_API_TOKEN", _TEST_TOKEN)

from mystery_agents.tools.nypl_digital import (
    BASE_URL,
    NYPLSource,
    _PLAIN_TEXT_URL,
    _fetch_plain_text,
)

# モック検索レスポンス
_MOCK_SEARCH_RESPONSE = {
    "nyplAPI": {
        "response": {
            "numResults": 2,
            "result": [
                {
                    "title": "Salem Witch Trial Manuscript",
                    "uuid": "uuid-aaa-111",
                    "dateDigitized": "2015-03-15",
                },
                {
                    "title": "Colonial New York Records",
                    "uuid": "uuid-bbb-222",
                    "dateDigitized": "2018-07-01",
                },
            ],
        }
    }
}

_MOCK_EMPTY_RESPONSE = {
    "nyplAPI": {
        "response": {
            "numResults": 0,
            "result": [],
        }
    }
}


class TestNYPLSource:
    """Tests for NYPLSource."""

    def test_source_metadata(self):
        """ソースメタデータの基本確認。"""
        source = NYPLSource()
        assert source.source_key == "nypl"
        assert source.source_name == "NYPL Digital Collections"
        assert source.supported_languages == {"en"}
        assert source.is_newspaper_source is False
        assert source.env_var_key == "NYPL_API_TOKEN"

    def test_empty_keywords(self):
        """空のキーワードでエラーを返す。"""
        source = NYPLSource()
        result = source.search(keywords=[])
        assert result.error == "No keywords provided"

    @responses.activate
    def test_successful_search(self):
        """正常なレスポンスで ArchiveDocument を生成する。"""
        responses.add(responses.GET, BASE_URL, json=_MOCK_SEARCH_RESPONSE, status=200)

        source = NYPLSource()
        result = source.search(keywords=["witch", "trial"])

        assert result.error is None
        assert result.total_hits == 2
        assert len(result.documents) == 2

        doc = result.documents[0]
        assert doc.title == "Salem Witch Trial Manuscript"
        assert doc.source_type == "nypl"
        assert doc.language == "en"
        assert doc.location == "New York"
        assert "uuid-aaa-111" in doc.source_url

    @responses.activate
    def test_api_error_handling(self):
        """500 エラー時はエラーメッセージを返す。"""
        responses.add(responses.GET, BASE_URL, body="Server Error", status=500)

        source = NYPLSource()
        result = source.search(keywords=["test"])

        assert result.error is not None
        assert "API error" in result.error

    @responses.activate
    def test_empty_results(self):
        """0件レスポンス。"""
        responses.add(responses.GET, BASE_URL, json=_MOCK_EMPTY_RESPONSE, status=200)

        source = NYPLSource()
        result = source.search(keywords=["nonexistent"])

        assert result.total_hits == 0
        assert result.documents == []
        assert result.error is None


class TestFetchPlainText:
    """Tests for _fetch_plain_text."""

    @responses.activate
    def test_successful_fetch(self):
        """正常な plain_text レスポンスからテキストを取得する。"""
        url = _PLAIN_TEXT_URL.format(uuid="uuid-aaa-111")
        mock_data = {
            "nyplAPI": {
                "response": {
                    "text": "Full OCR text of the Salem witch trial document."
                }
            }
        }
        responses.add(responses.GET, url, json=mock_data, status=200)

        from shared.http_retry import create_retry_session

        session = create_retry_session()
        text = _fetch_plain_text(session, "uuid-aaa-111")

        assert text is not None
        assert "Salem witch trial" in text

    @responses.activate
    def test_404_returns_none(self):
        """404 は None を返す。"""
        url = _PLAIN_TEXT_URL.format(uuid="uuid-missing")
        responses.add(responses.GET, url, body="Not Found", status=404)

        from shared.http_retry import create_retry_session

        session = create_retry_session()
        assert _fetch_plain_text(session, "uuid-missing") is None

    @responses.activate
    def test_403_returns_none(self):
        """403 は None を返す。"""
        url = _PLAIN_TEXT_URL.format(uuid="uuid-forbidden")
        responses.add(responses.GET, url, body="Forbidden", status=403)

        from shared.http_retry import create_retry_session

        session = create_retry_session()
        assert _fetch_plain_text(session, "uuid-forbidden") is None

    @responses.activate
    def test_timeout_returns_none(self):
        """タイムアウトは None を返す。"""
        import requests as req

        url = _PLAIN_TEXT_URL.format(uuid="uuid-timeout")
        responses.add(responses.GET, url, body=req.exceptions.Timeout("timeout"))

        from shared.http_retry import create_retry_session

        session = create_retry_session()
        assert _fetch_plain_text(session, "uuid-timeout") is None

    @responses.activate
    def test_truncated_at_5000(self):
        """テキストが5000文字で切り詰められる。"""
        url = _PLAIN_TEXT_URL.format(uuid="uuid-long")
        long_text = "A" * 6000
        mock_data = {"nyplAPI": {"response": {"text": long_text}}}
        responses.add(responses.GET, url, json=mock_data, status=200)

        from shared.http_retry import create_retry_session

        session = create_retry_session()
        text = _fetch_plain_text(session, "uuid-long")

        assert text is not None
        assert len(text) == 5000


class TestNYPLFulltextEnrichment:
    """検索 + 全文エンリッチメント統合テスト。"""

    @responses.activate
    def test_search_with_fulltext_enrichment(self):
        """UUID ありの結果に全文テキストが付与される。"""
        # 検索 API
        responses.add(responses.GET, BASE_URL, json=_MOCK_SEARCH_RESPONSE, status=200)

        # plain_text API（2件）
        for uuid in ["uuid-aaa-111", "uuid-bbb-222"]:
            url = _PLAIN_TEXT_URL.format(uuid=uuid)
            mock_data = {
                "nyplAPI": {"response": {"text": f"Full text for {uuid}"}}
            }
            responses.add(responses.GET, url, json=mock_data, status=200)

        source = NYPLSource()
        result = source.search(keywords=["witch"])

        assert len(result.documents) == 2
        assert result.documents[0].raw_text == "Full text for uuid-aaa-111"
        assert result.documents[1].raw_text == "Full text for uuid-bbb-222"

    @responses.activate
    def test_fulltext_failure_preserves_document(self):
        """全文取得失敗でもドキュメントは保持される（raw_text=None）。"""
        responses.add(responses.GET, BASE_URL, json=_MOCK_SEARCH_RESPONSE, status=200)

        # 全 plain_text リクエストが 500
        for uuid in ["uuid-aaa-111", "uuid-bbb-222"]:
            url = _PLAIN_TEXT_URL.format(uuid=uuid)
            responses.add(responses.GET, url, body="Error", status=500)

        source = NYPLSource()
        result = source.search(keywords=["witch"])

        assert len(result.documents) == 2
        assert result.documents[0].raw_text is None
        assert result.documents[1].raw_text is None
