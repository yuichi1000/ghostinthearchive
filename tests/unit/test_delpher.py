"""Unit tests for KB/Delpher SRU API tool."""

import responses

from mystery_agents.schemas.document import SourceLanguage
from mystery_agents.tools.delpher import (
    BASE_URL,
    DelpherSource,
    _parse_sru_response,
)

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

    def test_date_parsing(self):
        """SRU の日付フォーマット（YYYY/MM/DD HH:MM:SS）が正しくパースされる。"""
        result = _parse_sru_response(MOCK_SRU_RESPONSE, keywords=[])
        # "1842/03/15 00:00:00" → "1842-01-01"
        assert result.documents[0].date == "1842-01-01"
        # "1756/08/20 00:00:00" → "1756-01-01"
        assert result.documents[1].date == "1756-01-01"
