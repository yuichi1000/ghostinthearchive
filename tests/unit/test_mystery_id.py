"""Unit tests for Mystery ID schema — validate and parse (v2 format)."""

import pytest

from mystery_agents.schemas.mystery_id import (
    REGION_CODES,
    ClassificationCode,
    parse_mystery_id,
    validate_mystery_id,
)


class TestValidateMysteryId:
    """validate_mystery_id() のテスト。"""

    def test_valid_v2_id(self):
        """正常な v2 形式の ID を受理する。"""
        assert validate_mystery_id("OCC-US-BOS-20260207143025")

    def test_valid_v2_with_various_classifications(self):
        """全分類コードで受理する。"""
        for code in ClassificationCode:
            assert validate_mystery_id(f"{code.value}-GB-LHR-20260301120000")

    def test_valid_v2_with_5_letter_region(self):
        """5文字の地域コードを受理する。"""
        assert validate_mystery_id("HIS-JP-KANSA-20260315090000")

    def test_valid_v2_with_4_letter_region(self):
        """4文字の地域コードを受理する。"""
        assert validate_mystery_id("FLK-DE-HAMB-20260315090000")

    def test_rejects_empty_string(self):
        assert not validate_mystery_id("")

    def test_rejects_too_few_parts(self):
        assert not validate_mystery_id("OCC-US-20260207143025")

    def test_rejects_too_many_parts(self):
        assert not validate_mystery_id("OCC-US-BOS-123-20260207143025")

    def test_rejects_lowercase_classification(self):
        assert not validate_mystery_id("occ-US-BOS-20260207143025")

    def test_rejects_lowercase_country(self):
        assert not validate_mystery_id("OCC-us-BOS-20260207143025")

    def test_rejects_lowercase_region(self):
        assert not validate_mystery_id("OCC-US-bos-20260207143025")

    def test_rejects_2_letter_region(self):
        """地域コードが2文字だと不正。"""
        assert not validate_mystery_id("OCC-US-BO-20260207143025")

    def test_rejects_6_letter_region(self):
        """地域コードが6文字だと不正。"""
        assert not validate_mystery_id("OCC-US-BOSTON-20260207143025")

    def test_rejects_numeric_region(self):
        """数字のみの地域コード（旧 v1 area code）は不正。"""
        assert not validate_mystery_id("OCC-MA-617-20260207143025")

    def test_rejects_short_timestamp(self):
        assert not validate_mystery_id("OCC-US-BOS-2026020714302")

    def test_rejects_long_timestamp(self):
        assert not validate_mystery_id("OCC-US-BOS-202602071430250")

    def test_rejects_non_digit_timestamp(self):
        assert not validate_mystery_id("OCC-US-BOS-2026020714302A")

    def test_rejects_1_letter_country(self):
        assert not validate_mystery_id("OCC-U-BOS-20260207143025")

    def test_rejects_3_letter_country(self):
        assert not validate_mystery_id("OCC-USA-BOS-20260207143025")


class TestParseMysteryId:
    """parse_mystery_id() のテスト。"""

    def test_parses_v2_id(self):
        """v2 ID を正しくパースする。"""
        result = parse_mystery_id("OCC-US-BOS-20260207143025")
        assert result == {
            "classification": "OCC",
            "country_code": "US",
            "region_code": "BOS",
            "timestamp": "20260207143025",
        }

    def test_parses_international_id(self):
        """国際的な ID を正しくパースする。"""
        result = parse_mystery_id("FLK-GB-EDI-20260301120000")
        assert result == {
            "classification": "FLK",
            "country_code": "GB",
            "region_code": "EDI",
            "timestamp": "20260301120000",
        }

    def test_returns_none_for_invalid(self):
        """不正な ID では None を返す。"""
        assert parse_mystery_id("invalid") is None

    def test_returns_none_for_empty(self):
        assert parse_mystery_id("") is None


class TestRegionCodes:
    """REGION_CODES 辞書のテスト。"""

    def test_us_cities_have_us_country_code(self):
        """米国都市は国コード US を持つ。"""
        us_cities = ["BOSTON", "NEW_YORK", "CHICAGO", "LOS_ANGELES"]
        for city in us_cities:
            country, _region = REGION_CODES[city]
            assert country == "US", f"{city} should have country_code US"

    def test_international_cities_exist(self):
        """主要な国際都市がエントリとして存在する。"""
        expected = ["LONDON", "BERLIN", "PARIS", "AMSTERDAM", "LISBON", "TOKYO"]
        for city in expected:
            assert city in REGION_CODES, f"{city} should be in REGION_CODES"

    def test_region_codes_are_3_to_5_chars(self):
        """全地域コードが3-5文字の大文字アルファベットであること。"""
        for city, (country, region) in REGION_CODES.items():
            assert 3 <= len(region) <= 5, f"{city}: region {region} length out of range"
            assert region.isalpha() and region.isupper(), f"{city}: region {region} not uppercase alpha"

    def test_country_codes_are_2_chars(self):
        """全国コードが2文字の大文字アルファベットであること。"""
        for city, (country, region) in REGION_CODES.items():
            assert len(country) == 2 and country.isupper(), f"{city}: country {country} not 2 uppercase"
