"""Tests for Librarian search metrics extraction and Firestore persistence."""

from unittest.mock import MagicMock, patch

from shared.search_metrics import (
    _extract_from_single_result,
    extract_search_metrics,
    save_search_metrics,
)


class TestExtractFromSingleResult:
    """_extract_from_single_result のテスト。"""

    def test_newspaper_format(self):
        """search_newspapers 形式の結果を正しくパースする。"""
        result = {
            "source": "chronicling_america",
            "total_hits": 50,
            "documents_returned": 8,
        }
        extracted = _extract_from_single_result(result)

        assert extracted["per_api"] == {
            "chronicling_america": {"total_hits": 50, "documents_returned": 8},
        }
        assert extracted["errors"] == {}
        assert extracted["fallback_used"] is False

    def test_archive_format(self):
        """search_archives 形式の結果を正しくパースする。"""
        result = {
            "sources_searched": {
                "loc": {"total_hits": 150, "documents_returned": 5},
                "internet_archive": {"total_hits": 30, "documents_returned": 3},
            },
        }
        extracted = _extract_from_single_result(result)

        assert extracted["per_api"]["loc"] == {"total_hits": 150, "documents_returned": 5}
        assert extracted["per_api"]["internet_archive"] == {"total_hits": 30, "documents_returned": 3}

    def test_error_extraction(self):
        """エラー情報を正しく抽出する。"""
        result = {
            "source": "chronicling_america",
            "total_hits": 0,
            "documents_returned": 0,
            "error": "API timeout",
        }
        extracted = _extract_from_single_result(result)

        assert extracted["errors"] == {"chronicling_america": "API timeout"}

    def test_archive_errors(self):
        """search_archives 形式のエラー情報を抽出する。"""
        result = {
            "sources_searched": {
                "loc": {"total_hits": 10, "documents_returned": 2},
            },
            "errors": {"internet_archive": "API key not set"},
        }
        extracted = _extract_from_single_result(result)

        assert extracted["errors"] == {"internet_archive": "API key not set"}

    def test_fallback_used(self):
        """fallback_used フラグを検出する。"""
        result = {
            "source": "chronicling_america",
            "total_hits": 5,
            "documents_returned": 5,
            "fallback_used": True,
        }
        extracted = _extract_from_single_result(result)

        assert extracted["fallback_used"] is True

    def test_empty_result(self):
        """空の結果を安全にパースする。"""
        extracted = _extract_from_single_result({})

        assert extracted["per_api"] == {}
        assert extracted["errors"] == {}
        assert extracted["fallback_used"] is False

    def test_source_none_is_ignored(self):
        """source が "none" の場合は無視する。"""
        result = {"source": "none", "total_hits": 0, "documents_returned": 0}
        extracted = _extract_from_single_result(result)

        assert extracted["per_api"] == {}


