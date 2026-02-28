"""Unit tests for mystery_agents/tools/librarian_tools.py"""

import json
import time
from unittest.mock import patch

from mystery_agents.tools.archive_source_base import ArchiveSearchResult
from mystery_agents.tools.librarian_tools import (
    _TOTAL_DOCS_CAP,
    search_archives,
    search_newspapers,
)
from mystery_agents.tools.search_orchestration import (
    _is_ascii_only,
    _log_keyword_language_mismatch,
    _rank_documents,
    _search_single_source,
)
from tests.fakes import make_archive_doc as _make_doc


def _make_mock_source(
    source_key="mock",
    source_name="Mock Source",
    docs=None,
    total_hits=0,
    error=None,
    supports_language_filter=False,
    supported_languages=None,
    delay=0,
):
    """テスト用のモック ArchiveSource を作成する。"""

    class MockSource:
        pass

    s = MockSource()
    s.source_key = source_key
    s.source_name = source_name
    s.supports_language_filter = supports_language_filter
    s.supported_languages = supported_languages or {"en"}

    def _search(**kwargs):
        if delay > 0:
            time.sleep(delay)
        return ArchiveSearchResult(
            documents=list(docs or []),
            total_hits=total_hits,
            error=error,
        )

    s.search = _search
    return s


class TestSearchNewspapersValidationFallback:
    """search_newspapers の validate_documents 例外時フォールバック"""

    @patch("mystery_agents.tools.librarian_tools.validate_documents")
    @patch("mystery_agents.tools.librarian_tools.search_chronicling_america")
    def test_validate_documents_exception_preserves_all_docs(
        self, mock_search, mock_validate
    ):
        """validate_documents が例外を投げても全ドキュメントが保持される。"""
        doc = _make_doc()
        mock_search.return_value = {
            "total_hits": 1,
            "documents": [doc],
            "error": None,
        }
        mock_validate.side_effect = RuntimeError("unexpected error in validation")

        result_json = search_newspapers(keywords="test keyword")
        result = json.loads(result_json)

        assert result["documents_returned"] == 1
        assert result["documents"][0]["title"] == "Test Doc"
        # リンク検証はスキップされる
        assert result["link_validation"]["total_checked"] == 0


class TestSearchArchivesValidationFallback:
    """search_archives の validate_documents 例外時フォールバック"""

    @patch("mystery_agents.tools.librarian_tools.validate_documents")
    @patch("mystery_agents.tools.librarian_tools.get_all_sources")
    def test_validate_documents_exception_preserves_all_docs(
        self, mock_get_all, mock_validate
    ):
        """validate_documents が例外を投げても全ドキュメントが保持される。"""
        doc = _make_doc()
        mock_source = _make_mock_source(
            source_key="loc",
            source_name="LOC Digital Collections",
            docs=[doc],
            total_hits=1,
        )
        mock_get_all.return_value = {"loc": mock_source}
        mock_validate.side_effect = RuntimeError("unexpected error in validation")

        result_json = search_archives(keywords="test keyword", sources="loc")
        result = json.loads(result_json)

        assert result["total_documents"] == 1
        assert result["documents"][0]["title"] == "Test Doc"
        assert result["link_validation"]["total_checked"] == 0


class TestSearchAndCollectFallback:
    """_search_and_collect 内部関数の例外時フォールバック"""

    @patch("mystery_agents.tools.librarian_tools.validate_documents")
    @patch("mystery_agents.tools.librarian_tools.search_chronicling_america")
    def test_search_exception_captured_as_error(
        self, mock_search, mock_validate
    ):
        """search_chronicling_america が例外を投げるとエラーメッセージが記録される。"""
        mock_search.side_effect = ConnectionError("API unreachable")
        mock_validate.return_value = type("Summary", (), {
            "total_checked": 0, "reachable": 0, "unreachable": 0,
            "removed_urls": [], "duration_ms": 0, "verified_documents": [],
        })()

        result_json = search_newspapers(keywords="test keyword")
        result = json.loads(result_json)

        assert result["error"] == "API unreachable"
        assert result["documents_returned"] == 0


# === PR 2: 並列実行・動的制限・ランキングのテスト ===


