"""Unit tests for Europeana API tool."""

from unittest.mock import patch

import responses

from mystery_agents.tools.europeana import (
    BASE_URL,
    EuropeanaSource,
    _FULLTEXT_URL,
    _detect_language,
    _extract_location,
    _extract_record_ids,
    _fetch_fulltext,
    _parse_annotation_text,
)
from mystery_agents.tools.archive_source_base import ArchiveSource
from shared.http_retry import create_retry_session


class TestSearchEuropeana:
    """Tests for EuropeanaSource.search()."""

    def test_missing_api_key(self):
        """API Key 未設定時はエラーを返す。"""
        source = EuropeanaSource()
        with patch.dict("os.environ", {}, clear=True):
            result = source.search(keywords=["test"])
        assert result.error == "EUROPEANA_API_KEY not set"
        assert result.documents == []

    def test_empty_keywords(self):
        """空のキーワードリストでエラーを返す。"""
        source = EuropeanaSource()
        with patch.dict("os.environ", {"EUROPEANA_API_KEY": "test_key"}):
            result = source.search(keywords=[])
        assert result.error == "No keywords provided"

    @responses.activate
    def test_successful_search(self):
        """正常なレスポンスでドキュメントを返す。"""
        mock_response = {
            "success": True,
            "totalResults": 1,
            "items": [
                {
                    "title": ["Medieval Manuscript from Paris"],
                    "year": ["1450"],
                    "guid": "https://www.europeana.eu/item/123/abc",
                    "id": "/123/abc",
                    "dcDescription": ["A rare medieval manuscript found in Paris archives"],
                    "language": ["fr"],
                    "country": ["France"],
                }
            ],
        }
        responses.add(responses.GET, BASE_URL, json=mock_response, status=200)
        # 全文取得モック
        responses.add(
            responses.GET,
            _FULLTEXT_URL.format(dataset_id="123", local_id="abc"),
            json={"items": [{"body": {"value": "Full OCR text of the manuscript."}}]},
            status=200,
        )

        source = EuropeanaSource()
        with patch.dict("os.environ", {"EUROPEANA_API_KEY": "test_key"}):
            result = source.search(keywords=["medieval", "manuscript"])

        assert result.total_hits == 1
        assert len(result.documents) == 1
        doc = result.documents[0]
        assert doc.title == "Medieval Manuscript from Paris"
        assert doc.language == "fr"
        assert doc.source_type == "europeana"
        assert "europeana.eu" in doc.source_url
        assert doc.raw_text == "Full OCR text of the manuscript."

    @responses.activate
    def test_country_filter(self):
        """language パラメータで qf=COUNTRY:germany が送信される（LANGUAGE ではなく COUNTRY）。"""
        mock_response = {"success": True, "totalResults": 0, "items": []}
        responses.add(responses.GET, BASE_URL, json=mock_response, status=200)

        source = EuropeanaSource()
        with patch.dict("os.environ", {"EUROPEANA_API_KEY": "test_key"}):
            source.search(keywords=["test"], language="de")

        request = responses.calls[0].request
        assert "COUNTRY%3Agermany" in request.url or "COUNTRY:germany" in request.url
        assert "LANGUAGE" not in request.url

    @responses.activate
    def test_country_filter_french(self):
        """フランス語 → COUNTRY:france で送信される。"""
        mock_response = {"success": True, "totalResults": 0, "items": []}
        responses.add(responses.GET, BASE_URL, json=mock_response, status=200)

        source = EuropeanaSource()
        with patch.dict("os.environ", {"EUROPEANA_API_KEY": "test_key"}):
            source.search(keywords=["test"], language="fr")

        request = responses.calls[0].request
        assert "COUNTRY%3Afrance" in request.url or "COUNTRY:france" in request.url

    @responses.activate
    def test_country_filter_italian(self):
        """イタリア語 → COUNTRY:italy で送信される。"""
        mock_response = {"success": True, "totalResults": 0, "items": []}
        responses.add(responses.GET, BASE_URL, json=mock_response, status=200)

        source = EuropeanaSource()
        with patch.dict("os.environ", {"EUROPEANA_API_KEY": "test_key"}):
            source.search(keywords=["test"], language="it")

        request = responses.calls[0].request
        assert "COUNTRY%3Aitaly" in request.url or "COUNTRY:italy" in request.url

    @responses.activate
    def test_unmapped_language_no_country_filter(self):
        """マッピングにない言語（en 等）では COUNTRY フィルタが送信されない。"""
        mock_response = {"success": True, "totalResults": 0, "items": []}
        responses.add(responses.GET, BASE_URL, json=mock_response, status=200)

        source = EuropeanaSource()
        with patch.dict("os.environ", {"EUROPEANA_API_KEY": "test_key"}):
            source.search(keywords=["test"], language="en")

        request = responses.calls[0].request
        assert "COUNTRY" not in request.url
        assert "LANGUAGE" not in request.url

    @responses.activate
    def test_date_filter(self):
        """日付フィルタが qf パラメータで送信される。"""
        mock_response = {"success": True, "totalResults": 0, "items": []}
        responses.add(responses.GET, BASE_URL, json=mock_response, status=200)

        source = EuropeanaSource()
        with patch.dict("os.environ", {"EUROPEANA_API_KEY": "test_key"}):
            source.search(keywords=["test"], date_start="1800", date_end="1899")

        request = responses.calls[0].request
        assert "1800" in request.url
        assert "1899" in request.url

    @responses.activate
    def test_api_error_handling(self):
        """API エラー時はエラーメッセージを返す。"""
        responses.add(responses.GET, BASE_URL, json={"error": "forbidden"}, status=403)

        source = EuropeanaSource()
        with patch.dict("os.environ", {"EUROPEANA_API_KEY": "bad_key"}):
            result = source.search(keywords=["test"])

        assert result.error is not None
        assert "API error" in result.error
        assert result.documents == []

    @responses.activate
    def test_empty_results(self):
        """結果が0件の場合。"""
        mock_response = {"success": True, "totalResults": 0, "items": []}
        responses.add(responses.GET, BASE_URL, json=mock_response, status=200)

        source = EuropeanaSource()
        with patch.dict("os.environ", {"EUROPEANA_API_KEY": "test_key"}):
            result = source.search(keywords=["nonexistent"])

        assert result.total_hits == 0
        assert result.documents == []
        assert result.error is None

    @responses.activate
    def test_wskey_parameter(self):
        """wskey パラメータがリクエストに含まれることを確認。"""
        mock_response = {"success": True, "totalResults": 0, "items": []}
        responses.add(responses.GET, BASE_URL, json=mock_response, status=200)

        source = EuropeanaSource()
        with patch.dict("os.environ", {"EUROPEANA_API_KEY": "my_secret_key"}):
            source.search(keywords=["test"])

        request = responses.calls[0].request
        assert "wskey=my_secret_key" in request.url

    @responses.activate
    def test_edmIsShownAt_fallback(self):
        """guid がない場合は edmIsShownAt にフォールバックする。"""
        mock_response = {
            "success": True,
            "totalResults": 1,
            "items": [
                {
                    "title": ["Test Document"],
                    "id": "/456/test_doc",
                    "edmIsShownAt": ["https://example.europeana.eu/item/456"],
                    "language": ["en"],
                    "country": ["United Kingdom"],
                }
            ],
        }
        responses.add(responses.GET, BASE_URL, json=mock_response, status=200)
        # 全文取得モック
        responses.add(
            responses.GET,
            _FULLTEXT_URL.format(dataset_id="456", local_id="test_doc"),
            json={"items": [{"body": {"value": "Fulltext via edmIsShownAt."}}]},
            status=200,
        )

        source = EuropeanaSource()
        with patch.dict("os.environ", {"EUROPEANA_API_KEY": "test_key"}):
            result = source.search(keywords=["test"])

        assert len(result.documents) == 1
        assert result.documents[0].source_url == "https://example.europeana.eu/item/456"


