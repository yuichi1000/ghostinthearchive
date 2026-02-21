"""Unit tests for DigitalNZ API tool."""

import responses

from mystery_agents.tools.digitalnz import (
    BASE_URL,
    DigitalNZSource,
    _first_or_default,
    _parse_date,
)


# DigitalNZ Records API v3 のレスポンス（テスト用）
_SAMPLE_RESPONSE = {
    "search": {
        "result_count": 1542,
        "results": [
            {
                "title": "The Haunting of Dodd House",
                "description": "A mysterious series of events reported in the Otago Daily Times.",
                "date": ["1886-12-07T00:00:00.000Z"],
                "landing_url": "https://paperspast.natlib.govt.nz/newspapers/ODT18861207.2.15",
                "content_partner": ["Otago Daily Times"],
                "subject": ["haunting", "ghosts", "Otago"],
                "placename": ["Dunedin"],
                "collection_title": ["Papers Past"],
            }
        ],
    }
}

_EMPTY_RESPONSE = {"search": {"result_count": 0, "results": []}}

_NULL_DESCRIPTION_RESPONSE = {
    "search": {
        "result_count": 1,
        "results": [
            {
                "title": "Maori Legends of the Supernatural",
                "description": None,
                "date": ["1902-01-15T00:00:00.000Z"],
                "landing_url": "https://digitalnz.org/records/12345",
                "content_partner": ["Auckland Museum"],
                "subject": ["Maori", "legends"],
                "placename": [],
                "collection_title": ["Museum Collections"],
            }
        ],
    }
}

_NO_PLACENAME_RESPONSE = {
    "search": {
        "result_count": 1,
        "results": [
            {
                "title": "Canterbury Ghost Stories",
                "description": "Collection of ghost stories from Canterbury region.",
                "date": ["1895-03-20T00:00:00.000Z"],
                "landing_url": "https://digitalnz.org/records/67890",
                "content_partner": ["Canterbury Museum"],
                "subject": ["ghost", "Canterbury"],
                "placename": [],
                "collection_title": [],
            }
        ],
    }
}

_NO_LANDING_URL_RESPONSE = {
    "search": {
        "result_count": 2,
        "results": [
            {
                "title": "Record Without URL",
                "description": "This record has no landing_url.",
                "date": ["1890-01-01T00:00:00.000Z"],
                "landing_url": "",
                "content_partner": ["Unknown"],
                "subject": [],
                "placename": [],
                "collection_title": [],
            },
            {
                "title": "Record With URL",
                "description": "This record has a landing_url.",
                "date": ["1890-06-15T00:00:00.000Z"],
                "landing_url": "https://digitalnz.org/records/99999",
                "content_partner": ["National Library"],
                "subject": ["ghost"],
                "placename": ["Wellington"],
                "collection_title": [],
            },
        ],
    }
}

_MULTI_RESULT_RESPONSE = {
    "search": {
        "result_count": 3,
        "results": [
            {
                "title": "Phantom Ship of Cook Strait",
                "description": "Reports of a phantom ship sighted near Cook Strait.",
                "date": ["1870-08-10T00:00:00.000Z"],
                "landing_url": "https://paperspast.natlib.govt.nz/newspapers/EP18700810.2.8",
                "content_partner": ["Evening Post"],
                "subject": ["phantom", "ship", "maritime"],
                "placename": ["Wellington"],
                "collection_title": ["Papers Past"],
            },
            {
                "title": "The Ghost of Government House",
                "description": "A well-known ghost story from colonial Auckland.",
                "date": ["1882-05-22T00:00:00.000Z"],
                "landing_url": "https://digitalnz.org/records/44444",
                "content_partner": ["Auckland Libraries"],
                "subject": ["ghost", "colonial", "Auckland"],
                "placename": ["Auckland"],
                "collection_title": ["Heritage Collections"],
            },
            {
                "title": "Maori Taniwha Legends",
                "description": "Taniwha legends from the Waikato region.",
                "date": ["1910-11-30T00:00:00.000Z"],
                "landing_url": "https://digitalnz.org/records/55555",
                "content_partner": ["Waikato Museum"],
                "subject": ["taniwha", "Maori", "legends", "folklore"],
                "placename": ["Waikato"],
                "collection_title": ["Oral Histories"],
            },
        ],
    }
}


