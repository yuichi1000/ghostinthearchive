"""Unit tests for shared/api_coverage.py.

API カバレッジメタデータ、プロンプトテーブル生成、スコア算出ロジックをテストする。
"""

from curator_agents.probe import ProbeResult
from shared.api_coverage import (
    API_COVERAGE_REGISTRY,
    VALID_API_KEYS,
    ApiCoverage,
    build_coverage_prompt_table,
    calculate_coverage_score,
)


class TestApiCoverageRegistry:
    """API_COVERAGE_REGISTRY の定義検証。"""

    def test_contains_all_expected_apis(self):
        """全 6 API グループが定義されていること。"""
        expected = {"us_archives", "europeana", "internet_archive", "ndl", "delpher", "trove"}
        assert set(API_COVERAGE_REGISTRY.keys()) == expected

    def test_valid_api_keys_matches_registry(self):
        assert VALID_API_KEYS == frozenset(API_COVERAGE_REGISTRY.keys())

    def test_all_entries_are_api_coverage(self):
        for key, cov in API_COVERAGE_REGISTRY.items():
            assert isinstance(cov, ApiCoverage)
            assert cov.api_key == key

    def test_all_entries_have_source_keys(self):
        """各 API グループに source_keys が1つ以上あること。"""
        for key, cov in API_COVERAGE_REGISTRY.items():
            assert len(cov.source_keys) >= 1, f"{key} に source_keys がない"

    def test_fulltext_reliability_valid_values(self):
        """fulltext_reliability が HIGH/MEDIUM/LOW のいずれかであること。"""
        for key, cov in API_COVERAGE_REGISTRY.items():
            assert cov.fulltext_reliability in ("HIGH", "MEDIUM", "LOW"), \
                f"{key} の fulltext_reliability が不正: {cov.fulltext_reliability}"

    def test_us_archives_has_two_source_keys(self):
        """us_archives は nypl と chronicling_america の2つを持つこと。"""
        cov = API_COVERAGE_REGISTRY["us_archives"]
        assert set(cov.source_keys) == {"nypl", "chronicling_america"}


class TestBuildCoveragePromptTable:
    """build_coverage_prompt_table() のテスト。"""

    def test_contains_all_api_names(self):
        table = build_coverage_prompt_table()
        for cov in API_COVERAGE_REGISTRY.values():
            assert cov.display_name in table

    def test_contains_regions(self):
        table = build_coverage_prompt_table()
        assert "United States" in table
        assert "Japan" in table
        assert "Australia" in table

    def test_contains_fulltext_reliability(self):
        table = build_coverage_prompt_table()
        assert "HIGH" in table
        assert "MEDIUM" in table
        assert "LOW" in table

    def test_is_markdown_table(self):
        """マークダウンテーブル形式であること（ヘッダ + セパレータ + データ行）。"""
        table = build_coverage_prompt_table()
        lines = table.strip().split("\n")
        assert lines[0].startswith("|")
        assert "---" in lines[1]
        # データ行 = 全 API 数
        assert len(lines) == 2 + len(API_COVERAGE_REGISTRY)


class TestCalculateCoverageScore:
    """calculate_coverage_score() のスコア算出ロジックテスト。"""

    def test_high_score_three_apis_with_high_reliability(self):
        """3+ API で全文取得可能、うち 1+ が HIGH → HIGH。"""
        probe = {
            "us_archives": ProbeResult(has_content=True, total_hits=10),
            "internet_archive": ProbeResult(has_content=True, total_hits=5),
            "trove": ProbeResult(has_content=True, total_hits=3),
        }
        score, apis = calculate_coverage_score(probe)
        assert score == "HIGH"
        assert set(apis) == {"us_archives", "internet_archive", "trove"}

    def test_medium_score_two_apis(self):
        """2 API で全文取得可能 → MEDIUM。"""
        probe = {
            "europeana": ProbeResult(has_content=True, total_hits=5),
            "ndl": ProbeResult(has_content=True, total_hits=3),
        }
        score, apis = calculate_coverage_score(probe)
        assert score == "MEDIUM"
        assert set(apis) == {"europeana", "ndl"}

    def test_high_score_three_apis_with_delpher(self):
        """3 API で全文取得可能、delpher(HIGH) 含む → HIGH。"""
        probe = {
            "europeana": ProbeResult(has_content=True, total_hits=5),
            "ndl": ProbeResult(has_content=True, total_hits=3),
            "delpher": ProbeResult(has_content=True, total_hits=10),
        }
        score, apis = calculate_coverage_score(probe)
        assert score == "HIGH"

    def test_high_score_boosted_by_deep_hits(self):
        """2 API + HIGH reliability + total_hits>=50 → HIGH に昇格。"""
        probe = {
            "us_archives": ProbeResult(has_content=True, total_hits=120),
            "internet_archive": ProbeResult(has_content=True, total_hits=50),
        }
        score, apis = calculate_coverage_score(probe)
        assert score == "HIGH"
        assert set(apis) == {"us_archives", "internet_archive"}

    def test_medium_two_apis_without_deep_hits(self):
        """2 API + HIGH reliability だが total_hits<50 → MEDIUM のまま。"""
        probe = {
            "us_archives": ProbeResult(has_content=True, total_hits=10),
            "internet_archive": ProbeResult(has_content=True, total_hits=5),
        }
        score, apis = calculate_coverage_score(probe)
        assert score == "MEDIUM"

    def test_low_score_single_api(self):
        """1 API のみ全文取得可能 → LOW。"""
        probe = {"ndl": ProbeResult(has_content=True, total_hits=5)}
        score, apis = calculate_coverage_score(probe)
        assert score == "LOW"

    def test_low_score_no_hits(self):
        """全 API で全文取得不可 → LOW。"""
        probe = {
            "us_archives": ProbeResult(has_content=False, total_hits=0),
            "europeana": ProbeResult(has_content=False, total_hits=0),
        }
        score, apis = calculate_coverage_score(probe)
        assert score == "LOW"
        assert apis == []

    def test_low_score_empty_probe(self):
        """空の probe_results → LOW。"""
        score, apis = calculate_coverage_score({})
        assert score == "LOW"
        assert apis == []

    def test_backward_compat_bool_values(self):
        """dict[str, bool] でも動作すること（後方互換）。"""
        probe = {"us_archives": True, "internet_archive": True, "trove": True}
        score, apis = calculate_coverage_score(probe)
        assert score == "HIGH"
        assert set(apis) == {"us_archives", "internet_archive", "trove"}

    def test_unknown_api_key_ignored_for_reliability_check(self):
        """未知の API キーは信頼度チェックで無視される。"""
        probe = {
            "unknown_api_1": ProbeResult(has_content=True, total_hits=5),
            "unknown_api_2": ProbeResult(has_content=True, total_hits=5),
            "unknown_api_3": ProbeResult(has_content=True, total_hits=5),
        }
        score, apis = calculate_coverage_score(probe)
        # 3 API で全文取得可能だが全て未知 → HIGH reliability なし → MEDIUM
        assert score == "MEDIUM"
