"""Unit tests for NDL Search API tool."""

import responses

from mystery_agents.tools.ndl_search import (
    BASE_URL,
    NDLSearchSource,
    _NDL_LAB_URL,
    _extract_pid,
    _fetch_fulltext,
    _strip_html,
)


# NDL OpenSearch API の RSS 2.0 レスポンス（テスト用）
_SAMPLE_RSS = """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0"
  xmlns:dc="http://purl.org/dc/elements/1.1/"
  xmlns:dcndl="http://ndl.go.jp/dcndl/terms/"
  xmlns:openSearch="http://a9.com/-/spec/opensearchrss/1.0/"
  xmlns:rdfs="http://www.w3.org/2000/01/rdf-schema#"
  xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#">
  <channel>
    <openSearch:totalResults>1943</openSearch:totalResults>
    <item>
      <title>怪談牡丹燈籠</title>
      <link>https://ndlsearch.ndl.go.jp/books/R100000002-I000000012345</link>
      <rdfs:seeAlso rdf:resource="https://dl.ndl.go.jp/pid/12345" />
      <dc:date>1898-06</dc:date>
      <dc:description>三遊亭圓朝の落語怪談。&lt;br /&gt;牡丹の燈籠。</dc:description>
      <dcndl:publicationPlace>東京</dcndl:publicationPlace>
    </item>
  </channel>
</rss>"""

_EMPTY_RSS = """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0"
  xmlns:openSearch="http://a9.com/-/spec/opensearchrss/1.0/">
  <channel>
    <openSearch:totalResults>0</openSearch:totalResults>
  </channel>
</rss>"""

_MULTI_ITEM_RSS = """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0"
  xmlns:dc="http://purl.org/dc/elements/1.1/"
  xmlns:dcndl="http://ndl.go.jp/dcndl/terms/"
  xmlns:openSearch="http://a9.com/-/spec/opensearchrss/1.0/"
  xmlns:rdfs="http://www.w3.org/2000/01/rdf-schema#"
  xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#">
  <channel>
    <openSearch:totalResults>2</openSearch:totalResults>
    <item>
      <title>怪談集 第一巻</title>
      <link>https://ndlsearch.ndl.go.jp/books/R100000002-I000000011111</link>
      <rdfs:seeAlso rdf:resource="https://dl.ndl.go.jp/pid/11111" />
      <dc:date>1890</dc:date>
      <dc:description>怪談を集めた書物。</dc:description>
      <dcndl:publicationPlace>京都</dcndl:publicationPlace>
    </item>
    <item>
      <title>妖怪百物語</title>
      <link>https://ndlsearch.ndl.go.jp/books/R100000002-I000000022222</link>
      <dc:date>1905</dc:date>
      <dc:description>百物語形式の妖怪譚集。</dc:description>
    </item>
  </channel>
</rss>"""