class TestDigitalNZSource:
    """Tests for DigitalNZSource."""

    def test_no_api_key_needed(self):
        """API キー不要でエラーにならない。"""
        source = DigitalNZSource()
        assert source.env_var_key is None
        assert source._check_api_key() is None

    def test_source_metadata(self):
        """ソースメタデータが正しい。"""
        source = DigitalNZSource()
        assert source.source_key == "digitalnz"
        assert source.source_name == "DigitalNZ (Digital New Zealand)"
        assert source.supported_languages == {"en"}
        assert source.is_newspaper_source is False
        assert source.env_var_key is None
        assert source.min_request_delay == 1.0
        assert "digitalnz.org" in source.expected_domains
        assert "paperspast.natlib.govt.nz" in source.expected_domains

    def test_empty_keywords(self):
        """空のキーワードリストでエラーを返す。"""
        source = DigitalNZSource()
        result = source.search(keywords=[])
        assert result.error == "No keywords provided"

    @responses.activate
    def test_successful_search(self):
        """正常な JSON レスポンスからドキュメントを生成する。"""
        responses.add(
            responses.GET, BASE_URL, json=_SAMPLE_RESPONSE, status=200
        )

        source = DigitalNZSource()
        result = source.search(
            keywords=["haunting", "ghost"], date_start="1800", date_end="1900"
        )

        assert result.error is None
        assert result.total_hits == 1542
        assert len(result.documents) == 1

        doc = result.documents[0]
        assert doc.title == "The Haunting of Dodd House"
        assert doc.source_type == "digitalnz"
        assert doc.language == "en"
        assert doc.location == "Dunedin"
        assert doc.source_url == "https://paperspast.natlib.govt.nz/newspapers/ODT18861207.2.15"
        assert "haunting" in doc.keywords_matched
        assert doc.record_group == "Papers Past"

    @responses.activate
    def test_year_filter_params(self):
        """and[year] パラメータがリクエストに含まれる。"""
        responses.add(
            responses.GET, BASE_URL, json=_EMPTY_RESPONSE, status=200
        )

        source = DigitalNZSource()
        source.search(keywords=["ghost"], date_start="1800", date_end="1900")

        request = responses.calls[0].request
        # URL エンコードされた and[year] パラメータを確認
        assert "and%5Byear%5D" in request.url or "and[year]" in request.url

    @responses.activate
    def test_api_error_handling(self):
        """HTTP エラー時はエラーメッセージを返す。"""
        responses.add(
            responses.GET, BASE_URL, body="Server Error", status=500
        )

        source = DigitalNZSource()
        result = source.search(keywords=["ghost"])

        assert result.error is not None
        assert "API error" in result.error
        assert result.documents == []

    @responses.activate
    def test_empty_results(self):
        """0件結果。"""
        responses.add(
            responses.GET, BASE_URL, json=_EMPTY_RESPONSE, status=200
        )

        source = DigitalNZSource()
        result = source.search(keywords=["nonexistent"])

        assert result.total_hits == 0
        assert result.documents == []
        assert result.error is None

    @responses.activate
    def test_null_description_fallback(self):
        """description が null の場合は title にフォールバックする。"""
        responses.add(
            responses.GET, BASE_URL, json=_NULL_DESCRIPTION_RESPONSE, status=200
        )

        source = DigitalNZSource()
        result = source.search(keywords=["Maori"])

        doc = result.documents[0]
        assert doc.summary == "Maori Legends of the Supernatural"

    @responses.activate
    def test_empty_placename_fallback_to_content_partner(self):
        """placename が空の場合は content_partner にフォールバックする。"""
        responses.add(
            responses.GET, BASE_URL, json=_NO_PLACENAME_RESPONSE, status=200
        )

        source = DigitalNZSource()
        result = source.search(keywords=["ghost"])

        doc = result.documents[0]
        assert doc.location == "Canterbury Museum"

    @responses.activate
    def test_collection_title_to_record_group(self):
        """collection_title が record_group にマッピングされる。"""
        responses.add(
            responses.GET, BASE_URL, json=_SAMPLE_RESPONSE, status=200
        )

        source = DigitalNZSource()
        result = source.search(keywords=["haunting"])

        doc = result.documents[0]
        assert doc.record_group == "Papers Past"

    @responses.activate
    def test_empty_collection_title(self):
        """collection_title が空の場合は record_group が None。"""
        responses.add(
            responses.GET, BASE_URL, json=_NO_PLACENAME_RESPONSE, status=200
        )

        source = DigitalNZSource()
        result = source.search(keywords=["ghost"])

        doc = result.documents[0]
        assert doc.record_group is None

    @responses.activate
    def test_skip_records_without_landing_url(self):
        """landing_url のないレコードはスキップされる。"""
        responses.add(
            responses.GET, BASE_URL, json=_NO_LANDING_URL_RESPONSE, status=200
        )

        source = DigitalNZSource()
        result = source.search(keywords=["ghost"])

        # landing_url がある1件のみ
        assert len(result.documents) == 1
        assert result.documents[0].title == "Record With URL"

    @responses.activate
    def test_subject_keyword_matching(self):
        """subject フィールドもキーワードマッチの対象になる。"""
        responses.add(
            responses.GET, BASE_URL, json=_MULTI_RESULT_RESPONSE, status=200
        )

        source = DigitalNZSource()
        result = source.search(keywords=["folklore"])

        # "folklore" は 3件目の subject にのみ含まれる
        taniwha_doc = result.documents[2]
        assert "folklore" in taniwha_doc.keywords_matched

    @responses.activate
    def test_date_parsing_iso8601_array(self):
        """ISO 8601 配列形式の日付が正しくパースされる。"""
        responses.add(
            responses.GET, BASE_URL, json=_SAMPLE_RESPONSE, status=200
        )

        source = DigitalNZSource()
        result = source.search(keywords=["haunting"])

        doc = result.documents[0]
        assert doc.date == "1886-01-01"

    @responses.activate
    def test_multiple_results(self):
        """複数件の結果が正しくパースされる。"""
        responses.add(
            responses.GET, BASE_URL, json=_MULTI_RESULT_RESPONSE, status=200
        )

        source = DigitalNZSource()
        result = source.search(keywords=["ghost", "phantom"])

        assert len(result.documents) == 3
        assert result.total_hits == 3

    @responses.activate
    def test_null_description_keyword_match_in_location(self):
        """description が null でも placename が空でも content_partner で location を取得。"""
        responses.add(
            responses.GET, BASE_URL, json=_NULL_DESCRIPTION_RESPONSE, status=200
        )

        source = DigitalNZSource()
        result = source.search(keywords=["legends"])

        doc = result.documents[0]
        # content_partner にフォールバック
        assert doc.location == "Auckland Museum"
        # "legends" は subject にも title にも含まれる
        assert "legends" in doc.keywords_matched

    @responses.activate
    def test_fields_parameter_sent(self):
        """fields パラメータが API リクエストに含まれる（帯域節約）。"""
        responses.add(
            responses.GET, BASE_URL, json=_EMPTY_RESPONSE, status=200
        )

        source = DigitalNZSource()
        source.search(keywords=["test"])

        request = responses.calls[0].request
        assert "fields=" in request.url


class TestFirstOrDefault:
    """Tests for _first_or_default helper."""

    def test_list_with_values(self):
        assert _first_or_default(["first", "second"]) == "first"

    def test_empty_list(self):
        assert _first_or_default([]) == ""

    def test_empty_list_with_default(self):
        assert _first_or_default([], "fallback") == "fallback"

    def test_string_value(self):
        assert _first_or_default("direct") == "direct"

    def test_none_value(self):
        assert _first_or_default(None) == ""

    def test_integer_value(self):
        assert _first_or_default(42) == ""


class TestParseDate:
    """Tests for _parse_date helper."""

    def test_iso8601_array(self):
        assert _parse_date(["1886-12-07T00:00:00.000Z"]) == "1886-12-07"

    def test_empty_array(self):
        assert _parse_date([]) == ""

    def test_none_value(self):
        assert _parse_date(None) == ""

    def test_string_date(self):
        assert _parse_date("1900-05-15") == "1900-05-15"

    def test_short_date(self):
        assert _parse_date(["1900"]) == "1900"
