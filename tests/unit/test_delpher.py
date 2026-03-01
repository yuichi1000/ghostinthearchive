"""Unit tests for KB/Delpher SRU API tool."""

import responses

from mystery_agents.schemas.document import SourceLanguage
from mystery_agents.tools.delpher import (
    BASE_URL,
    COLLECTION,
    DelpherSource,
    _fetch_ocr_text,
    _parse_sru_response,
)
from mystery_agents.tools.search_utils import build_search_query
from shared.http_retry import create_retry_session

# モック SRU XML レスポンス
MOCK_SRU_RESPONSE = """\
<?xml version="1.0" encoding="UTF-8"?>
<srw:searchRetrieveResponse xmlns:srw="http://www.loc.gov/zing/srw/"
    xmlns:dc="http://purl.org/dc/elements/1.1/">
  <srw:version>1.2</srw:version>
  <srw:numberOfRecords>2</srw:numberOfRecords>
  <srw:records>
    <srw:record>
      <srw:recordData>
        <dc:title>Het spookhuis te Amsterdam</dc:title>
        <dc:date>1842/03/15 00:00:00</dc:date>
        <dc:identifier>http://resolver.kb.nl/resolve?urn=ddd:010097857:mpeg21:a0001</dc:identifier>
        <dc:description>Een mysterieus verhaal over het spookhuis</dc:description>
        <dc:publisher>De Tijd</dc:publisher>
        <dc:language>dut</dc:language>
        <dc:type>Text</dc:type>
      </srw:recordData>
    </srw:record>
    <srw:record>
      <srw:recordData>
        <dc:title>Vliegende Hollander gezien</dc:title>
        <dc:date>1756/08/20 00:00:00</dc:date>
        <dc:identifier>http://resolver.kb.nl/resolve?urn=ddd:010054321:mpeg21:a0002</dc:identifier>
        <dc:description>Bericht over de Vliegende Hollander</dc:description>
        <dc:source>Opregte Haarlemsche Courant</dc:source>
        <dc:language>dut</dc:language>
        <dc:type>Text</dc:type>
      </srw:recordData>
    </srw:record>
  </srw:records>
</srw:searchRetrieveResponse>"""

MOCK_EMPTY_RESPONSE = """\
<?xml version="1.0" encoding="UTF-8"?>
<srw:searchRetrieveResponse xmlns:srw="http://www.loc.gov/zing/srw/">
  <srw:version>1.2</srw:version>
  <srw:numberOfRecords>0</srw:numberOfRecords>
</srw:searchRetrieveResponse>"""