class TestParallelExecution:
    """ThreadPoolExecutor 並列実行のテスト"""

    @patch("mystery_agents.tools.librarian_tools.validate_documents")
    @patch("mystery_agents.tools.librarian_tools.get_all_sources")
    def test_parallel_execution_faster_than_sequential(
        self, mock_get_all, mock_validate
    ):
        """3ソース × 0.3s delay → 合計 < 1.5s（逐次なら 0.9s 以上）。"""
        delay = 0.3
        docs = [_make_doc(url=f"https://example.com/{i}") for i in range(3)]
        sources = {}
        for i, key in enumerate(["s1", "s2", "s3"]):
            sources[key] = _make_mock_source(
                source_key=key,
                source_name=f"Source {i}",
                docs=[docs[i]],
                total_hits=1,
                delay=delay,
            )
        mock_get_all.return_value = sources
        mock_validate.return_value = type("Summary", (), {
            "total_checked": 3, "reachable": 3, "unreachable": 0,
            "removed_urls": [], "duration_ms": 100,
            "verified_documents": docs,
        })()

        start = time.monotonic()
        result_json = search_archives(
            keywords="test", sources="s1,s2,s3", language="en"
        )
        elapsed = time.monotonic() - start

        result = json.loads(result_json)
        assert result["total_documents"] == 3
        # 並列なので逐次（0.9s）よりはるかに短い
        assert elapsed < 1.5, f"並列実行が遅すぎる: {elapsed:.2f}s"

    @patch("mystery_agents.tools.librarian_tools.validate_documents")
    @patch("mystery_agents.tools.librarian_tools.get_all_sources")
    def test_parallel_deduplication(self, mock_get_all, mock_validate):
        """2ソースから同一 URL が返った場合、1件に重複除去される。"""
        shared_doc = _make_doc(url="https://shared.example.com/doc1")
        unique_doc = _make_doc(url="https://unique.example.com/doc2", title="Unique")

        sources = {
            "s1": _make_mock_source(
                source_key="s1", docs=[shared_doc], total_hits=1,
            ),
            "s2": _make_mock_source(
                source_key="s2", docs=[shared_doc, unique_doc], total_hits=2,
            ),
        }
        mock_get_all.return_value = sources
        mock_validate.return_value = type("Summary", (), {
            "total_checked": 2, "reachable": 2, "unreachable": 0,
            "removed_urls": [], "duration_ms": 50,
            "verified_documents": [shared_doc, unique_doc],
        })()

        result_json = search_archives(
            keywords="test", sources="s1,s2", language="en"
        )
        result = json.loads(result_json)

        assert result["total_documents"] == 2
        urls = [d["source_url"] for d in result["documents"]]
        assert len(set(urls)) == 2

    @patch("mystery_agents.tools.librarian_tools.validate_documents")
    @patch("mystery_agents.tools.librarian_tools.get_all_sources")
    def test_parallel_one_source_fails(self, mock_get_all, mock_validate):
        """1ソースが例外を投げても他ソースの結果は保持される。"""
        good_doc = _make_doc(url="https://good.example.com/doc")

        class FailingSource:
            source_key = "bad"
            source_name = "Bad Source"
            supports_language_filter = False
            supported_languages = {"en"}

            def search(self, **kwargs):
                raise ConnectionError("API down")

        sources = {
            "good": _make_mock_source(
                source_key="good", source_name="Good Source",
                docs=[good_doc], total_hits=1,
            ),
            "bad": FailingSource(),
        }
        mock_get_all.return_value = sources
        mock_validate.return_value = type("Summary", (), {
            "total_checked": 1, "reachable": 1, "unreachable": 0,
            "removed_urls": [], "duration_ms": 50,
            "verified_documents": [good_doc],
        })()

        result_json = search_archives(
            keywords="test", sources="good,bad", language="en"
        )
        result = json.loads(result_json)

        assert result["total_documents"] == 1
        assert result["documents"][0]["source_url"] == "https://good.example.com/doc"
        # bad ソースのエラーが記録されている
        assert result["errors"] is not None
        assert "bad" in result["errors"]


class TestDynamicMaxResults:
    """動的 per-source 結果制限のテスト"""

    @patch("mystery_agents.tools.librarian_tools.validate_documents")
    @patch("mystery_agents.tools.librarian_tools.get_all_sources")
    def test_dynamic_limit_2_sources(self, mock_get_all, mock_validate):
        """2ソース → per_source_limit = min(10, max(3, 30//2)) = 10。"""
        call_log = []

        def _make_logging_source(key):
            class LogSource:
                source_key = key
                source_name = f"Source {key}"
                supports_language_filter = False
                supported_languages = {"en"}

                def search(self, **kwargs):
                    call_log.append((key, kwargs["max_results"]))
                    return ArchiveSearchResult(documents=[], total_hits=0)

            return LogSource()

        sources = {
            "s1": _make_logging_source("s1"),
            "s2": _make_logging_source("s2"),
        }
        mock_get_all.return_value = sources
        mock_validate.return_value = type("Summary", (), {
            "total_checked": 0, "reachable": 0, "unreachable": 0,
            "removed_urls": [], "duration_ms": 0, "verified_documents": [],
        })()

        search_archives(keywords="test", sources="s1,s2", language="en")

        # per_source_limit = min(10, max(3, 30//2)) = 10
        for key, max_r in call_log:
            assert max_r == 10

    @patch("mystery_agents.tools.librarian_tools.validate_documents")
    @patch("mystery_agents.tools.librarian_tools.get_all_sources")
    def test_dynamic_limit_6_sources(self, mock_get_all, mock_validate):
        """6ソース → per_source_limit = min(10, max(3, 30//6)) = 5。"""
        call_log = []

        def _make_logging_source(key):
            class LogSource:
                source_key = key
                source_name = f"Source {key}"
                supports_language_filter = False
                supported_languages = {"en"}

                def search(self, **kwargs):
                    call_log.append((key, kwargs["max_results"]))
                    return ArchiveSearchResult(documents=[], total_hits=0)

            return LogSource()

        keys = [f"s{i}" for i in range(6)]
        sources = {k: _make_logging_source(k) for k in keys}
        mock_get_all.return_value = sources
        mock_validate.return_value = type("Summary", (), {
            "total_checked": 0, "reachable": 0, "unreachable": 0,
            "removed_urls": [], "duration_ms": 0, "verified_documents": [],
        })()

        search_archives(
            keywords="test",
            sources=",".join(keys),
            language="en",
        )

        # per_source_limit = min(10, max(3, 30//6)) = 5
        for key, max_r in call_log:
            assert max_r == 5