class TestNDLSearchSource:
    """Tests for NDLSearchSource."""

    def test_no_api_key_needed(self):
        """API キー不要でエラーにならない。"""
        source = NDLSearchSource()
        assert source.env_var_key is None
        # _check_api_key() は None を返すはず（キー不要）
        assert source._check_api_key() is None

    def test_empty_keywords(self):
        """空のキーワードリストでエラーを返す。"""
        source = NDLSearchSource()
        result = source.search(keywords=[])
        assert result.error == "No keywords provided"

    @responses.activate
    def test_successful_search(self):
        """正常な RSS レスポンスからドキュメントを生成する。"""
        responses.add(responses.GET, BASE_URL, body=_SAMPLE_RSS, status=200)

        source = NDLSearchSource()
        result = source.search(keywords=["怪談"], date_start="1868", date_end="1945")

        assert result.error is None
        assert result.total_hits == 1943
        assert len(result.documents) == 1

        doc = result.documents[0]
        assert doc.title == "怪談牡丹燈籠"
        assert doc.source_type == "ndl"
        assert doc.language == "ja"
        assert doc.location == "東京"
        assert "怪談" in doc.keywords_matched

    @responses.activate
    def test_date_filter(self):
        """from/until パラメータがリクエストに含まれる。"""
        responses.add(responses.GET, BASE_URL, body=_EMPTY_RSS, status=200)

        source = NDLSearchSource()
        source.search(keywords=["妖怪"], date_start="1868", date_end="1945")

        request = responses.calls[0].request
        assert "from=1868" in request.url
        assert "until=1945" in request.url

    @responses.activate
    def test_api_error_handling(self):
        """HTTP エラー時はエラーメッセージを返す。"""
        responses.add(responses.GET, BASE_URL, body="Server Error", status=500)

        source = NDLSearchSource()
        result = source.search(keywords=["怪談"])

        assert result.error is not None
        assert "API error" in result.error
        assert result.documents == []

    @responses.activate
    def test_empty_results(self):
        """0件結果。"""
        responses.add(responses.GET, BASE_URL, body=_EMPTY_RSS, status=200)

        source = NDLSearchSource()
        result = source.search(keywords=["存在しないキーワード"])

        assert result.total_hits == 0
        assert result.documents == []
        assert result.error is None

    @responses.activate
    def test_digital_resource_url_preferred(self):
        """rdfs:seeAlso の URL（デジタルコンテンツ直リンク）を優先する。"""
        responses.add(responses.GET, BASE_URL, body=_SAMPLE_RSS, status=200)

        source = NDLSearchSource()
        result = source.search(keywords=["怪談"])

        doc = result.documents[0]
        # rdfs:seeAlso の dl.ndl.go.jp URL を優先
        assert doc.source_url == "https://dl.ndl.go.jp/pid/12345"

    @responses.activate
    def test_fallback_to_link_url(self):
        """rdfs:seeAlso がない場合は link URL にフォールバックする。"""
        responses.add(responses.GET, BASE_URL, body=_MULTI_ITEM_RSS, status=200)

        source = NDLSearchSource()
        result = source.search(keywords=["妖怪"])

        # 2件目は rdfs:seeAlso なし → link にフォールバック
        doc2 = result.documents[1]
        assert "ndlsearch.ndl.go.jp" in doc2.source_url

    @responses.activate
    def test_html_description_stripped(self):
        """HTML タグが除去される。"""
        responses.add(responses.GET, BASE_URL, body=_SAMPLE_RSS, status=200)

        source = NDLSearchSource()
        result = source.search(keywords=["怪談"])

        doc = result.documents[0]
        # <br /> タグが除去されていること
        assert "<br" not in doc.summary
        assert "三遊亭圓朝の落語怪談。" in doc.summary

    @responses.activate
    def test_default_location(self):
        """出版地がない場合は Japan がデフォルト。"""
        responses.add(responses.GET, BASE_URL, body=_MULTI_ITEM_RSS, status=200)

        source = NDLSearchSource()
        result = source.search(keywords=["妖怪"])

        # 2件目は dcndl:publicationPlace なし → "Japan"
        doc2 = result.documents[1]
        assert doc2.location == "Japan"

    def test_source_metadata(self):
        """ソースメタデータが正しい。"""
        source = NDLSearchSource()
        assert source.source_key == "ndl"
        assert source.supported_languages == {"ja"}
        assert source.is_newspaper_source is False
        assert source.env_var_key is None
        assert source.min_request_delay == 1.0


class TestExtractPid:
    """Tests for _extract_pid helper."""

    def test_extracts_from_dl_url(self):
        """dl.ndl.go.jp URL から PID を抽出する。"""
        assert _extract_pid("https://dl.ndl.go.jp/pid/12345") == "12345"

    def test_extracts_from_url_with_suffix(self):
        """PID 後にパスが続く場合も抽出可能。"""
        assert _extract_pid("https://dl.ndl.go.jp/pid/99999/1/1") == "99999"

    def test_returns_none_for_catalog_url(self):
        """カタログ URL からは PID を抽出できない。"""
        assert _extract_pid("https://ndlsearch.ndl.go.jp/books/R100000002-I000") is None

    def test_returns_none_for_empty(self):
        """空文字列は None。"""
        assert _extract_pid("") is None

    def test_returns_none_for_unrelated_url(self):
        """無関係な URL は None。"""
        assert _extract_pid("https://example.com/pid/12345") is None


class TestFetchFulltext:
    """Tests for _fetch_fulltext."""

    @responses.activate
    def test_successful_fetch(self):
        """正常な layouttext レスポンスからテキストを抽出する。"""
        lab_url = _NDL_LAB_URL.format(pid="12345")
        mock_data = [
            {
                "blocks": [
                    {
                        "lines": [
                            {"text": "怪談牡丹燈籠"},
                            {"text": "三遊亭圓朝"},
                        ]
                    }
                ]
            },
            {
                "blocks": [
                    {
                        "lines": [
                            {"text": "第一話"},
                        ]
                    }
                ]
            },
        ]
        responses.add(responses.GET, lab_url, json=mock_data, status=200)

        from shared.http_retry import create_retry_session

        session = create_retry_session()
        text = _fetch_fulltext(session, "12345")

        assert text is not None
        assert "怪談牡丹燈籠" in text
        assert "三遊亭圓朝" in text
        assert "第一話" in text

    @responses.activate
    def test_404_returns_none(self):
        """404 レスポンスは None を返す。"""
        lab_url = _NDL_LAB_URL.format(pid="99999")
        responses.add(responses.GET, lab_url, body="Not Found", status=404)

        from shared.http_retry import create_retry_session

        session = create_retry_session()
        assert _fetch_fulltext(session, "99999") is None

    @responses.activate
    def test_timeout_returns_none(self):
        """タイムアウトは None を返す。"""
        import requests as req

        lab_url = _NDL_LAB_URL.format(pid="11111")
        responses.add(
            responses.GET, lab_url, body=req.exceptions.Timeout("timeout")
        )

        from shared.http_retry import create_retry_session

        session = create_retry_session()
        assert _fetch_fulltext(session, "11111") is None

    @responses.activate
    def test_truncated_at_5000(self):
        """テキストが5000文字で切り詰められる。"""
        lab_url = _NDL_LAB_URL.format(pid="22222")
        # 6000文字のテキストを含む1行
        long_text = "あ" * 6000
        mock_data = [{"blocks": [{"lines": [{"text": long_text}]}]}]
        responses.add(responses.GET, lab_url, json=mock_data, status=200)

        from shared.http_retry import create_retry_session

        session = create_retry_session()
        text = _fetch_fulltext(session, "22222")

        assert text is not None
        assert len(text) == 5000