class TestDetectLanguage:
    """Tests for _detect_language helper — returns ISO 639-1 str."""

    def test_detect_french(self):
        assert _detect_language({"language": ["fr"]}) == "fr"

    def test_detect_german(self):
        assert _detect_language({"language": ["de"]}) == "de"

    def test_default_to_english(self):
        assert _detect_language({"language": []}) == "en"

    def test_unknown_language_passes_through(self):
        """未知の言語コードもそのまま ISO 639-1 として返す。"""
        assert _detect_language({"language": ["pl"]}) == "pl"

    def test_italian_detected(self):
        assert _detect_language({"language": ["it"]}) == "it"

    def test_string_language(self):
        assert _detect_language({"language": "nl"}) == "nl"

    def test_no_language_field(self):
        assert _detect_language({}) == "en"


class TestExtractLocation:
    """Tests for _extract_location helper."""

    def test_from_country(self):
        assert _extract_location({"country": ["France"]}) == "France"

    def test_from_place_label(self):
        result = _extract_location({"edmPlaceLabelLangAware": {"en": ["Paris"]}})
        assert result == "Paris"

    def test_default_europe(self):
        assert _extract_location({}) == "Europe"


class TestEmptyDates:
    """空文字日付のテスト。"""

    @responses.activate
    def test_empty_dates_omits_date_filter(self):
        """date_start/date_end が空文字の場合、YEAR フィルタが省略される。"""
        mock_response = {"success": True, "totalResults": 0, "items": []}
        responses.add(responses.GET, BASE_URL, json=mock_response, status=200)

        source = EuropeanaSource()
        with patch.dict("os.environ", {"EUROPEANA_API_KEY": "test_key"}):
            source.search(keywords=["test"], date_start="", date_end="")

        request = responses.calls[0].request
        assert "YEAR" not in request.url


