"""Unit tests for curator_agents/probe.py.

API プローブの並列実行、全文取得可否判定、エラー時のグレースフルデグラデーション、
ストップワード除去、ProbeResult をテストする。
"""

from unittest.mock import MagicMock, patch

from curator_agents.probe import (
    _extract_fallback_keywords,
    probe_all_themes,
    probe_theme,
)


def _make_mock_doc(raw_text: str | None = None):
    """テスト用のモックドキュメントを生成する。"""
    doc = MagicMock()
    doc.raw_text = raw_text
    return doc


def _make_mock_source(
    source_key: str,
    documents: list | None = None,
    raise_error: bool = False,
    total_hits: int | None = None,
):
    """テスト用のモックソースを生成する。"""
    source = MagicMock()
    source.source_key = source_key
    if raise_error:
        source.search.side_effect = Exception("API error")
    else:
        result = MagicMock()
        result.documents = documents if documents is not None else []
        result.total_hits = total_hits if total_hits is not None else len(result.documents)
        source.search.return_value = result
    return source


class TestExtractFallbackKeywords:
    """_extract_fallback_keywords() のテスト。"""

    def test_removes_stopwords(self):
        """ストップワードが除去されること。"""
        keywords = _extract_fallback_keywords("The ghost of the Boston Harbor in 1850")
        assert "The" not in keywords
        assert "the" not in keywords
        assert "of" not in keywords
        assert "in" not in keywords
        assert "ghost" in keywords
        assert "Boston" in keywords
        assert "Harbor" in keywords
        assert "1850" in keywords

    def test_limits_to_max_count(self):
        """max_count を超えるキーワードは返さないこと。"""
        keywords = _extract_fallback_keywords(
            "Boston Harbor Ghost Ship Mystery Legend", max_count=3
        )
        assert len(keywords) == 3

    def test_fallback_when_all_stopwords(self):
        """全単語がストップワードの場合は元テキストの先頭3単語にフォールバック。"""
        keywords = _extract_fallback_keywords("the of in on at")
        assert keywords == ["the", "of", "in"]

    def test_empty_string(self):
        """空文字列の場合は空リスト。"""
        keywords = _extract_fallback_keywords("")
        assert keywords == []


class TestProbeTheme:
    """probe_theme() のテスト。"""

    def test_detects_content_by_api_group(self):
        """raw_text を持つドキュメントがある API グループは has_content=True になること。"""
        mock_sources = {
            "nypl": _make_mock_source("nypl", documents=[_make_mock_doc("Full text here")]),
            "chronicling_america": _make_mock_source("chronicling_america", documents=[_make_mock_doc("More text")]),
            "europeana": _make_mock_source("europeana", documents=[_make_mock_doc("European text")]),
            "internet_archive": _make_mock_source("internet_archive", documents=[]),
        }
        with patch("curator_agents.probe.get_all_sources", return_value=mock_sources):
            result = probe_theme(["Boston", "1850"])

        # nypl + chronicling_america → us_archives に集約（いずれかが True なら True）
        assert result["us_archives"].has_content is True
        assert result["europeana"].has_content is True
        # internet_archive はドキュメントなし → False
        assert result["internet_archive"].has_content is False

    def test_false_when_no_raw_text(self):
        """ドキュメントはあるが raw_text が None の場合は has_content=False になること。"""
        mock_sources = {
            "europeana": _make_mock_source("europeana", documents=[_make_mock_doc(None)]),
        }
        with patch("curator_agents.probe.get_all_sources", return_value=mock_sources):
            result = probe_theme(["test"])

        assert result["europeana"].has_content is False

    def test_true_when_any_source_in_group_has_content(self):
        """同一グループの複数ソースのうち1つでも raw_text があれば has_content=True になること。"""
        mock_sources = {
            "nypl": _make_mock_source("nypl", documents=[]),
            "chronicling_america": _make_mock_source("chronicling_america", documents=[_make_mock_doc("Text")]),
        }
        with patch("curator_agents.probe.get_all_sources", return_value=mock_sources):
            result = probe_theme(["test"])

        assert result["us_archives"].has_content is True

    def test_calls_search_with_probe_depth(self):
        """search を max_results=3 で呼ぶこと。"""
        mock_source = _make_mock_source("nypl", documents=[_make_mock_doc("text")])
        mock_sources = {"nypl": mock_source}
        with patch("curator_agents.probe.get_all_sources", return_value=mock_sources):
            probe_theme(["test"])

        mock_source.search.assert_called_once_with(["test"], max_results=3)

    def test_content_detected_in_second_document(self):
        """1件目に raw_text がなくても2件目で検出されること。"""
        mock_sources = {
            "europeana": _make_mock_source(
                "europeana",
                documents=[_make_mock_doc(None), _make_mock_doc("Found text")],
            ),
        }
        with patch("curator_agents.probe.get_all_sources", return_value=mock_sources):
            result = probe_theme(["test"])

        assert result["europeana"].has_content is True

    def test_total_hits_captured(self):
        """ProbeResult に total_hits が含まれること。"""
        mock_sources = {
            "europeana": _make_mock_source(
                "europeana",
                documents=[_make_mock_doc("text")],
                total_hits=127,
            ),
        }
        with patch("curator_agents.probe.get_all_sources", return_value=mock_sources):
            result = probe_theme(["test"])

        assert result["europeana"].total_hits == 127

    def test_total_hits_accumulated_across_group(self):
        """同一グループ内で total_hits が合算されること。"""
        mock_sources = {
            "nypl": _make_mock_source("nypl", documents=[_make_mock_doc("text")], total_hits=50),
            "chronicling_america": _make_mock_source(
                "chronicling_america", documents=[_make_mock_doc("text")], total_hits=30
            ),
        }
        with patch("curator_agents.probe.get_all_sources", return_value=mock_sources):
            result = probe_theme(["test"])

        assert result["us_archives"].total_hits == 80
        assert result["us_archives"].has_content is True

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
        assert result["europeana"].has_content is True

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
        """probe_keywords が空の場合、ストップワード除去後のキーワードにフォールバックすること。"""
        themes = [
            {"theme": "The Ghost of the Boston Harbor", "description": "Test", "category": "OCC"},
        ]
        mock_sources = {
            "nypl": _make_mock_source("nypl", documents=[_make_mock_doc("text")]),
        }
        with patch("curator_agents.probe.get_all_sources", return_value=mock_sources) as _:
            probe_all_themes(themes)

        # ストップワード（The, of, the）が除去されていること
        mock_sources["nypl"].search.assert_called_once()
        call_args = mock_sources["nypl"].search.call_args
        assert call_args[0][0] == ["Ghost", "Boston", "Harbor"]

    def test_probe_result_serialized_in_theme(self):
        """probe_hits が dict 形式（has_content, total_hits）でシリアライズされること。"""
        themes = [
            {"theme": "Test Theme", "description": "Desc", "category": "HIS",
             "probe_keywords": ["test"]},
        ]
        mock_sources = {
            "europeana": _make_mock_source(
                "europeana", documents=[_make_mock_doc("text")], total_hits=42
            ),
        }
        with patch("curator_agents.probe.get_all_sources", return_value=mock_sources):
            result = probe_all_themes(themes)

        probe_hit = result[0]["probe_hits"]["europeana"]
        assert probe_hit == {"has_content": True, "total_hits": 42}

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