class TestNDLFulltextEnrichment:
    """検索 + 全文エンリッチメント統合テスト。"""

    @responses.activate
    def test_search_with_fulltext_enrichment(self):
        """PID ありの結果に全文テキストが付与される。"""
        # 検索 API
        responses.add(responses.GET, BASE_URL, body=_SAMPLE_RSS, status=200)
        # Lab API（PID 12345）
        lab_url = _NDL_LAB_URL.format(pid="12345")
        mock_data = [{"blocks": [{"lines": [{"text": "OCR全文テキスト"}]}]}]
        responses.add(responses.GET, lab_url, json=mock_data, status=200)

        source = NDLSearchSource()
        result = source.search(keywords=["怪談"])

        assert len(result.documents) == 1
        assert result.documents[0].raw_text == "OCR全文テキスト"

    @responses.activate
    def test_fulltext_failure_preserves_document(self):
        """全文取得失敗でもドキュメントは保持される（raw_text=None）。"""
        responses.add(responses.GET, BASE_URL, body=_SAMPLE_RSS, status=200)
        lab_url = _NDL_LAB_URL.format(pid="12345")
        responses.add(responses.GET, lab_url, body="Error", status=500)

        source = NDLSearchSource()
        result = source.search(keywords=["怪談"])

        assert len(result.documents) == 1
        assert result.documents[0].raw_text is None

    @responses.activate
    def test_max_5_fulltext_fetches(self):
        """全文取得は最大5件まで。"""
        # 7件のアイテムを含む RSS を作成（全て PID あり）
        items = ""
        for i in range(7):
            items += f"""
            <item>
              <title>書籍{i}</title>
              <rdfs:seeAlso rdf:resource="https://dl.ndl.go.jp/pid/{10000 + i}" />
              <dc:date>1900</dc:date>
              <dc:description>説明{i}</dc:description>
            </item>"""

        rss = f"""<?xml version="1.0" encoding="UTF-8"?>
        <rss version="2.0"
          xmlns:dc="http://purl.org/dc/elements/1.1/"
          xmlns:openSearch="http://a9.com/-/spec/opensearchrss/1.0/"
          xmlns:rdfs="http://www.w3.org/2000/01/rdf-schema#"
          xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#">
          <channel>
            <openSearch:totalResults>7</openSearch:totalResults>
            {items}
          </channel>
        </rss>"""

        responses.add(responses.GET, BASE_URL, body=rss, status=200)

        # Lab API（全件成功）
        for i in range(7):
            lab_url = _NDL_LAB_URL.format(pid=str(10000 + i))
            mock_data = [{"blocks": [{"lines": [{"text": f"テキスト{i}"}]}]}]
            responses.add(responses.GET, lab_url, json=mock_data, status=200)

        source = NDLSearchSource()
        result = source.search(keywords=["書籍"])

        assert len(result.documents) == 7
        # 上位5件のみ全文取得（Lab API へのリクエスト数で確認）
        # 検索1回 + Lab 5回 = 6回
        assert len(responses.calls) == 6
        # 5件目までは raw_text あり、6-7件目は None
        for i in range(5):
            assert result.documents[i].raw_text is not None
        for i in range(5, 7):
            assert result.documents[i].raw_text is None


class TestStripHtml:
    """Tests for _strip_html helper."""

    def test_strips_tags(self):
        assert _strip_html("<p>hello</p>") == "hello"

    def test_strips_br(self):
        assert _strip_html("line1<br />line2") == "line1line2"

    def test_no_tags(self):
        assert _strip_html("plain text") == "plain text"

    def test_empty_string(self):
        assert _strip_html("") == ""