class TestSupportedLanguages:
    """EuropeanaSource.supported_languages のテスト。"""

    def test_en_in_supported_languages(self):
        """英語が supported_languages に含まれる。"""
        source = EuropeanaSource()
        assert "en" in source.supported_languages

    def test_all_expected_languages(self):
        """全6言語が supported_languages に含まれる。"""
        source = EuropeanaSource()
        expected = {"en", "de", "es", "fr", "nl", "pt"}
        assert source.supported_languages == expected


class TestParseYear:
    """Tests for ArchiveSource.parse_year() (旧 _parse_year)。"""

    def test_parse_year(self):
        assert ArchiveSource.parse_year("1850") == "1850-01-01"

    def test_parse_empty(self):
        assert ArchiveSource.parse_year("") is None

    def test_parse_full_date(self):
        assert ArchiveSource.parse_year("1850-03-15") == "1850-01-01"


class TestExtractRecordIds:
    """_extract_record_ids のテスト。"""

    def test_valid_id(self):
        """正常な Europeana ID を datasetId / localId に分解する。"""
        ds, loc = _extract_record_ids("/2020601/abc_def")
        assert ds == "2020601"
        assert loc == "abc_def"

    def test_empty_string(self):
        """空文字列は (None, None) を返す。"""
        assert _extract_record_ids("") == (None, None)

    def test_no_leading_slash(self):
        """先頭 / がない場合は (None, None) を返す。"""
        assert _extract_record_ids("2020601/abc") == (None, None)

    def test_single_segment(self):
        """スラッシュが1つだけで localId がない場合は (None, None) を返す。"""
        assert _extract_record_ids("/2020601") == (None, None)

    def test_complex_local_id(self):
        """localId にスラッシュを含む場合でも正しく分解する。"""
        ds, loc = _extract_record_ids("/123/https___example.com_path")
        assert ds == "123"
        assert loc == "https___example.com_path"