class TestTotalDocsCap:
    """合計ドキュメント上限のテスト"""

    @patch("mystery_agents.tools.librarian_tools.validate_documents")
    @patch("mystery_agents.tools.librarian_tools.get_all_sources")
    def test_total_docs_capped(self, mock_get_all, mock_validate):
        """全ソースから合計 40 件 → 上限 30 件にカットされる。"""
        docs_per_source = 20
        all_docs = []
        sources = {}
        for src_idx in range(2):
            key = f"s{src_idx}"
            src_docs = [
                _make_doc(
                    url=f"https://example.com/{key}/{i}",
                    title=f"Doc {key}-{i}",
                )
                for i in range(docs_per_source)
            ]
            all_docs.extend(src_docs)
            sources[key] = _make_mock_source(
                source_key=key,
                docs=src_docs,
                total_hits=docs_per_source,
            )

        mock_get_all.return_value = sources
        # validate_documents は全件通す
        mock_validate.side_effect = lambda docs: type("Summary", (), {
            "total_checked": len(docs), "reachable": len(docs), "unreachable": 0,
            "removed_urls": [], "duration_ms": 50,
            "verified_documents": list(docs),
        })()

        result_json = search_archives(
            keywords="test", sources="s0,s1", language="en"
        )
        result = json.loads(result_json)

        assert result["total_documents"] <= _TOTAL_DOCS_CAP


class TestRankDocuments:
    """_rank_documents のテスト（ソースインターリーブ方式）"""

    def test_interleave_prevents_single_source_domination(self):
        """IA 10件 + LOC 3件 → LOC の上位資料が埋もれない。"""
        ia_docs = [
            _make_doc(
                url=f"https://archive.org/{i}",
                source_type="internet_archive",
                keywords_matched=["ghost", "ship", "harbor"][:3 - i % 3],
            )
            for i in range(10)
        ]
        loc_docs = [
            _make_doc(
                url=f"https://loc.gov/{i}",
                source_type="nypl",
                keywords_matched=["ghost", "ship"][:2 - i % 2],
            )
            for i in range(3)
        ]

        ranked = _rank_documents(ia_docs + loc_docs)

        # 最初の4件には IA と LOC の両方が含まれる
        source_types_top4 = [d.source_type for d in ranked[:4]]
        assert "nypl" in source_types_top4
        assert "internet_archive" in source_types_top4

    def test_interleave_round_robin_order(self):
        """2ソースから交互に取り出される。"""
        doc_a1 = _make_doc(url="https://a.com/1", source_type="nypl", keywords_matched=["ghost", "ship"])
        doc_a2 = _make_doc(url="https://a.com/2", source_type="nypl", keywords_matched=["ghost"])
        doc_b1 = _make_doc(url="https://b.com/1", source_type="internet_archive", keywords_matched=["ghost", "ship", "harbor"])
        doc_b2 = _make_doc(url="https://b.com/2", source_type="internet_archive", keywords_matched=["ghost"])

        ranked = _rank_documents([doc_a1, doc_a2, doc_b1, doc_b2])

        # 4件全て含まれる
        assert len(ranked) == 4
        # 最初の2件は異なるソースタイプ
        assert ranked[0].source_type != ranked[1].source_type

    def test_ranking_within_source_by_keyword_match(self):
        """各ソース内では keywords_matched 数でソートされる。"""
        doc_3kw = _make_doc(
            url="https://a.com/3",
            source_type="nypl",
            keywords_matched=["ghost", "ship", "harbor"],
        )
        doc_1kw = _make_doc(
            url="https://a.com/1",
            source_type="nypl",
            keywords_matched=["ghost"],
        )
        doc_2kw = _make_doc(
            url="https://a.com/2",
            source_type="nypl",
            keywords_matched=["ghost", "ship"],
        )

        ranked = _rank_documents([doc_1kw, doc_3kw, doc_2kw])

        # 単一ソースなのでキーワード数順
        assert ranked[0].source_url == "https://a.com/3"
        assert ranked[1].source_url == "https://a.com/2"
        assert ranked[2].source_url == "https://a.com/1"

    def test_ranking_empty_list(self):
        """空リストでエラーにならない。"""
        assert _rank_documents([]) == []

    def test_ranking_single_source(self):
        """単一ソースのみの場合は通常のキーワード順。"""
        doc_a = _make_doc(url="https://a.com/a", source_type="nypl", keywords_matched=["ghost"])
        doc_b = _make_doc(url="https://a.com/b", source_type="nypl", keywords_matched=["ghost", "ship"])

        ranked = _rank_documents([doc_a, doc_b])

        assert ranked[0].source_url == "https://a.com/b"
        assert ranked[1].source_url == "https://a.com/a"

    def test_three_sources_interleave(self):
        """3ソースが正しくインターリーブされる。"""
        docs = [
            _make_doc(url="https://loc.gov/1", source_type="nypl", keywords_matched=["a"]),
            _make_doc(url="https://ia.org/1", source_type="internet_archive", keywords_matched=["a"]),
            _make_doc(url="https://ia.org/2", source_type="internet_archive", keywords_matched=["a", "b"]),
            _make_doc(url="https://euro.eu/1", source_type="europeana", keywords_matched=["a"]),
            _make_doc(url="https://euro.eu/2", source_type="europeana", keywords_matched=["a", "b"]),
        ]

        ranked = _rank_documents(docs)

        # 5件全て含まれる
        assert len(ranked) == 5
        # 最初の3件は全て異なるソース
        first_three_sources = {d.source_type for d in ranked[:3]}
        assert len(first_three_sources) == 3