class TestExtractSearchMetrics:
    """extract_search_metrics のテスト。"""

    def test_empty_state_returns_none(self):
        """セッション状態が空なら None を返す。"""
        assert extract_search_metrics({}) is None

    def test_no_raw_search_results_returns_none(self):
        """raw_search_results キーがなければ None を返す。"""
        state = {"creative_content": "some content"}
        assert extract_search_metrics(state) is None

    def test_single_language(self):
        """単一言語の検索結果を正しく集約する。"""
        state = {
            "raw_search_results_en": [
                {
                    "sources_searched": {
                        "loc": {"total_hits": 150, "documents_returned": 5},
                        "internet_archive": {"total_hits": 30, "documents_returned": 3},
                    },
                },
            ],
        }
        metrics = extract_search_metrics(state)

        assert metrics is not None
        assert metrics["languages"] == ["en"]
        assert metrics["total_documents"] == 8
        assert metrics["by_language"]["en"]["loc"] == {"total_hits": 150, "documents_returned": 5}
        assert metrics["by_api"]["loc"] == {"total_hits": 150, "documents_returned": 5}
        assert metrics["by_api"]["internet_archive"] == {"total_hits": 30, "documents_returned": 3}

    def test_multiple_languages(self):
        """複数言語の検索結果を by_language と by_api に正しく集約する。"""
        state = {
            "raw_search_results_en": [
                {
                    "sources_searched": {
                        "loc": {"total_hits": 100, "documents_returned": 5},
                    },
                },
            ],
            "raw_search_results_de": [
                {
                    "sources_searched": {
                        "trove": {"total_hits": 12, "documents_returned": 7},
                        "europeana": {"total_hits": 8, "documents_returned": 5},
                    },
                },
            ],
        }
        metrics = extract_search_metrics(state)

        assert metrics is not None
        assert sorted(metrics["languages"]) == ["de", "en"]
        assert metrics["total_documents"] == 17

        # by_language
        assert "en" in metrics["by_language"]
        assert "de" in metrics["by_language"]
        assert metrics["by_language"]["en"]["loc"]["documents_returned"] == 5
        assert metrics["by_language"]["de"]["trove"]["documents_returned"] == 7

        # by_api（全言語横断集約）
        assert metrics["by_api"]["loc"]["total_hits"] == 100
        assert metrics["by_api"]["trove"]["total_hits"] == 12
        assert metrics["by_api"]["europeana"]["total_hits"] == 8

    def test_base_key_as_newspapers(self):
        """ベースキー raw_search_results は "newspapers" ラベルで by_language に入る。"""
        state = {
            "raw_search_results": [
                {
                    "source": "chronicling_america",
                    "total_hits": 50,
                    "documents_returned": 8,
                },
            ],
        }
        metrics = extract_search_metrics(state)

        assert metrics is not None
        assert "newspapers" in metrics["by_language"]
        assert metrics["by_language"]["newspapers"]["chronicling_america"]["documents_returned"] == 8
        assert metrics["by_api"]["chronicling_america"]["total_hits"] == 50
        # ベースキーは languages リストに含まれない
        assert metrics["languages"] == []

    def test_by_api_cross_language_aggregation(self):
        """同じ API が複数言語で使われた場合、by_api では合算される。"""
        state = {
            "raw_search_results_en": [
                {
                    "sources_searched": {
                        "europeana": {"total_hits": 20, "documents_returned": 3},
                    },
                },
            ],
            "raw_search_results_de": [
                {
                    "sources_searched": {
                        "europeana": {"total_hits": 15, "documents_returned": 5},
                    },
                },
            ],
        }
        metrics = extract_search_metrics(state)

        assert metrics["by_api"]["europeana"] == {"total_hits": 35, "documents_returned": 8}
        # by_language では言語ごとの値
        assert metrics["by_language"]["en"]["europeana"]["total_hits"] == 20
        assert metrics["by_language"]["de"]["europeana"]["total_hits"] == 15

    def test_errors_collected(self):
        """エラー情報がメトリクスに含まれる。"""
        state = {
            "raw_search_results_en": [
                {
                    "sources_searched": {
                        "loc": {"total_hits": 10, "documents_returned": 2},
                    },
                    "errors": {"internet_archive": "API key not set"},
                },
            ],
        }
        metrics = extract_search_metrics(state)

        assert metrics["errors"] == {"internet_archive": "API key not set"}

    def test_fallback_used_flag(self):
        """fallback_used フラグがメトリクスに含まれる。"""
        state = {
            "raw_search_results_en": [
                {
                    "sources_searched": {
                        "loc": {"total_hits": 5, "documents_returned": 5},
                    },
                    "fallback_used": True,
                },
            ],
        }
        metrics = extract_search_metrics(state)

        assert metrics["fallback_used"] is True

    def test_non_dict_results_ignored(self):
        """リスト内の非 dict エントリは無視する。"""
        state = {
            "raw_search_results_en": [
                "invalid_entry",
                {
                    "sources_searched": {
                        "loc": {"total_hits": 10, "documents_returned": 2},
                    },
                },
            ],
        }
        metrics = extract_search_metrics(state)

        assert metrics is not None
        assert metrics["by_api"]["loc"]["documents_returned"] == 2


class TestSaveSearchMetrics:
    """save_search_metrics のテスト。"""

    def test_saves_to_firestore(self, mock_firestore_client):
        """pipeline_runs ドキュメントに search_metrics を書き込む。"""
        metrics = {
            "languages": ["en"],
            "total_documents": 8,
            "by_language": {"en": {"loc": {"total_hits": 150, "documents_returned": 5}}},
            "by_api": {"loc": {"total_hits": 150, "documents_returned": 5}},
        }

        with patch("shared.firestore.get_firestore_client", return_value=mock_firestore_client):
            save_search_metrics("run-123", metrics)

        mock_firestore_client.collection.assert_called_with("pipeline_runs")
        mock_firestore_client.collection().document.assert_called_with("run-123")
        mock_firestore_client.collection().document().update.assert_called_once()

        call_args = mock_firestore_client.collection().document().update.call_args
        data = call_args[0][0]
        assert data["search_metrics"] == metrics
        assert "updated_at" in data

    def test_none_metrics_returns_early(self):
        """metrics が None なら Firestore に書き込まない。"""
        with patch("shared.firestore.get_firestore_client") as mock_get:
            save_search_metrics("run-123", None)
            mock_get.assert_not_called()

    def test_none_run_id_returns_early(self):
        """run_id が None なら Firestore に書き込まない。"""
        with patch("shared.firestore.get_firestore_client") as mock_get:
            save_search_metrics(None, {"total_documents": 5})
            mock_get.assert_not_called()

    def test_does_not_raise_on_firestore_error(self):
        """Firestore エラー時に例外を投げない（非ブロッキング）。"""
        mock_client = MagicMock()
        mock_client.collection.side_effect = Exception("Firestore unavailable")

        with patch("shared.firestore.get_firestore_client", return_value=mock_client):
            # 例外が発生しないことを確認
            save_search_metrics("run-123", {"total_documents": 5})