class TestParseAnnotationText:
    """_parse_annotation_text のテスト。"""

    def test_flat_items(self):
        """フラットな items からテキストを抽出する。"""
        data = {"items": [{"body": {"value": "First page text."}}]}
        assert _parse_annotation_text(data) == "First page text."

    def test_nested_items(self):
        """ネストされた AnnotationPage からテキストを抽出する。"""
        data = {
            "items": [
                {"items": [{"body": {"value": "Nested page text."}}]}
            ]
        }
        assert _parse_annotation_text(data) == "Nested page text."

    def test_multiple_items_joined(self):
        """複数のテキストが改行で結合される。"""
        data = {
            "items": [
                {"body": {"value": "Line one."}},
                {"body": {"value": "Line two."}},
            ]
        }
        result = _parse_annotation_text(data)
        assert "Line one." in result
        assert "Line two." in result
        assert "\n" in result

    def test_empty_items(self):
        """items が空の場合は None を返す。"""
        assert _parse_annotation_text({"items": []}) is None

    def test_no_items_key(self):
        """items キーがない場合は None を返す。"""
        assert _parse_annotation_text({}) is None

    def test_truncates_long_text(self):
        """5000文字を超えるテキストは切り詰める。"""
        data = {"items": [{"body": {"value": "A" * 6000}}]}
        result = _parse_annotation_text(data)
        assert len(result) == 5000


class TestFetchFulltext:
    """_fetch_fulltext のテスト。"""

    @responses.activate
    def test_returns_text(self):
        """正常なレスポンスでテキストを返す。"""
        responses.add(
            responses.GET,
            _FULLTEXT_URL.format(dataset_id="123", local_id="abc"),
            json={"items": [{"body": {"value": "Annotation text."}}]},
            status=200,
        )

        session = create_retry_session()
        result = _fetch_fulltext(session, "123", "abc", "test_key")

        assert result == "Annotation text."

    @responses.activate
    def test_returns_none_on_404(self):
        """404 の場合は None を返す。"""
        responses.add(
            responses.GET,
            _FULLTEXT_URL.format(dataset_id="123", local_id="missing"),
            status=404,
        )

        session = create_retry_session()
        result = _fetch_fulltext(session, "123", "missing", "test_key")

        assert result is None

    @responses.activate
    def test_returns_none_on_empty_annotation(self):
        """空の Annotation は None を返す。"""
        responses.add(
            responses.GET,
            _FULLTEXT_URL.format(dataset_id="123", local_id="empty"),
            json={"items": []},
            status=200,
        )

        session = create_retry_session()
        result = _fetch_fulltext(session, "123", "empty", "test_key")

        assert result is None


class TestEuropeanaFulltextFilter:
    """Europeana 全文フィルタリングテスト。"""

    @responses.activate
    def test_filters_docs_without_fulltext(self):
        """全文取得に失敗したドキュメントは除外される。"""
        mock_response = {
            "success": True,
            "totalResults": 2,
            "items": [
                {
                    "title": ["Has Fulltext"],
                    "guid": "https://www.europeana.eu/item/has/text",
                    "id": "/has/text",
                    "language": ["en"],
                },
                {
                    "title": ["No Fulltext"],
                    "guid": "https://www.europeana.eu/item/no/text",
                    "id": "/no/text",
                    "language": ["en"],
                },
            ],
        }
        responses.add(responses.GET, BASE_URL, json=mock_response, status=200)
        # 1件目: 全文あり
        responses.add(
            responses.GET,
            _FULLTEXT_URL.format(dataset_id="has", local_id="text"),
            json={"items": [{"body": {"value": "Fulltext here."}}]},
            status=200,
        )
        # 2件目: 404
        responses.add(
            responses.GET,
            _FULLTEXT_URL.format(dataset_id="no", local_id="text"),
            status=404,
        )

        source = EuropeanaSource()
        with patch.dict("os.environ", {"EUROPEANA_API_KEY": "test_key"}):
            result = source.search(keywords=["test"])

        assert len(result.documents) == 1
        assert result.documents[0].title == "Has Fulltext"
        assert result.documents[0].raw_text == "Fulltext here."

    @responses.activate
    def test_no_id_field_means_no_fulltext(self):
        """id フィールドがないアイテムは全文取得対象外 → 除外される。"""
        mock_response = {
            "success": True,
            "totalResults": 1,
            "items": [
                {
                    "title": ["No ID"],
                    "guid": "https://www.europeana.eu/item/test",
                    "language": ["en"],
                }
            ],
        }
        responses.add(responses.GET, BASE_URL, json=mock_response, status=200)

        source = EuropeanaSource()
        with patch.dict("os.environ", {"EUROPEANA_API_KEY": "test_key"}):
            result = source.search(keywords=["test"])

        assert len(result.documents) == 0