class TestDelpherSource:
    """Tests for DelpherSource."""

    def test_no_api_key_required(self):
        """env_var_key が None であることを確認（認証不要）。"""
        source = DelpherSource()
        assert source.env_var_key is None

    def test_source_metadata(self):
        """ソースメタデータの基本確認。"""
        source = DelpherSource()
        assert source.source_key == "delpher"
        assert source.supported_languages == {"nl"}
        assert source.is_newspaper_source is False
        assert source.min_request_delay == 2.0

    @responses.activate
    def test_successful_search(self):
        """正常な XML レスポンスで ArchiveDocument に変換する。"""
        responses.add(
            responses.GET,
            BASE_URL,
            body=MOCK_SRU_RESPONSE,
            content_type="application/xml",
            status=200,
        )
        # OCR 全文取得モック
        responses.add(
            responses.GET,
            "http://resolver.kb.nl/resolve?urn=ddd:010097857:mpeg21:a0001:ocr",
            body="OCR text van het spookhuis.",
            status=200,
        )
        responses.add(
            responses.GET,
            "http://resolver.kb.nl/resolve?urn=ddd:010054321:mpeg21:a0002:ocr",
            body="OCR text van de Vliegende Hollander.",
            status=200,
        )

        source = DelpherSource()
        result = source.search(keywords=["spookhuis", "Amsterdam"])

        assert result.error is None
        assert result.total_hits == 2
        assert len(result.documents) == 2

        doc = result.documents[0]
        assert doc.title == "Het spookhuis te Amsterdam"
        assert doc.language == SourceLanguage.NL
        assert doc.source_type == "delpher"
        assert "resolver.kb.nl" in doc.source_url
        assert doc.date == "1842-01-01"
        assert doc.location == "De Tijd"
        assert doc.summary == "Een mysterieus verhaal over het spookhuis"
        assert doc.raw_text == "OCR text van het spookhuis."

        # 2件目: publisher がない場合 source フィールドを location に使用
        doc2 = result.documents[1]
        assert doc2.location == "Opregte Haarlemsche Courant"

    @responses.activate
    def test_empty_results(self):
        """0件レスポンスの場合。"""
        responses.add(
            responses.GET,
            BASE_URL,
            body=MOCK_EMPTY_RESPONSE,
            content_type="application/xml",
            status=200,
        )

        source = DelpherSource()
        result = source.search(keywords=["nonexistent"])

        assert result.total_hits == 0
        assert result.documents == []
        assert result.error is None

    @responses.activate
    def test_api_error_handling(self):
        """500 エラー時はエラーメッセージを返す。"""
        responses.add(
            responses.GET,
            BASE_URL,
            body="Internal Server Error",
            status=500,
        )

        source = DelpherSource()
        result = source.search(keywords=["test"])

        assert result.error is not None
        assert "API error" in result.error
        assert result.documents == []

    @responses.activate
    def test_sru_parameters(self):
        """SRU パラメータが正しくリクエストに含まれる。"""
        responses.add(
            responses.GET,
            BASE_URL,
            body=MOCK_EMPTY_RESPONSE,
            content_type="application/xml",
            status=200,
        )

        source = DelpherSource()
        source.search(keywords=["spook"])

        request = responses.calls[0].request
        assert "operation=searchRetrieve" in request.url
        assert "version=1.2" in request.url
        assert "x-collection=DDD_artikel" in request.url
        assert "recordSchema=dc" in request.url
        assert "spook" in request.url

    def test_keyword_matching(self):
        """keywords_matched が正しく検出される。"""
        result = _parse_sru_response(
            MOCK_SRU_RESPONSE, keywords=["spookhuis", "Hollander"]
        )

        # 1件目: "spookhuis" がタイトル・説明に含まれる
        assert "spookhuis" in result.documents[0].keywords_matched
        # 2件目: "Hollander" がタイトル・説明に含まれる
        assert "Hollander" in result.documents[1].keywords_matched

    def test_parse_invalid_xml(self):
        """不正 XML のエラーハンドリング。"""
        result = _parse_sru_response("<invalid>xml", keywords=["test"])
        assert result.error is not None
        assert "XML parse error" in result.error

    def test_record_without_identifier_skipped(self):
        """identifier（URL）がないレコードはスキップされる。"""
        xml_no_identifier = """\
<?xml version="1.0" encoding="UTF-8"?>
<srw:searchRetrieveResponse xmlns:srw="http://www.loc.gov/zing/srw/"
    xmlns:dc="http://purl.org/dc/elements/1.1/">
  <srw:numberOfRecords>1</srw:numberOfRecords>
  <srw:records>
    <srw:record>
      <srw:recordData>
        <dc:title>Record without URL</dc:title>
        <dc:date>1800/01/01 00:00:00</dc:date>
        <dc:language>dut</dc:language>
      </srw:recordData>
    </srw:record>
  </srw:records>
</srw:searchRetrieveResponse>"""

        result = _parse_sru_response(xml_no_identifier, keywords=["test"])
        assert result.total_hits == 1  # サーバーは1件と報告
        assert len(result.documents) == 0  # identifier なしでスキップ

    def test_empty_keywords_returns_error(self):
        """空のキーワードでエラーを返す。"""
        source = DelpherSource()
        result = source.search(keywords=[])
        assert result.error == "No keywords provided"

    def test_multi_word_keywords_quoted_in_cql(self):
        """複数語キーワードが CQL クエリ内で正しくクォートされる。"""
        query = build_search_query(["Oera Linda Boek", "1867"])
        assert '"Oera Linda Boek"' in query
        assert "1867" in query
        # 単語キーワードはクォートされない
        assert query == '"Oera Linda Boek" OR 1867'

    def test_date_parsing(self):
        """SRU の日付フォーマット（YYYY/MM/DD HH:MM:SS）が正しくパースされる。"""
        result = _parse_sru_response(MOCK_SRU_RESPONSE, keywords=[])
        # "1842/03/15 00:00:00" → "1842-01-01"
        assert result.documents[0].date == "1842-01-01"
        # "1756/08/20 00:00:00" → "1756-01-01"
        assert result.documents[1].date == "1756-01-01"


