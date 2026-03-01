"""API ベース Librarian エージェントファクトリのユニットテスト。

create_api_librarian() は SequentialAgent(Round 1 + Round 2) を返す:
- Round 1（temp=0.3）: 堅実な初回検索 → collected_documents_{api_key}
- Round 2（temp=0.7）: 適応的再検索 → adaptive_search_{api_key}
"""

from unittest.mock import MagicMock

import pytest

from mystery_agents.agents.api_librarians import (
    API_CONFIGS,
    create_all_api_librarians,
    create_api_librarian,
)


def _fake_generate_content_config(**kwargs):
    """GenerateContentConfig のフェイク。kwargs を属性として保持する。"""
    m = MagicMock()
    for k, v in kwargs.items():
        setattr(m, k, v)
    return m


class TestAPILibrarianFactory:
    """API Librarian ファクトリ関数のテスト。"""

    def test_create_all_returns_correct_count(self):
        """全 API Librarian ブロックが生成される。"""
        librarians = create_all_api_librarians()
        assert len(librarians) == len(API_CONFIGS)

    def test_all_blocks_have_unique_names(self):
        """全ブロックのエージェント名がユニーク。"""
        librarians = create_all_api_librarians()
        names = [agent.name for agent in librarians]
        assert len(names) == len(set(names))

    def test_invalid_api_key_raises(self):
        """存在しない API キーで KeyError が発生する。"""
        with pytest.raises(KeyError):
            create_api_librarian("nonexistent_api")

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


class TestAdaptiveSearchBlock:
    """SequentialAgent ブロック（Round 1 + Round 2）の構造テスト。"""

    def test_block_has_two_sub_agents(self):
        """ブロックは Round 1 + Round 2 の2つの sub_agent を持つ。"""
        block = create_api_librarian("europeana")
        assert len(block.sub_agents) == 2

    def test_block_name_format(self):
        """ブロック名が librarian_{api_key}_block 形式。"""
        for api_key in API_CONFIGS:
            block = create_api_librarian(api_key)
            assert f"librarian_{api_key}_block" in repr(block)

    def test_round1_name_format(self):
        """Round 1 のエージェント名が librarian_{api_key} 形式。"""
        for api_key in API_CONFIGS:
            block = create_api_librarian(api_key)
            round1 = block.sub_agents[0]
            assert f"librarian_{api_key}" in repr(round1)

    def test_round2_name_format(self):
        """Round 2 のエージェント名が librarian_{api_key}_adaptive 形式。"""
        for api_key in API_CONFIGS:
            block = create_api_librarian(api_key)
            round2 = block.sub_agents[1]
            assert f"librarian_{api_key}_adaptive" in repr(round2)

    def test_round1_output_key(self):
        """Round 1 の output_key が collected_documents_{api_key} 形式。"""
        for api_key in API_CONFIGS:
            block = create_api_librarian(api_key)
            round1 = block.sub_agents[0]
            assert round1.output_key == f"collected_documents_{api_key}"

    def test_round2_output_key(self):
        """Round 2 の output_key が adaptive_search_{api_key} 形式。"""
        for api_key in API_CONFIGS:
            block = create_api_librarian(api_key)
            round2 = block.sub_agents[1]
            assert round2.output_key == f"adaptive_search_{api_key}"

    @pytest.mark.parametrize("api_key", list(API_CONFIGS.keys()))
    def test_round1_instruction_contains_api_name(self, api_key):
        """Round 1 の instruction に API 名が含まれる。"""
        block = create_api_librarian(api_key)
        round1 = block.sub_agents[0]
        display_name = API_CONFIGS[api_key]["api_display_name"]
        assert display_name in round1.instruction

    @pytest.mark.parametrize("api_key", list(API_CONFIGS.keys()))
    def test_round2_instruction_contains_api_name(self, api_key):
        """Round 2 の instruction に API 名が含まれる。"""
        block = create_api_librarian(api_key)
        round2 = block.sub_agents[1]
        display_name = API_CONFIGS[api_key]["api_display_name"]
        assert display_name in round2.instruction

    @pytest.mark.parametrize("api_key", list(API_CONFIGS.keys()))
    def test_round2_instruction_has_state_placeholder(self, api_key):
        """Round 2 の instruction が Round 1 結果の状態変数を参照している。"""
        block = create_api_librarian(api_key)
        round2 = block.sub_agents[1]
        # .format() 後に残る ADK 状態変数プレースホルダー
        expected = f"{{collected_documents_{api_key}}}"
        assert expected in round2.instruction

    def test_round1_temperature(self):
        """Round 1 の temperature が 0.3 である。"""
        from google.genai import types

        types.GenerateContentConfig.side_effect = _fake_generate_content_config
        try:
            block = create_api_librarian("europeana")
            round1 = block.sub_agents[0]
            assert round1.generate_content_config.temperature == 0.3
        finally:
            types.GenerateContentConfig.side_effect = None

    def test_round2_temperature(self):
        """Round 2 の temperature が 0.7 である。"""
        from google.genai import types

        types.GenerateContentConfig.side_effect = _fake_generate_content_config
        try:
            block = create_api_librarian("europeana")
            round2 = block.sub_agents[1]
            assert round2.generate_content_config.temperature == 0.7
        finally:
            types.GenerateContentConfig.side_effect = None

    def test_round1_has_search_archives_tool(self):
        """Round 1 が search_archives ツールを持つ。"""
        from mystery_agents.tools.librarian_tools import search_archives

        for api_key in API_CONFIGS:
            block = create_api_librarian(api_key)
            round1 = block.sub_agents[0]
            assert search_archives in round1.tools

    def test_round2_has_search_archives_tool(self):
        """Round 2 が search_archives ツールを持つ。"""
        from mystery_agents.tools.librarian_tools import search_archives

        for api_key in API_CONFIGS:
            block = create_api_librarian(api_key)
            round2 = block.sub_agents[1]
            assert search_archives in round2.tools

    def test_us_archives_both_rounds_have_newspaper_tool(self):
        """US Archives の Round 1 と Round 2 の両方が search_newspapers を持つ。"""
        from mystery_agents.tools.librarian_tools import search_newspapers

        block = create_api_librarian("us_archives")
        round1 = block.sub_agents[0]
        round2 = block.sub_agents[1]
        assert search_newspapers in round1.tools
        assert search_newspapers in round2.tools

    def test_non_us_both_rounds_lack_newspaper_tool(self):
        """US 以外の Round 1 と Round 2 は search_newspapers を持たない。"""
        from mystery_agents.tools.librarian_tools import search_newspapers

        for api_key in ["europeana", "internet_archive", "ndl", "trove", "delpher"]:
            block = create_api_librarian(api_key)
            round1 = block.sub_agents[0]
            round2 = block.sub_agents[1]
            assert search_newspapers not in round1.tools
            assert search_newspapers not in round2.tools

    def test_all_block_names_unique(self):
        """全ブロック名、Round 1 名、Round 2 名がそれぞれユニーク。"""
        blocks = create_all_api_librarians()
        block_names = []
        round1_names = []
        round2_names = []
        for block in blocks:
            block_names.append(repr(block))
            round1_names.append(repr(block.sub_agents[0]))
            round2_names.append(repr(block.sub_agents[1]))
        assert len(block_names) == len(set(block_names))
        assert len(round1_names) == len(set(round1_names))
        assert len(round2_names) == len(set(round2_names))
