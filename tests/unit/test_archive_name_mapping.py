"""archive-name.ts マッピングと source_registry.py の同期テスト。

TypeScript の URL ドメインマッピング・source_type フォールバックが
Python ソースレジストリの全 ArchiveSource をカバーしているか検証する。
"""

import re
from pathlib import Path

import pytest

from mystery_agents.tools.source_registry import get_all_sources

# TypeScript マッピングファイルのパス
_TS_FILE = (
    Path(__file__).resolve().parents[2]
    / "packages"
    / "shared"
    / "src"
    / "lib"
    / "archive-name.ts"
)


@pytest.fixture(scope="module")
def ts_content() -> str:
    """archive-name.ts の内容を読み込む。"""
    return _TS_FILE.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def ts_url_domains(ts_content: str) -> set[str]:
    """URL_DOMAIN_MAP に含まれるドメイン文字列を抽出する。"""
    # ["loc.gov", "Library of Congress"] 形式の1要素目を抽出
    return set(re.findall(r'\["([^"]+)",\s*"[^"]+"', ts_content))


@pytest.fixture(scope="module")
def ts_source_types(ts_content: str) -> set[str]:
    """SOURCE_TYPE_MAP のキーを抽出する。"""
    # SOURCE_TYPE_MAP ブロック内の `key: "value"` パターン
    block_match = re.search(
        r"SOURCE_TYPE_MAP.*?=\s*\{(.*?)\}", ts_content, re.DOTALL
    )
    assert block_match, "SOURCE_TYPE_MAP が archive-name.ts に見つからない"
    return set(re.findall(r"(\w+):", block_match.group(1)))


class TestUrlDomainCoverage:
    """全 ArchiveSource の expected_domains が URL マッピングにカバーされているか。"""

    def test_all_expected_domains_covered(self, ts_url_domains: set[str]):
        """各ソースの expected_domains が TS の URL_DOMAIN_MAP に含まれる。"""
        all_sources = get_all_sources()
        uncovered: list[str] = []

        for key, source in all_sources.items():
            for domain in source.expected_domains:
                if not any(ts_domain in domain or domain in ts_domain
                           for ts_domain in ts_url_domains):
                    uncovered.append(f"{key}: {domain}")

        assert not uncovered, (
            f"以下のドメインが archive-name.ts の URL_DOMAIN_MAP に不足:\n"
            + "\n".join(f"  - {u}" for u in uncovered)
        )


class TestSourceTypeCoverage:
    """全 ArchiveSource の source_type が source_type フォールバックにカバーされているか。"""

    def test_all_source_types_covered(self, ts_source_types: set[str]):
        """各ソースの source_type が TS の SOURCE_TYPE_MAP に含まれる。"""
        all_sources = get_all_sources()
        uncovered: list[str] = []

        for key, source in all_sources.items():
            if source.source_type not in ts_source_types:
                uncovered.append(f"{key}: source_type={source.source_type}")

        assert not uncovered, (
            f"以下の source_type が archive-name.ts の SOURCE_TYPE_MAP に不足:\n"
            + "\n".join(f"  - {u}" for u in uncovered)
        )
