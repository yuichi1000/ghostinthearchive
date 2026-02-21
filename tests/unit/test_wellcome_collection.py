"""Unit tests for Wellcome Collection Catalogue API tool."""

import responses

from mystery_agents.schemas.document import SourceLanguage
from mystery_agents.tools.wellcome_collection import (
    BASE_URL,
    WellcomeSource,
    _detect_language,
    _extract_date_label,
    _extract_location,
    _parse_wellcome_response,
    _strip_html,
)

# モック JSON レスポンス
MOCK_RESPONSE = {
    "totalResults": 2,
    "results": [
        {
            "id": "abc123",
            "title": "A Treatise on Witchcraft and Superstition",
            "description": "<p>An early modern text on <strong>witchcraft</strong> beliefs.</p>",
            "production": [
                {
                    "dates": [{"label": "1684"}],
                    "places": [{"label": "London"}],
                }
            ],
            "languages": [{"id": "eng", "label": "English"}],
        },
        {
            "id": "def456",
            "title": "Folk Medicine in Rural England",
            "description": None,
            "production": [
                {
                    "dates": [{"label": "circa 1750"}],
                    "places": [],
                }
            ],
            "languages": [{"id": "eng", "label": "English"}],
        },
    ],
}

MOCK_EMPTY_RESPONSE = {
    "totalResults": 0,
    "results": [],
}


class TestWellcomeSource:
    """Tests for WellcomeSource."""

    def test_source_metadata(self):
        """ソースメタデータの基本確認。"""
        source = WellcomeSource()
        assert source.source_key == "wellcome"
        assert source.source_name == "Wellcome Collection"
        assert source.supported_languages == {"en"}
        assert source.supports_language_filter is True
        assert source.is_newspaper_source is False
        assert source.min_request_delay == 1.0
        assert source.env_var_key is None

    @responses.activate
    def test_successful_search(self):
        """正常な JSON レスポンスで ArchiveDocument に変換する。"""
        responses.add(
            responses.GET,
            BASE_URL,
            json=MOCK_RESPONSE,
            status=200,
        )

        source = WellcomeSource()
        result = source.search(keywords=["witchcraft", "superstition"])

        assert result.error is None
        assert result.total_hits == 2
        assert len(result.documents) == 2

        doc = result.documents[0]
        assert doc.title == "A Treatise on Witchcraft and Superstition"
        assert doc.language == SourceLanguage.EN
        assert doc.source_type == "wellcome"
        assert doc.source_url == "https://wellcomecollection.org/works/abc123"
        assert doc.date == "1684-01-01"
        assert doc.location == "London"
        # HTML が除去されたサマリー
        assert doc.summary == "An early modern text on witchcraft beliefs."
        assert doc.raw_text is None

    @responses.activate
    def test_html_stripped_from_description(self):
        """description の HTML タグが除去される。"""
        responses.add(
            responses.GET,
            BASE_URL,
            json=MOCK_RESPONSE,
            status=200,
        )

        source = WellcomeSource()
        result = source.search(keywords=["witchcraft"])

        doc = result.documents[0]
        assert "<p>" not in doc.summary
        assert "<strong>" not in doc.summary

    @responses.activate
    def test_none_description_uses_title(self):
        """description が None の場合、title をサマリーに代替する。"""
        responses.add(
            responses.GET,
            BASE_URL,
            json=MOCK_RESPONSE,
            status=200,
        )

        source = WellcomeSource()
        result = source.search(keywords=["folk"])

        doc = result.documents[1]
        assert doc.summary == "Folk Medicine in Rural England"

    @responses.activate
    def test_empty_results(self):
        """0件レスポンスの場合。"""
        responses.add(
            responses.GET,
            BASE_URL,
            json=MOCK_EMPTY_RESPONSE,
            status=200,
        )

        source = WellcomeSource()
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

        source = WellcomeSource()
        result = source.search(keywords=["test"])

        assert result.error is not None
        assert "API error" in result.error
        assert result.documents == []

    def test_empty_keywords_returns_error(self):
        """空のキーワードでエラーを返す。"""
        source = WellcomeSource()
        result = source.search(keywords=[])
        assert result.error == "No keywords provided"

    @responses.activate
    def test_date_parameters(self):
        """日付パラメータが YYYY-MM-DD 形式でリクエストに含まれる。"""
        responses.add(
            responses.GET,
            BASE_URL,
            json=MOCK_EMPTY_RESPONSE,
            status=200,
        )

        source = WellcomeSource()
        source.search(
            keywords=["plague"],
            date_start="1600",
            date_end="1700",
        )

        request = responses.calls[0].request
        assert "production.dates.from=1600-01-01" in request.url
        assert "production.dates.to=1700-12-31" in request.url

    @responses.activate
    def test_language_parameter(self):
        """言語パラメータが ISO 639-3 に変換されてリクエストに含まれる。"""
        responses.add(
            responses.GET,
            BASE_URL,
            json=MOCK_EMPTY_RESPONSE,
            status=200,
        )

        source = WellcomeSource()
        source.search(keywords=["test"], language="en")

        request = responses.calls[0].request
        assert "languages=eng" in request.url

    @responses.activate
    def test_default_location(self):
        """places が空の場合、デフォルト "United Kingdom" を使用する。"""
        responses.add(
            responses.GET,
            BASE_URL,
            json=MOCK_RESPONSE,
            status=200,
        )

        source = WellcomeSource()
        result = source.search(keywords=["folk"])

        # 2件目は places が空
        doc = result.documents[1]
        assert doc.location == "United Kingdom"

    @responses.activate
    def test_work_without_id_skipped(self):
        """id が未設定のワークはスキップされる。"""
        data = {
            "totalResults": 1,
            "results": [
                {
                    "title": "No ID Work",
                    "description": "Some description",
                    "production": [],
                    "languages": [{"id": "eng"}],
                }
            ],
        }
        responses.add(
            responses.GET,
            BASE_URL,
            json=data,
            status=200,
        )

        source = WellcomeSource()
        result = source.search(keywords=["test"])

        assert result.total_hits == 1  # サーバーは1件と報告
        assert len(result.documents) == 0  # id なしでスキップ

    def test_keyword_matching(self):
        """keywords_matched が正しく検出される。"""
        result = _parse_wellcome_response(
            MOCK_RESPONSE, keywords=["witchcraft", "Folk"]
        )

        # 1件目: "witchcraft" がタイトル・説明に含まれる
        assert "witchcraft" in result.documents[0].keywords_matched
        # 2件目: "Folk" がタイトルに含まれる（大文字小文字非区別）
        assert "Folk" in result.documents[1].keywords_matched


