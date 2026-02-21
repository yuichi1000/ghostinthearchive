"""Unit tests for NDL Search API tool."""

import responses

from mystery_agents.tools.ndl_search import BASE_URL, NDLSearchSource, _strip_html


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