class TestSearchSingleSource:
    """_search_single_source のテスト"""

    def test_returns_docs_and_metadata(self):
        """正常時にドキュメントとメタデータが返される。"""
        doc = _make_doc()
        source = _make_mock_source(
            source_key="test_src",
            docs=[doc],
            total_hits=1,
        )

        key, docs, hits, err, fallback = _search_single_source(
            source,
            [["ghost"]],
            date_start="1800",
            date_end="1899",
            per_source_limit=10,
            language=None,
        )

        assert key == "test_src"
        assert len(docs) == 1
        assert hits == 1
        assert err is None
        assert fallback is False

    def test_fallback_on_empty_combined_result(self):
        """複合キーワードで結果なし → 個別キーワードでフォールバック。"""
        doc = _make_doc()
        call_count = 0

        class FallbackSource:
            source_key = "fb"
            source_name = "Fallback Source"
            supports_language_filter = False

            def search(self, **kwargs):
                nonlocal call_count
                call_count += 1
                # 最初の呼び出し（複合キーワード）は結果なし
                # 個別キーワードでは結果あり
                if len(kwargs["keywords"]) > 1:
                    return ArchiveSearchResult(documents=[], total_hits=0)
                return ArchiveSearchResult(documents=[doc], total_hits=1)

        key, docs, hits, err, fallback = _search_single_source(
            FallbackSource(),
            [["ghost", "ship"]],
            date_start="1800",
            date_end="1899",
            per_source_limit=10,
            language=None,
        )

        assert fallback is True
        assert len(docs) == 1

    def test_passes_date_params_to_source(self):
        """日付パラメータがソースに正しく渡される。"""
        doc = _make_doc()
        call_log = []

        class NoExpandSource:
            source_key = "ne_src"
            source_name = "No Expand Source"
            supports_language_filter = False

            def search(self, **kwargs):
                call_log.append(kwargs)
                return ArchiveSearchResult(documents=[doc], total_hits=1)

        key, docs, hits, err, fallback = _search_single_source(
            NoExpandSource(),
            [["ghost"]],
            date_start="1800",
            date_end="1850",
            per_source_limit=10,
            language=None,
        )

        assert len(docs) == 1
        assert fallback is False
        # 元の日付範囲のみで検索（拡大なし）
        assert all(c["date_start"] == "1800" for c in call_log)

    def test_none_dates_passed_to_source(self):
        """date_start=None, date_end=None でクラッシュしない。"""
        call_log = []

        class NullDatesSource:
            source_key = "nd"
            source_name = "Null Dates Source"
            supports_language_filter = False

            def search(self, **kwargs):
                call_log.append(kwargs)
                return ArchiveSearchResult(documents=[], total_hits=0)

        key, docs, hits, err, fallback = _search_single_source(
            NullDatesSource(),
            [["ghost"]],
            date_start=None,
            date_end=None,
            per_source_limit=10,
            language=None,
        )

        assert len(call_log) == 1
        assert call_log[0]["date_start"] is None
        assert call_log[0]["date_end"] is None
        assert err is None

    def test_deduplicates_within_source(self):
        """同一ソース内の URL 重複が除去される。"""
        doc1 = _make_doc(url="https://same.com/doc")
        doc2 = _make_doc(url="https://same.com/doc", title="Duplicate")

        source = _make_mock_source(
            source_key="dup", docs=[doc1, doc2], total_hits=2,
        )

        key, docs, hits, err, fallback = _search_single_source(
            source,
            [["ghost"]],
            date_start="1800",
            date_end="1899",
            per_source_limit=10,
            language=None,
        )

        assert len(docs) == 1


# === PR 3: バイリンガル展開除去・デフォルト日付・新聞ディスパッチャのテスト ===


class TestNoBilingualExpansion:
    """search_archives がバイリンガル展開を行わないことを確認"""

    @patch("mystery_agents.tools.librarian_tools.validate_documents")
    @patch("mystery_agents.tools.librarian_tools.get_all_sources")
    @patch("mystery_agents.tools.librarian_tools.expand_keywords_bilingual")
    def test_search_archives_no_bilingual_expansion(
        self, mock_expand, mock_get_all, mock_validate
    ):
        """search_archives は expand_keywords_bilingual を呼ばない。"""
        mock_get_all.return_value = {
            "loc": _make_mock_source(source_key="loc", docs=[], total_hits=0),
        }
        mock_validate.return_value = type("Summary", (), {
            "total_checked": 0, "reachable": 0, "unreachable": 0,
            "removed_urls": [], "duration_ms": 0, "verified_documents": [],
        })()

        search_archives(keywords="ghost, ship", sources="loc", language="en")

        mock_expand.assert_not_called()


