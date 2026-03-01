"""Unit tests for curator_agents/probe.py.

API プローブの並列実行、全文取得可否判定、エラー時のグレースフルデグラデーションをテストする。
"""

from unittest.mock import MagicMock, patch

from curator_agents.probe import probe_all_themes, probe_theme


def _make_mock_doc(raw_text: str | None = None):
    """テスト用のモックドキュメントを生成する。"""
    doc = MagicMock()
    doc.raw_text = raw_text
    return doc


def _make_mock_source(
    source_key: str,
    documents: list | None = None,
    raise_error: bool = False,
):
    """テスト用のモックソースを生成する。"""
    source = MagicMock()
    source.source_key = source_key
    if raise_error:
        source.search.side_effect = Exception("API error")
    else:
        result = MagicMock()
        result.documents = documents if documents is not None else []
        result.total_hits = len(result.documents)
        source.search.return_value = result
    return source


class TestProbeTheme:
    """probe_theme() のテスト。"""

    def test_detects_content_by_api_group(self):
        """raw_text を持つドキュメントがある API グループは True になること。"""
        mock_sources = {
            "nypl": _make_mock_source("nypl", documents=[_make_mock_doc("Full text here")]),
            "chronicling_america": _make_mock_source("chronicling_america", documents=[_make_mock_doc("More text")]),
            "europeana": _make_mock_source("europeana", documents=[_make_mock_doc("European text")]),
            "internet_archive": _make_mock_source("internet_archive", documents=[]),
        }
        with patch("curator_agents.probe.get_all_sources", return_value=mock_sources):
            result = probe_theme(["Boston", "1850"])

        # nypl + chronicling_america → us_archives に集約（いずれかが True なら True）
        assert result["us_archives"] is True
        assert result["europeana"] is True
        # internet_archive はドキュメントなし → False
        assert result["internet_archive"] is False

    def test_false_when_no_raw_text(self):
        """ドキュメントはあるが raw_text が None の場合は False になること。"""
        mock_sources = {
            "europeana": _make_mock_source("europeana", documents=[_make_mock_doc(None)]),
        }
        with patch("curator_agents.probe.get_all_sources", return_value=mock_sources):
            result = probe_theme(["test"])

        assert result["europeana"] is False

    def test_true_when_any_source_in_group_has_content(self):
        """同一グループの複数ソースのうち1つでも raw_text があれば True になること。"""
        mock_sources = {
            "nypl": _make_mock_source("nypl", documents=[]),
            "chronicling_america": _make_mock_source("chronicling_america", documents=[_make_mock_doc("Text")]),
        }
        with patch("curator_agents.probe.get_all_sources", return_value=mock_sources):
            result = probe_theme(["test"])

        assert result["us_archives"] is True

    def test_calls_search_with_max_results_1(self):
        """search を max_results=1 で呼ぶこと。"""
        mock_source = _make_mock_source("nypl", documents=[_make_mock_doc("text")])
        mock_sources = {"nypl": mock_source}
        with patch("curator_agents.probe.get_all_sources", return_value=mock_sources):
            probe_theme(["test"])

        mock_source.search.assert_called_once_with(["test"], max_results=1)

    def test_graceful_on_api_error(self):
        """API エラー時は該当ソースをスキップし、他のソースの結果を返すこと。"""
        mock_sources = {
            "nypl": _make_mock_source("nypl", raise_error=True),
            "europeana": _make_mock_source("europeana", documents=[_make_mock_doc("text")]),
        }
        with patch("curator_agents.probe.get_all_sources", return_value=mock_sources):
            result = probe_theme(["test"])

        # nypl はエラーで結果なし、europeana は正常
        assert "us_archives" not in result
        assert result["europeana"] is True

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
            "nypl": _make_mock_source("nypl", documents=[_make_mock_doc("text")]),
            "chronicling_america": _make_mock_source("chronicling_america", documents=[_make_mock_doc("text")]),
            "internet_archive": _make_mock_source("internet_archive", documents=[_make_mock_doc("text")]),
            "trove": _make_mock_source("trove", documents=[_make_mock_doc("text")]),
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
            "nypl": _make_mock_source("nypl", documents=[_make_mock_doc("text")]),
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
