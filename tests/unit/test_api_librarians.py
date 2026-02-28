"""API ベース Librarian エージェントファクトリのユニットテスト。"""

import pytest

from mystery_agents.agents.api_librarians import (
    API_CONFIGS,
    create_all_api_librarians,
    create_api_librarian,
)


class TestAPILibrarianFactory:
    """API Librarian ファクトリ関数のテスト。"""

    def test_create_all_returns_correct_count(self):
        """全 API Librarian が生成される。"""
        librarians = create_all_api_librarians()
        assert len(librarians) == len(API_CONFIGS)

    def test_all_have_unique_names(self):
        """全 Librarian のエージェント名がユニーク。"""
        librarians = create_all_api_librarians()
        names = [agent.name for agent in librarians]
        assert len(names) == len(set(names))

    def test_all_have_unique_output_keys(self):
        """全 Librarian の output_key がユニーク。"""
        librarians = create_all_api_librarians()
        keys = [agent.output_key for agent in librarians]
        assert len(keys) == len(set(keys))

    def test_output_key_format(self):
        """output_key が collected_documents_{api_key} 形式。"""
        for api_key in API_CONFIGS:
            agent = create_api_librarian(api_key)
            assert agent.output_key == f"collected_documents_{api_key}"

    def test_us_archives_has_newspaper_tool(self):
        """USArchivesLibrarian は search_newspapers ツールを持つ。"""
        from mystery_agents.tools.librarian_tools import search_newspapers

        agent = create_api_librarian("us_archives")
        assert search_newspapers in agent.tools

    def test_non_us_lacks_newspaper_tool(self):
        """US 以外の Librarian は search_newspapers を持たない。"""
        from mystery_agents.tools.librarian_tools import search_newspapers

        for api_key in ["europeana", "internet_archive", "ndl", "trove", "delpher"]:
            agent = create_api_librarian(api_key)
            assert search_newspapers not in agent.tools

    def test_all_have_search_archives_tool(self):
        """全 Librarian が search_archives ツールを持つ。"""
        from mystery_agents.tools.librarian_tools import search_archives

        librarians = create_all_api_librarians()
        for agent in librarians:
            assert search_archives in agent.tools

    def test_invalid_api_key_raises(self):
        """存在しない API キーで KeyError が発生する。"""
        with pytest.raises(KeyError):
            create_api_librarian("nonexistent_api")

    @pytest.mark.parametrize("api_key", list(API_CONFIGS.keys()))
    def test_instruction_contains_api_name(self, api_key):
        """各 Librarian の instruction に API 名が含まれる。"""
        agent = create_api_librarian(api_key)
        display_name = API_CONFIGS[api_key]["api_display_name"]
        assert display_name in agent.instruction

    def test_agent_name_format(self):
        """エージェント名が librarian_{api_key} 形式。"""
        for api_key in API_CONFIGS:
            agent = create_api_librarian(api_key)
            # MagicMock 環境では .name がモックされるため repr で検証
            assert f"librarian_{api_key}" in repr(agent)

    def test_instruction_source_keys_exist_in_registry(self):
        """instruction 内の sources= 値がソースレジストリに登録済みであること。"""
        import re

        from mystery_agents.tools.source_registry import get_all_sources

        registry_keys = set(get_all_sources().keys())
        pattern = re.compile(r'sources="([^"]+)"')

        for api_key, config in API_CONFIGS.items():
            strategy = config.get("search_strategy", "")
            match = pattern.search(strategy)
            if match:
                source_refs = [s.strip() for s in match.group(1).split(",")]
                for src in source_refs:
                    assert src in registry_keys, (
                        f"API '{api_key}' の instruction が参照する "
                        f"sources=\"{src}\" はソースレジストリに未登録"
                    )