class TestDefaultDates:
    """デフォルト日付が None であることを確認"""

    @patch("mystery_agents.tools.librarian_tools.validate_documents")
    @patch("mystery_agents.tools.librarian_tools.get_all_sources")
    def test_search_archives_default_dates_none(
        self, mock_get_all, mock_validate
    ):
        """search_archives のデフォルト日付が None でソースに渡される。"""
        call_log = []

        class LogSource:
            source_key = "loc"
            source_name = "LOC"
            supports_language_filter = False
            supported_languages = {"en"}

            def search(self, **kwargs):
                call_log.append(kwargs)
                return ArchiveSearchResult(documents=[], total_hits=0)

        mock_get_all.return_value = {"loc": LogSource()}
        mock_validate.return_value = type("Summary", (), {
            "total_checked": 0, "reachable": 0, "unreachable": 0,
            "removed_urls": [], "duration_ms": 0, "verified_documents": [],
        })()

        # date_start / date_end を明示しない → None が渡される
        search_archives(keywords="test", sources="loc", language="en")

        assert call_log[0]["date_start"] is None
        assert call_log[0]["date_end"] is None


class TestNewspaperDispatcher:
    """search_newspapers のディスパッチャ動作テスト"""

    @patch("mystery_agents.tools.librarian_tools.validate_documents")
    @patch("mystery_agents.tools.librarian_tools.search_chronicling_america")
    @patch("mystery_agents.tools.librarian_tools.resolve_newspaper_sources")
    def test_newspaper_dispatcher_en_uses_chronicling_america(
        self, mock_resolve, mock_search_ca, mock_validate
    ):
        """EN → Chronicling America にルーティングされる。"""
        mock_ca = type("CA", (), {
            "source_key": "chronicling_america",
            "is_newspaper_source": True,
        })()
        mock_resolve.return_value = [mock_ca]

        doc = _make_doc()
        mock_search_ca.return_value = {
            "total_hits": 1,
            "documents": [doc],
            "error": None,
        }
        mock_validate.return_value = type("Summary", (), {
            "total_checked": 1, "reachable": 1, "unreachable": 0,
            "removed_urls": [], "duration_ms": 50,
            "verified_documents": [doc],
        })()

        result_json = search_newspapers(keywords="ghost", language="en")
        result = json.loads(result_json)

        assert result["source"] == "chronicling_america"
        assert result["documents_returned"] == 1
        mock_search_ca.assert_called()

    @patch("mystery_agents.tools.librarian_tools.resolve_newspaper_sources")
    def test_newspaper_dispatcher_unsupported_lang_returns_empty(
        self, mock_resolve
    ):
        """新聞ソースが存在しない言語 → 空結果を返す（エラーではない）。"""
        mock_resolve.return_value = []

        result_json = search_newspapers(keywords="Geist", language="de")
        result = json.loads(result_json)

        assert result["source"] == "none"
        assert result["documents_returned"] == 0
        assert result["error"] is None
        assert result["total_hits"] == 0

    @patch("mystery_agents.tools.librarian_tools.validate_documents")
    @patch("mystery_agents.tools.librarian_tools.search_chronicling_america")
    @patch("mystery_agents.tools.librarian_tools.resolve_newspaper_sources")
    def test_newspaper_dispatcher_default_language_is_en(
        self, mock_resolve, mock_search_ca, mock_validate
    ):
        """language 未指定 → "en" として処理される。"""
        mock_ca = type("CA", (), {
            "source_key": "chronicling_america",
            "is_newspaper_source": True,
        })()
        mock_resolve.return_value = [mock_ca]

        mock_search_ca.return_value = {
            "total_hits": 0,
            "documents": [],
            "error": None,
        }
        mock_validate.return_value = type("Summary", (), {
            "total_checked": 0, "reachable": 0, "unreachable": 0,
            "removed_urls": [], "duration_ms": 0, "verified_documents": [],
        })()

        search_newspapers(keywords="test")

        # language 未指定でも resolve_newspaper_sources("en") が呼ばれる
        mock_resolve.assert_called_once_with("en")


# === キーワード言語診断ログのテスト ===


class TestIsAsciiOnly:
    """_is_ascii_only のテスト"""

    def test_ascii_keyword_returns_true(self):
        """ASCII のみのキーワードは True を返す。"""
        assert _is_ascii_only("nightmare") is True
        assert _is_ascii_only("sleep paralysis") is True

    def test_umlaut_keyword_returns_false(self):
        """ウムラウト含むキーワードは False を返す。"""
        assert _is_ascii_only("Alpträume") is False
        assert _is_ascii_only("Ärzte") is False

    def test_accent_keyword_returns_false(self):
        """アクセント含むキーワードは False を返す。"""
        assert _is_ascii_only("cauchemar médical") is False

    def test_dutch_mixed_keyword(self):
        """オランダ語: ASCII のみなら True、非 ASCII があれば False。"""
        assert _is_ascii_only("geneeskunde") is True
        assert _is_ascii_only("coöperatie") is False

    def test_empty_string(self):
        """空文字列は ASCII のみ扱い。"""
        assert _is_ascii_only("") is True