class TestDelpherDateFilter:
    """Delpher 年代フィルタのテスト。"""

    @responses.activate
    def test_date_filter_in_cql_query(self):
        """日付パラメータが CQL dc.date 比較としてリクエストに含まれる。"""
        responses.add(
            responses.GET,
            BASE_URL,
            body=MOCK_EMPTY_RESPONSE,
            content_type="application/xml",
            status=200,
        )

        source = DelpherSource()
        source.search(
            keywords=["spook"],
            date_start="1800",
            date_end="1899",
        )

        request = responses.calls[0].request
        from urllib.parse import unquote_plus
        query_str = unquote_plus(request.url)
        assert 'dc.date >= "1800"' in query_str
        assert 'dc.date <= "1899"' in query_str

    @responses.activate
    def test_no_date_filter_when_dates_empty(self):
        """date_start/date_end が空文字の場合、dc.date が含まれない。"""
        responses.add(
            responses.GET,
            BASE_URL,
            body=MOCK_EMPTY_RESPONSE,
            content_type="application/xml",
            status=200,
        )

        source = DelpherSource()
        source.search(
            keywords=["spook"],
            date_start="",
            date_end="",
        )

        request = responses.calls[0].request
        assert "dc.date" not in request.url


class TestFetchOcrText:
    """_fetch_ocr_text のテスト。"""

    @responses.activate
    def test_returns_text(self):
        """OCR テキストが取得できる場合にテキストを返す。"""
        resolver_url = "http://resolver.kb.nl/resolve?urn=ddd:010097857:mpeg21:a0001"
        responses.add(
            responses.GET,
            f"{resolver_url}:ocr",
            body="Dit is de OCR tekst.",
            status=200,
        )

        session = create_retry_session()
        result = _fetch_ocr_text(session, resolver_url)

        assert result == "Dit is de OCR tekst."

    @responses.activate
    def test_returns_none_on_404(self):
        """404 の場合は None を返す。"""
        resolver_url = "http://resolver.kb.nl/resolve?urn=ddd:missing"
        responses.add(
            responses.GET,
            f"{resolver_url}:ocr",
            status=404,
        )

        session = create_retry_session()
        result = _fetch_ocr_text(session, resolver_url)

        assert result is None

    @responses.activate
    def test_returns_full_text_under_raw_limit(self):
        """安全上限以下のテキストはそのまま返す（キーワード抽出は呼び出し側で行う）。"""
        resolver_url = "http://resolver.kb.nl/resolve?urn=ddd:long"
        responses.add(
            responses.GET,
            f"{resolver_url}:ocr",
            body="X" * 6000,
            status=200,
        )

        session = create_retry_session()
        result = _fetch_ocr_text(session, resolver_url)

        assert len(result) == 6000

    @responses.activate
    def test_returns_none_on_empty_text(self):
        """空のレスポンスは None を返す。"""
        resolver_url = "http://resolver.kb.nl/resolve?urn=ddd:empty"
        responses.add(
            responses.GET,
            f"{resolver_url}:ocr",
            body="   ",
            status=200,
        )

        session = create_retry_session()
        result = _fetch_ocr_text(session, resolver_url)

        assert result is None


class TestDelpherFulltextFilter:
    """Delpher 全文フィルタリングテスト。"""

    @responses.activate
    def test_filters_docs_without_ocr(self):
        """OCR 取得に失敗したドキュメントは除外される。"""
        responses.add(
            responses.GET,
            BASE_URL,
            body=MOCK_SRU_RESPONSE,
            content_type="application/xml",
            status=200,
        )
        # 1件目: OCR あり
        responses.add(
            responses.GET,
            "http://resolver.kb.nl/resolve?urn=ddd:010097857:mpeg21:a0001:ocr",
            body="OCR tekst beschikbaar.",
            status=200,
        )
        # 2件目: OCR 404
        responses.add(
            responses.GET,
            "http://resolver.kb.nl/resolve?urn=ddd:010054321:mpeg21:a0002:ocr",
            status=404,
        )

        source = DelpherSource()
        result = source.search(keywords=["spookhuis"])

        assert len(result.documents) == 1
        assert result.documents[0].title == "Het spookhuis te Amsterdam"
        assert result.documents[0].raw_text == "OCR tekst beschikbaar."
