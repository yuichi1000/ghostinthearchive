"""Unit tests for curator_agents/probe.py.

API プローブの並列実行、ヒット集約、エラー時のグレースフルデグラデーションをテストする。
"""

from unittest.mock import MagicMock, patch

from curator_agents.probe import probe_all_themes, probe_theme


def _make_mock_source(source_key: str, total_hits: int = 0, raise_error: bool = False):
    """テスト用のモックソースを生成する。"""
    source = MagicMock()
    source.source_key = source_key
    if raise_error:
        source.search.side_effect = Exception("API error")
    else:
        result = MagicMock()
        result.total_hits = total_hits
        source.search.return_value = result
    return source


class TestProbeTheme:
    """probe_theme() のテスト。"""

    def test_aggregates_hits_by_api_group(self):
        """source_key レベルの結果を API グループレベルに集約すること。"""
        mock_sources = {
            "nypl": _make_mock_source("nypl", total_hits=5),
            "chronicling_america": _make_mock_source("chronicling_america", total_hits=3),
            "europeana": _make_mock_source("europeana", total_hits=2),
            "internet_archive": _make_mock_source("internet_archive", total_hits=0),
        }
        with patch("curator_agents.probe.get_all_sources", return_value=mock_sources):
            result = probe_theme(["Boston", "1850"])

        # nypl + chronicling_america → us_archives に集約
        assert result.get("us_archives", 0) == 8
        assert result.get("europeana", 0) == 2
        # internet_archive はヒット0だが結果には含まれる
        assert result.get("internet_archive", 0) == 0

    def test_calls_search_with_max_results_1(self):
        """search を max_results=1 で呼ぶこと。"""
        mock_source = _make_mock_source("nypl", total_hits=10)
        mock_sources = {"nypl": mock_source}
        with patch("curator_agents.probe.get_all_sources", return_value=mock_sources):
            probe_theme(["test"])

        mock_source.search.assert_called_once_with(["test"], max_results=1)

    def test_graceful_on_api_error(self):
        """API エラー時は該当ソースをスキップし、他のソースの結果を返すこと。"""
        mock_sources = {
            "nypl": _make_mock_source("nypl", raise_error=True),
            "europeana": _make_mock_source("europeana", total_hits=5),
        }
        with patch("curator_agents.probe.get_all_sources", return_value=mock_sources):
            result = probe_theme(["test"])

        # nypl はエラーで結果なし、europeana は正常
        assert "us_archives" not in result or result.get("us_archives", 0) == 0
        assert result.get("europeana", 0) == 5

    def test_empty_sources_returns_empty(self):
        """ソースが空の場合は空 dict を返すこと。"""
        with patch("curator_agents.probe.get_all_sources", return_value={}):
            result = probe_theme(["test"])
        assert result == {}


class TestProbeAllThemes:
    """probe_all_themes() のテスト。"""

    def test_adds_coverage_fields_to_themes(self):
        """各テーマに coverage_score, primary_apis, probe_hits が付与されること。"""
        themes = [
            {"theme": "Boston Harbor Ghosts", "description": "Test", "category": "OCC",
             "probe_keywords": ["Boston", "harbor", "ghost"]},
        ]
        mock_sources = {
            "nypl": _make_mock_source("nypl", total_hits=5),
            "chronicling_america": _make_mock_source("chronicling_america", total_hits=3),
            "internet_archive": _make_mock_source("internet_archive", total_hits=2),
            "trove": _make_mock_source("trove", total_hits=1),
        }
        with patch("curator_agents.probe.get_all_sources", return_value=mock_sources):
            result = probe_all_themes(themes)

        assert len(result) == 1
        assert result[0]["coverage_score"] in ("HIGH", "MEDIUM", "LOW")
        assert isinstance(result[0]["primary_apis"], list)
        assert isinstance(result[0]["probe_hits"], dict)

    def test_fallback_keywords_when_probe_keywords_missing(self):
        """probe_keywords が空の場合、テーマ文を分割してフォールバックすること。"""
        themes = [
            {"theme": "Boston Harbor Ghosts 1850", "description": "Test", "category": "OCC"},
        ]
        mock_sources = {
            "nypl": _make_mock_source("nypl", total_hits=1),
        }
        with patch("curator_agents.probe.get_all_sources", return_value=mock_sources) as _:
            probe_all_themes(themes)

        # search が呼ばれたキーワードがテーマの先頭5単語であること
        mock_sources["nypl"].search.assert_called_once()
        call_args = mock_sources["nypl"].search.call_args
        assert call_args[0][0] == ["Boston", "Harbor", "Ghosts", "1850"]

    def test_preserves_existing_theme_fields(self):
        """既存のテーマフィールド（theme, description, category）が保持されること。"""
        themes = [
            {"theme": "Test Theme", "description": "Desc", "category": "HIS",
             "probe_keywords": ["test"]},
        ]
        with patch("curator_agents.probe.get_all_sources", return_value={}):
            result = probe_all_themes(themes)

        assert result[0]["theme"] == "Test Theme"
        assert result[0]["description"] == "Desc"
        assert result[0]["category"] == "HIS"