class TestLogKeywordLanguageMismatch:
    """_log_keyword_language_mismatch のテスト"""

    def test_no_warning_for_latin_script_language(self, caplog):
        """ラテン文字言語（de）で全キーワードが ASCII → WARNING は出ない。"""
        import logging

        with caplog.at_level(logging.DEBUG):
            _log_keyword_language_mismatch(
                ["nightmare", "sleep paralysis"], "de"
            )

        # WARNING レベルのログは出ないこと
        warning_records = [r for r in caplog.records if r.levelno >= logging.WARNING]
        assert not warning_records

    def test_debug_log_for_latin_script_language(self, caplog):
        """ラテン文字言語（de）で全キーワードが ASCII → DEBUG ログが出力される。"""
        import logging

        with caplog.at_level(logging.DEBUG):
            _log_keyword_language_mismatch(
                ["nightmare", "sleep paralysis"], "de"
            )

        debug_records = [r for r in caplog.records if r.levelno == logging.DEBUG]
        assert any("キーワード言語不一致" in r.message for r in debug_records)

    def test_warning_for_non_latin_script_language(self, caplog):
        """非ラテン文字言語（ja）で全キーワードが ASCII → WARNING が出る。"""
        import logging

        with caplog.at_level(logging.WARNING):
            _log_keyword_language_mismatch(
                ["nightmare", "sleep paralysis"], "ja"
            )

        assert "キーワード言語不一致" in caplog.text
        assert "ja" in caplog.text

    def test_no_warning_for_native_keywords(self, caplog):
        """ネイティブ言語キーワードが含まれる場合は警告なし。"""
        import logging

        with caplog.at_level(logging.WARNING):
            _log_keyword_language_mismatch(
                ["Alpträume", "nightmare"], "de"
            )

        assert "キーワード言語不一致" not in caplog.text

    def test_no_warning_for_empty_keywords(self, caplog):
        """空のキーワードリストでは警告なし。"""
        import logging

        with caplog.at_level(logging.WARNING):
            _log_keyword_language_mismatch([], "de")

        assert "キーワード言語不一致" not in caplog.text


class TestGetExpansionLanguages:
    """_get_expansion_languages のテスト。"""

    def test_returns_other_languages(self):
        """自言語を除いた他の言語を返す。"""
        from mystery_agents.tools.search_orchestration import _get_expansion_languages
        from tests.fakes import make_tool_context

        ctx = make_tool_context({"selected_languages": ["en", "de", "fr"]})
        result = _get_expansion_languages(ctx, "de")
        assert result == ["en", "fr"]

    def test_single_language_returns_empty(self):
        """1言語のみなら空リスト。"""
        from mystery_agents.tools.search_orchestration import _get_expansion_languages
        from tests.fakes import make_tool_context

        ctx = make_tool_context({"selected_languages": ["en"]})
        result = _get_expansion_languages(ctx, "en")
        assert result == []

    def test_none_context_returns_empty(self):
        """tool_context が None なら空リスト。"""
        from mystery_agents.tools.search_orchestration import _get_expansion_languages

        result = _get_expansion_languages(None, "en")
        assert result == []


class TestMultilingualKeywordExpansion:
    """search_archives の多言語キーワード展開テスト。"""

    @patch("mystery_agents.tools.librarian_tools._translate_keywords_for_source")
    @patch("mystery_agents.tools.librarian_tools.translate_keywords")
    @patch("mystery_agents.tools.librarian_tools.validate_documents")
    @patch("mystery_agents.tools.librarian_tools.get_all_sources")
    def test_expansion_sent_to_multilingual_sources_only(
        self, mock_get_all, mock_validate, mock_translate, mock_per_source
    ):
        """展開キーワードは多言語ソースのみに渡される。"""
        from tests.fakes import make_tool_context

        # ソース別自動翻訳を無効化してテスト対象を限定
        mock_per_source.return_value = None

        # 多言語ソース（Europeana: 6言語対応）
        multi_source = _make_mock_source(
            source_key="europeana",
            source_name="Europeana",
            docs=[_make_doc(url="https://europeana.eu/1")],
            total_hits=1,
            supported_languages={"en", "de", "es", "fr", "nl", "pt"},
        )
        # 単一言語ソース（NDL: 日本語のみ）
        single_source = _make_mock_source(
            source_key="ndl",
            source_name="NDL",
            docs=[_make_doc(url="https://ndl.go.jp/1")],
            total_hits=1,
            supported_languages={"ja"},
        )
        mock_get_all.return_value = {"europeana": multi_source, "ndl": single_source}
        mock_validate.return_value = type("Summary", (), {
            "total_checked": 2, "reachable": 2, "unreachable": 0,
            "removed_urls": [], "duration_ms": 50,
            "verified_documents": [
                _make_doc(url="https://europeana.eu/1"),
                _make_doc(url="https://ndl.go.jp/1"),
            ],
        })()
        mock_translate.return_value = {"en": ["ghost", "haunting"]}

        ctx = make_tool_context({"selected_languages": ["en", "de"]})
        search_archives(
            keywords="Geist, Spuk",
            sources="europeana,ndl",
            language="de",
            tool_context=ctx,
        )

        mock_translate.assert_called_once()

    @patch("mystery_agents.tools.librarian_tools.translate_keywords")
    @patch("mystery_agents.tools.librarian_tools.validate_documents")
    @patch("mystery_agents.tools.librarian_tools.get_all_sources")
    def test_no_expansion_without_tool_context(
        self, mock_get_all, mock_validate, mock_translate
    ):
        """tool_context がない場合は展開しない。"""
        mock_source = _make_mock_source(
            source_key="europeana",
            docs=[],
            total_hits=0,
            supported_languages={"en", "de"},
        )
        mock_get_all.return_value = {"europeana": mock_source}
        mock_validate.return_value = type("Summary", (), {
            "total_checked": 0, "reachable": 0, "unreachable": 0,
            "removed_urls": [], "duration_ms": 0, "verified_documents": [],
        })()

        search_archives(
            keywords="ghost",
            sources="europeana",
            language="en",
            tool_context=None,
        )

        mock_translate.assert_not_called()

    @patch("mystery_agents.tools.librarian_tools.translate_keywords")
    @patch("mystery_agents.tools.librarian_tools.validate_documents")
    @patch("mystery_agents.tools.librarian_tools.get_all_sources")
    def test_no_expansion_without_language(
        self, mock_get_all, mock_validate, mock_translate
    ):
        """language が未指定の場合は展開しない。"""
        from tests.fakes import make_tool_context

        mock_source = _make_mock_source(
            source_key="loc",
            docs=[],
            total_hits=0,
        )
        mock_get_all.return_value = {"loc": mock_source}
        mock_validate.return_value = type("Summary", (), {
            "total_checked": 0, "reachable": 0, "unreachable": 0,
            "removed_urls": [], "duration_ms": 0, "verified_documents": [],
        })()

        ctx = make_tool_context({"selected_languages": ["en", "de"]})
        search_archives(
            keywords="ghost",
            sources="loc",
            language=None,
            tool_context=ctx,
        )

        mock_translate.assert_not_called()


