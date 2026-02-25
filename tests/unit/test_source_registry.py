"""Unit tests for mystery_agents/tools/source_registry.py"""

import pytest

from mystery_agents.tools.archive_source_base import ArchiveSearchResult, ArchiveSource
from mystery_agents.tools.source_registry import (
    _reset_registry,
    get_all_sources,
    get_source,
    register_source,
    resolve_newspaper_sources,
    resolve_sources,
)
from mystery_agents.schemas.document import SourceLanguage


class FakeSource(ArchiveSource):
    """テスト用の具象ソース。"""

    source_key = "fake"
    source_name = "Fake Source"
    source_type = "fake"
    min_request_delay = 0.0
    supported_languages = {"en", "de"}
    is_newspaper_source = False
    expected_domains = ["fake.example.com"]
    env_var_key = None

    def _search_impl(self, keywords, date_start, date_end, max_results, language):
        return ArchiveSearchResult()


class FakeNewspaperSource(ArchiveSource):
    """テスト用の新聞ソース。"""

    source_key = "fake_news"
    source_name = "Fake Newspaper"
    source_type = "fake_newspaper"
    min_request_delay = 0.0
    supported_languages = {"en"}
    is_newspaper_source = True
    expected_domains = ["news.example.com"]
    env_var_key = None

    def _search_impl(self, keywords, date_start, date_end, max_results, language):
        return ArchiveSearchResult()


class FakeGermanSource(ArchiveSource):
    """テスト用のドイツ語ソース。"""

    source_key = "fake_de"
    source_name = "Fake DE"
    source_type = "fake_de"
    min_request_delay = 0.0
    supported_languages = {"de"}
    is_newspaper_source = False
    env_var_key = None

    def _search_impl(self, keywords, date_start, date_end, max_results, language):
        return ArchiveSearchResult()


@pytest.fixture(autouse=True)
def clean_registry():
    """各テスト前にレジストリをリセットする（本物のソースはロードしない）。"""
    _reset_registry()
    # _all_loaded = True にして ensure_all_loaded() がリアルモジュールをロードしないようにする
    import mystery_agents.tools.source_registry as reg
    reg._all_loaded = True
    yield
    _reset_registry()


class TestRegisterAndGet:
    """register_source / get_source のテスト。"""

    def test_register_and_retrieve(self):
        """登録したソースを取得できる。"""
        source = FakeSource()
        register_source(source)

        retrieved = get_source("fake")
        assert retrieved is source

    def test_get_nonexistent_returns_none(self):
        """未登録のキーは None を返す。"""
        assert get_source("nonexistent") is None

    def test_get_all_sources(self):
        """全ソースを取得できる。"""
        s1 = FakeSource()
        s2 = FakeNewspaperSource()
        register_source(s1)
        register_source(s2)

        all_sources = get_all_sources()
        assert "fake" in all_sources
        assert "fake_news" in all_sources
        assert len(all_sources) == 2

    def test_duplicate_registration_overwrites(self):
        """同じキーで再登録すると上書きされる。"""
        s1 = FakeSource()
        s2 = FakeSource()
        register_source(s1)
        register_source(s2)

        assert get_source("fake") is s2


class TestResolveSources:
    """resolve_sources / resolve_newspaper_sources のテスト。"""

    def test_resolve_by_language(self):
        """言語コードでソースを解決できる。"""
        register_source(FakeSource())  # en, de
        register_source(FakeGermanSource())  # de only

        en_sources = resolve_sources("en")
        assert len(en_sources) == 1
        assert en_sources[0].source_key == "fake"

        de_sources = resolve_sources("de")
        assert len(de_sources) == 2
        keys = {s.source_key for s in de_sources}
        assert keys == {"fake", "fake_de"}

    def test_resolve_unsupported_language(self):
        """未対応言語は空リストを返す。"""
        register_source(FakeSource())

        result = resolve_sources("ja")
        assert result == []

    def test_resolve_newspaper_sources(self):
        """新聞ソースのみをフィルタできる。"""
        register_source(FakeSource())  # 非新聞
        register_source(FakeNewspaperSource())  # 新聞

        newspapers = resolve_newspaper_sources("en")
        assert len(newspapers) == 1
        assert newspapers[0].source_key == "fake_news"

    def test_resolve_newspaper_no_match(self):
        """新聞ソースがない言語は空リスト。"""
        register_source(FakeGermanSource())  # ドイツ語だが新聞ではない

        newspapers = resolve_newspaper_sources("de")
        assert newspapers == []


class TestEnsureAllLoaded:
    """ensure_all_loaded() のテスト。"""

    @pytest.fixture(autouse=True)
    def allow_real_loading(self):
        """このクラスではリアルモジュールのロードを許可する。"""
        _reset_registry()
        # _all_loaded = False のままにして ensure_all_loaded() が動くようにする
        yield
        _reset_registry()

    def test_real_sources_loaded(self):
        """実際のモジュールがロードされ、ソースが登録される。"""
        all_sources = get_all_sources()

        # 全 API ツールが登録されていること（Delpher は除外済み）
        expected_keys = {
            "loc", "dpla", "nypl", "internet_archive",
            "ddb", "europeana", "chronicling_america", "trove",
            "ndl", "wellcome",
        }
        assert expected_keys.issubset(set(all_sources.keys()))

    def test_source_metadata_correct(self):
        """各ソースのメタデータが正しく設定されている。"""
        all_sources = get_all_sources()

        loc = all_sources["loc"]
        assert loc.source_type == "loc_digital"
        assert loc.supported_languages == {"en"}
        assert loc.env_var_key is None

        ddb = all_sources["ddb"]
        assert ddb.source_type == "ddb"
        assert ddb.supported_languages == {"de"}
        assert ddb.env_var_key == "DDB_API_KEY"

        ca = all_sources["chronicling_america"]
        assert ca.is_newspaper_source is True
        assert ca.source_type == "newspaper"
