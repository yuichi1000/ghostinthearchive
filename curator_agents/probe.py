"""テーマ候補に対する軽量 API プローブ。

Curator が生成した probe_keywords を使い、全ソースを並列検索して
実際のヒット件数に基づいた coverage_score を算出・上書きする。
"""

from __future__ import annotations

import logging
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed

from mystery_agents.tools.source_registry import get_all_sources
from shared.api_coverage import API_COVERAGE_REGISTRY, calculate_coverage_score

logger = logging.getLogger(__name__)


def _build_source_to_group_map() -> dict[str, str]:
    """source_registry キー → API グループキーのマッピングを構築する。"""
    mapping: dict[str, str] = {}
    for api_key, cov in API_COVERAGE_REGISTRY.items():
        for sk in cov.source_keys:
            mapping[sk] = api_key
    return mapping


def probe_theme(keywords: list[str]) -> dict[str, int]:
    """1テーマについて全ソースを並列プローブし、API グループごとのヒット件数を返す。

    Args:
        keywords: 検索キーワードリスト（probe_keywords）

    Returns:
        {api_group_key: total_hits} 形式の dict
    """
    all_sources = get_all_sources()
    source_to_group = _build_source_to_group_map()

    group_hits: dict[str, int] = defaultdict(int)

    with ThreadPoolExecutor(max_workers=7) as executor:
        futures = {
            executor.submit(source.search, keywords, max_results=1): key
            for key, source in all_sources.items()
        }
        for future in as_completed(futures):
            source_key = futures[future]
            try:
                result = future.result()
                api_group = source_to_group.get(source_key, source_key)
                group_hits[api_group] += result.total_hits
            except Exception:
                logger.debug(
                    "プローブ失敗 (source=%s): %s",
                    source_key,
                    future.exception(),
                )

    return dict(group_hits)


def probe_all_themes(themes: list[dict]) -> list[dict]:
    """全テーマをプローブし、coverage_score と primary_apis を付与する。

    Args:
        themes: Curator が生成したテーマ dict のリスト

    Returns:
        coverage_score, primary_apis, probe_hits が付与されたテーマリスト
    """
    for theme in themes:
        # probe_keywords が未出力の場合はテーマ文をフォールバック分割
        probe_kws = theme.get("probe_keywords") or theme["theme"].split()[:5]
        hits = probe_theme(probe_kws)
        score, apis = calculate_coverage_score(hits)
        theme["coverage_score"] = score
        theme["primary_apis"] = apis
        theme["probe_hits"] = hits

    return themes