class TestTranslateKeywordsForSource:
    """_translate_keywords_for_source のテスト。"""

    def test_trove_latin_script_skips_translation(self):
        """Trove（en: ラテン文字言語）に ASCII キーワード → 翻訳スキップ（None）。"""
        from mystery_agents.tools.search_orchestration import _translate_keywords_for_source

        trove_source = _make_mock_source(
            source_key="trove", supported_languages={"en"},
        )
        result = _translate_keywords_for_source(["ghost", "haunting"], trove_source)
        assert result is None

    def test_ndl_english_keywords_triggers_translation(self):
        """NDL（ja 単一言語）に英語キーワード → 翻訳が呼ばれる。"""
        from mystery_agents.tools.search_orchestration import _translate_keywords_for_source

        ndl_source = _make_mock_source(
            source_key="ndl", supported_languages={"ja"},
        )
        with patch(
            "mystery_agents.tools.search_orchestration.translate_keywords",
            return_value={"ja": ["幽霊", "怪奇"]},
        ) as mock_translate:
            result = _translate_keywords_for_source(["ghost", "haunting"], ndl_source)

        assert result == ["幽霊", "怪奇"]
        mock_translate.assert_called_once_with(["ghost", "haunting"], "en", ["ja"])

    def test_english_source_skipped(self):
        """英語ソース（LOC 等）→ None（スキップ）。"""
        from mystery_agents.tools.search_orchestration import _translate_keywords_for_source

        loc_source = _make_mock_source(
            source_key="loc", supported_languages={"en"},
        )
        result = _translate_keywords_for_source(["ghost"], loc_source)
        assert result is None

    def test_multilingual_source_skipped(self):
        """多言語ソース（Europeana 等）→ None（既存展開ロジックが担当）。"""
        from mystery_agents.tools.search_orchestration import _translate_keywords_for_source

        europeana_source = _make_mock_source(
            source_key="europeana",
            supported_languages={"en", "de", "es", "fr"},
        )
        result = _translate_keywords_for_source(["ghost"], europeana_source)
        assert result is None

    def test_non_ascii_keywords_skipped(self):
        """非 ASCII キーワードが含まれる場合 → None（既にネイティブ言語あり）。"""
        from mystery_agents.tools.search_orchestration import _translate_keywords_for_source

        trove_source = _make_mock_source(
            source_key="trove", supported_languages={"de"},
        )
        # ドイツ語キーワードが混在
        result = _translate_keywords_for_source(["ghost", "Alpträume"], trove_source)
        assert result is None

    def test_translation_failure_returns_none(self):
        """翻訳失敗時 → None（元キーワードで続行）。"""
        from mystery_agents.tools.search_orchestration import _translate_keywords_for_source

        ndl_source = _make_mock_source(
            source_key="ndl", supported_languages={"ja"},
        )
        with patch(
            "mystery_agents.tools.search_orchestration.translate_keywords",
            return_value={},
        ):
            result = _translate_keywords_for_source(["ghost"], ndl_source)

        assert result is None

    def test_mismatch_warning_logged_for_non_latin(self, caplog):
        """非ラテン文字ソース（NDL）で不一致検出時に WARNING ログが出力される。"""
        import logging

        from mystery_agents.tools.search_orchestration import _translate_keywords_for_source

        ndl_source = _make_mock_source(
            source_key="ndl", supported_languages={"ja"},
        )
        with patch(
            "mystery_agents.tools.search_orchestration.translate_keywords",
            return_value={"ja": ["幽霊"]},
        ):
            with caplog.at_level(logging.WARNING):
                _translate_keywords_for_source(["ghost"], ndl_source)

        assert "キーワード言語不一致" in caplog.text or "自動翻訳" in caplog.text


# === 2段階キーワード + search_log のテスト ===


