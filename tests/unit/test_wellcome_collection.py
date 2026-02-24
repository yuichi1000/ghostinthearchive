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
        # description がある場合、raw_text に設定される
        assert doc.raw_text == "An early modern text on witchcraft beliefs."

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

    def test_strip_html_list_input(self):
        """list 型入力（実 Wellcome API の notes[].contents 形式）を処理する。"""
        assert _strip_html(["<p>text</p>", "more"]) == "text more"

    def test_strip_html_list_with_none_items(self):
        """list 内の None 項目をスキップする。"""
        assert _strip_html(["first", None, "third"]) == "first third"

    def test_strip_html_empty_list(self):
        """空リストの場合は空文字列を返す。"""
        assert _strip_html([]) == ""

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


class TestNotesToRawText:
    """notes → raw_text 変換のテスト。"""

    def test_notes_to_raw_text(self):
        """notes フィールドが raw_text に反映される（実 API は contents が list）。"""
        data = {
            "totalResults": 1,
            "results": [
                {
                    "id": "note1",
                    "title": "Test Work",
                    "description": None,
                    "notes": [
                        {"contents": ["First note about the manuscript."]},
                        {"contents": ["<p>Second note with <b>HTML</b>.</p>"]},
                    ],
                    "production": [],
                    "languages": [{"id": "eng"}],
                }
            ],
        }
        result = _parse_wellcome_response(data, keywords=["test"])
        doc = result.documents[0]
        assert doc.raw_text == "First note about the manuscript. Second note with HTML."

    def test_description_and_notes_combined(self):
        """description と notes が結合されて raw_text になる。"""
        data = {
            "totalResults": 1,
            "results": [
                {
                    "id": "combo1",
                    "title": "Combined Work",
                    "description": "A detailed description.",
                    "notes": [
                        {"contents": ["Additional context from notes."]},
                    ],
                    "production": [],
                    "languages": [{"id": "eng"}],
                }
            ],
        }
        result = _parse_wellcome_response(data, keywords=["test"])
        doc = result.documents[0]
        assert doc.raw_text == "A detailed description. Additional context from notes."

    def test_no_notes_backward_compat(self):
        """notes がない場合は description のみで raw_text が設定される。"""
        data = {
            "totalResults": 1,
            "results": [
                {
                    "id": "nonote1",
                    "title": "No Notes Work",
                    "description": "Only description here.",
                    "production": [],
                    "languages": [{"id": "eng"}],
                }
            ],
        }
        result = _parse_wellcome_response(data, keywords=["test"])
        doc = result.documents[0]
        assert doc.raw_text == "Only description here."

    def test_no_description_no_notes(self):
        """description も notes もない場合は raw_text が None。"""
        data = {
            "totalResults": 1,
            "results": [
                {
                    "id": "empty1",
                    "title": "Empty Work",
                    "description": None,
                    "production": [],
                    "languages": [{"id": "eng"}],
                }
            ],
        }
        result = _parse_wellcome_response(data, keywords=["test"])
        doc = result.documents[0]
        assert doc.raw_text is None

    def test_raw_text_truncated_at_5000(self):
        """raw_text が5000文字で切り詰められる。"""
        long_note = "A" * 6000
        data = {
            "totalResults": 1,
            "results": [
                {
                    "id": "long1",
                    "title": "Long Work",
                    "description": None,
                    "notes": [{"contents": [long_note]}],
                    "production": [],
                    "languages": [{"id": "eng"}],
                }
            ],
        }
        result = _parse_wellcome_response(data, keywords=["test"])
        doc = result.documents[0]
        assert len(doc.raw_text) == 5000


class TestDateFilterFallback:
    """日付フィルタのフォールバック機構テスト。"""

    @responses.activate
    def test_date_filter_fallback_on_zero_results(self):
        """日付フィルタ付きで 0 件 → 日付フィルタなしで再検索する。"""
        # 1 回目: 日付フィルタ付き → 0 件
        responses.add(
            responses.GET,
            BASE_URL,
            json=MOCK_EMPTY_RESPONSE,
            status=200,
        )
        # 2 回目: 日付フィルタなし → 結果あり
        responses.add(
            responses.GET,
            BASE_URL,
            json=MOCK_RESPONSE,
            status=200,
        )

        source = WellcomeSource()
        result = source.search(
            keywords=["witchcraft"],
            date_start="1650",
            date_end="1850",
        )

        # フォールバックで結果が取得される
        assert len(result.documents) == 2
        assert result.total_hits == 2

        # 2 回リクエストされた
        assert len(responses.calls) == 2

        # 1 回目: 日付フィルタあり
        first_request = responses.calls[0].request
        assert "production.dates.from=1650-01-01" in first_request.url

        # 2 回目: 日付フィルタなし
        second_request = responses.calls[1].request
        assert "production.dates.from" not in second_request.url
        assert "production.dates.to" not in second_request.url

    @responses.activate
    def test_no_fallback_when_results_found(self):
        """日付フィルタ付きで結果がある場合、再検索しない。"""
        responses.add(
            responses.GET,
            BASE_URL,
            json=MOCK_RESPONSE,
            status=200,
        )

        source = WellcomeSource()
        result = source.search(
            keywords=["witchcraft"],
            date_start="1650",
            date_end="1850",
        )

        assert len(result.documents) == 2
        # 1 回のみリクエスト
        assert len(responses.calls) == 1

    @responses.activate
    def test_no_fallback_without_date_filter(self):
        """日付フィルタなしの検索で 0 件でも再検索しない。"""
        responses.add(
            responses.GET,
            BASE_URL,
            json=MOCK_EMPTY_RESPONSE,
            status=200,
        )

        source = WellcomeSource()
        result = source.search(keywords=["nonexistent"])

        assert len(result.documents) == 0
        # 1 回のみリクエスト
        assert len(responses.calls) == 1

    @responses.activate
    def test_fallback_also_zero_returns_empty(self):
        """フォールバック検索も 0 件の場合は空を返す。"""
        # 両方 0 件
        responses.add(
            responses.GET,
            BASE_URL,
            json=MOCK_EMPTY_RESPONSE,
            status=200,
        )
        responses.add(
            responses.GET,
            BASE_URL,
            json=MOCK_EMPTY_RESPONSE,
            status=200,
        )

        source = WellcomeSource()
        result = source.search(
            keywords=["obscure_term"],
            date_start="1650",
            date_end="1850",
        )

        assert len(result.documents) == 0
        # 2 回リクエスト（フォールバック含む）
        assert len(responses.calls) == 2