class TestHelperFunctions:
    """ヘルパー関数の個別テスト。"""

    def test_strip_html_removes_tags(self):
        """HTML タグが除去される。"""
        assert _strip_html("<p>Hello <b>world</b></p>") == "Hello world"

    def test_strip_html_none(self):
        """None の場合は空文字列を返す。"""
        assert _strip_html(None) == ""

    def test_strip_html_empty(self):
        """空文字列の場合はそのまま返す。"""
        assert _strip_html("") == ""

    def test_strip_html_no_tags(self):
        """タグなしテキストはそのまま返す。"""
        assert _strip_html("plain text") == "plain text"

    def test_detect_language_english(self):
        """英語の検出。"""
        work = {"languages": [{"id": "eng", "label": "English"}]}
        assert _detect_language(work) == SourceLanguage.EN

    def test_detect_language_french(self):
        """フランス語の検出（fre / fra 両方）。"""
        assert _detect_language({"languages": [{"id": "fre"}]}) == SourceLanguage.FR
        assert _detect_language({"languages": [{"id": "fra"}]}) == SourceLanguage.FR

    def test_detect_language_german(self):
        """ドイツ語の検出（ger / deu 両方）。"""
        assert _detect_language({"languages": [{"id": "ger"}]}) == SourceLanguage.DE
        assert _detect_language({"languages": [{"id": "deu"}]}) == SourceLanguage.DE

    def test_detect_language_unknown_defaults_to_en(self):
        """不明な言語コードは EN をデフォルトにする。"""
        assert _detect_language({"languages": [{"id": "zho"}]}) == SourceLanguage.EN

    def test_detect_language_empty_languages(self):
        """languages が空の場合は EN。"""
        assert _detect_language({"languages": []}) == SourceLanguage.EN

    def test_detect_language_no_languages_key(self):
        """languages キーがない場合は EN。"""
        assert _detect_language({}) == SourceLanguage.EN

    def test_extract_date_label(self):
        """production.dates からラベルを抽出する。"""
        work = {"production": [{"dates": [{"label": "1750"}]}]}
        assert _extract_date_label(work) == "1750"

    def test_extract_date_label_empty(self):
        """production が空の場合は空文字列。"""
        assert _extract_date_label({"production": []}) == ""
        assert _extract_date_label({}) == ""

    def test_extract_date_label_no_dates(self):
        """dates が空の場合は空文字列。"""
        assert _extract_date_label({"production": [{"dates": []}]}) == ""

    def test_extract_location(self):
        """production.places からラベルを抽出する。"""
        work = {"production": [{"places": [{"label": "Edinburgh"}]}]}
        assert _extract_location(work) == "Edinburgh"

    def test_extract_location_default(self):
        """places が空の場合はデフォルト "United Kingdom"。"""
        assert _extract_location({"production": []}) == "United Kingdom"
        assert _extract_location({}) == "United Kingdom"

    def test_extract_location_empty_places(self):
        """places が空リストの場合はデフォルト。"""
        assert _extract_location({"production": [{"places": []}]}) == "United Kingdom"