class TestReferenceKeywords:
    """reference_keywords の結合・後方互換テスト"""

    @patch("mystery_agents.tools.librarian_tools.validate_documents")
    @patch("mystery_agents.tools.librarian_tools.get_all_sources")
    def test_reference_keywords_combined_with_exploratory(
        self, mock_get_all, mock_validate
    ):
        """reference + exploratory キーワードが結合されて検索される。"""
        call_log = []

        class LogSource:
            source_key = "loc"
            source_name = "LOC"
            supports_language_filter = False
            supported_languages = {"en"}

            def search(self, **kwargs):
                call_log.append(kwargs["keywords"])
                return ArchiveSearchResult(documents=[], total_hits=0)

        mock_get_all.return_value = {"loc": LogSource()}
        mock_validate.return_value = type("Summary", (), {
            "total_checked": 0, "reachable": 0, "unreachable": 0,
            "removed_urls": [], "duration_ms": 0, "verified_documents": [],
        })()

        result_json = search_archives(
            keywords="poltergeist, haunting",
            reference_keywords="Bell, Adams, Tennessee",
            sources="loc",
            language="en",
        )
        result = json.loads(result_json)

        # reference + exploratory の両方が keywords_used に含まれる
        assert "Bell" in result["keywords_used"]
        assert "poltergeist" in result["keywords_used"]
        # reference / exploratory が分離記録されている
        assert result["reference_keywords"] == ["Bell", "Adams", "Tennessee"]
        assert result["exploratory_keywords"] == ["poltergeist", "haunting"]
        # 最初の検索呼び出しに両方のキーワードが含まれる
        assert len(call_log) >= 1
        assert "Bell" in call_log[0]
        assert "poltergeist" in call_log[0]

    @patch("mystery_agents.tools.librarian_tools.validate_documents")
    @patch("mystery_agents.tools.librarian_tools.get_all_sources")
    def test_backward_compatible_without_reference_keywords(
        self, mock_get_all, mock_validate
    ):
        """reference_keywords 未指定時は全キーワードが exploratory 扱い。"""
        mock_get_all.return_value = {
            "loc": _make_mock_source(source_key="loc", docs=[], total_hits=0),
        }
        mock_validate.return_value = type("Summary", (), {
            "total_checked": 0, "reachable": 0, "unreachable": 0,
            "removed_urls": [], "duration_ms": 0, "verified_documents": [],
        })()

        result_json = search_archives(
            keywords="ghost, ship",
            sources="loc",
            language="en",
        )
        result = json.loads(result_json)

        assert result["reference_keywords"] == []
        assert result["exploratory_keywords"] == ["ghost", "ship"]
        assert result["keywords_used"] == ["ghost", "ship"]


class TestSearchLog:
    """search_log のセッション状態蓄積テスト"""

    @patch("mystery_agents.tools.librarian_tools.validate_documents")
    @patch("mystery_agents.tools.librarian_tools.get_all_sources")
    def test_search_log_entry_structure(self, mock_get_all, mock_validate):
        """search_log エントリに必須フィールドが存在する。"""
        from tests.fakes import make_tool_context

        mock_get_all.return_value = {
            "loc": _make_mock_source(source_key="loc", docs=[], total_hits=0),
        }
        mock_validate.return_value = type("Summary", (), {
            "total_checked": 0, "reachable": 0, "unreachable": 0,
            "removed_urls": [], "duration_ms": 0, "verified_documents": [],
        })()

        ctx = make_tool_context({})
        search_archives(
            keywords="haunting",
            reference_keywords="Bell, Tennessee",
            sources="loc",
            language="en",
            tool_context=ctx,
        )

        log = ctx.state.get("search_log", [])
        assert len(log) == 1
        entry = log[0]
        assert entry["tool"] == "search_archives"
        assert entry["reference_keywords"] == ["Bell", "Tennessee"]
        assert entry["exploratory_keywords"] == ["haunting"]
        assert entry["language"] == "en"
        assert "timestamp" in entry
        assert "sources_searched" in entry
        assert "total_documents" in entry
        assert "link_validation" in entry
        assert "fallback_used" in entry

    @patch("mystery_agents.tools.librarian_tools.validate_documents")
    @patch("mystery_agents.tools.librarian_tools.search_chronicling_america")
    @patch("mystery_agents.tools.librarian_tools.resolve_newspaper_sources")
    @patch("mystery_agents.tools.librarian_tools.get_all_sources")
    def test_search_log_accumulates_across_calls(
        self, mock_get_all, mock_resolve, mock_search_ca, mock_validate
    ):
        """search_archives + search_newspapers で search_log が蓄積される。"""
        from tests.fakes import make_tool_context

        # search_archives 用モック
        mock_get_all.return_value = {
            "loc": _make_mock_source(source_key="loc", docs=[], total_hits=0),
        }
        mock_validate.return_value = type("Summary", (), {
            "total_checked": 0, "reachable": 0, "unreachable": 0,
            "removed_urls": [], "duration_ms": 0, "verified_documents": [],
        })()

        # search_newspapers 用モック
        mock_ca = type("CA", (), {
            "source_key": "chronicling_america",
            "is_newspaper_source": True,
        })()
        mock_resolve.return_value = [mock_ca]
        mock_search_ca.return_value = {
            "total_hits": 0,
            "documents": [],
            "error": None,
        }

        ctx = make_tool_context({})

        # 1回目: search_archives
        search_archives(
            keywords="haunting",
            reference_keywords="Bell",
            sources="loc",
            language="en",
            tool_context=ctx,
        )
        # 2回目: search_newspapers
        search_newspapers(
            keywords="ghost",
            reference_keywords="Adams",
            language="en",
            tool_context=ctx,
        )

        log = ctx.state.get("search_log", [])
        assert len(log) == 2
        assert log[0]["tool"] == "search_archives"
        assert log[1]["tool"] == "search_newspapers"
