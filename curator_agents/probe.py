"""テーマ候補に対する軽量 API プローブ。

Curator が生成した probe_keywords を使い、全ソースを並列検索して
全文取得可能かどうかに基づいた coverage_score を算出・上書きする。
"""

from __future__ import annotations

import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass

from mystery_agents.tools.source_registry import get_all_sources
from shared.api_coverage import API_COVERAGE_REGISTRY, calculate_coverage_score

logger = logging.getLogger(__name__)

# プローブ時の最大取得件数（1→3 に増加し、判定精度を向上）
_PROBE_MAX_RESULTS = 3

# フォールバックキーワード抽出時に除去するストップワード
_STOP_WORDS: frozenset[str] = frozenset({
    "a", "an", "the",
    "of", "in", "on", "at", "to", "for", "from", "by", "with",
    "and", "or", "but", "nor", "not", "no",
    "is", "was", "were", "are", "be", "been", "being",
    "has", "have", "had", "do", "does", "did",
    "it", "its", "this", "that", "these", "those",
    "as", "if", "so", "than", "then",
    "about", "between", "through", "during", "before", "after",
})


@dataclass
class ProbeResult:
    """1 API グループのプローブ結果。"""

    has_content: bool  # raw_text を持つドキュメントが存在するか
    total_hits: int  # API が返した総ヒット件数


def _extract_fallback_keywords(theme_text: str, max_count: int = 5) -> list[str]:
    """テーマ文からストップワードを除去してフォールバックキーワードを抽出する。

    Args:
        theme_text: テーマの原文
        max_count: 返すキーワードの最大数

    Returns:
        ストップワード除去後の先頭 max_count 個のキーワード。
        全除去時は元テキストの先頭3単語にフォールバック（安全弁）。
    """
    words = theme_text.split()
    filtered = [w for w in words if w.lower() not in _STOP_WORDS]
    if not filtered:
        # 全単語がストップワードの場合は元テキストの先頭3単語にフォールバック
        return words[:3]
    return filtered[:max_count]


def _build_source_to_group_map() -> dict[str, str]:
    """source_registry キー → API グループキーのマッピングを構築する。"""
    mapping: dict[str, str] = {}
    for api_key, cov in API_COVERAGE_REGISTRY.items():
        for sk in cov.source_keys:
            mapping[sk] = api_key
    return mapping


def probe_theme(keywords: list[str]) -> dict[str, ProbeResult]:
    """1テーマについて全ソースを並列プローブし、API グループごとのプローブ結果を返す。

    Args:
        keywords: 検索キーワードリスト（probe_keywords）

    Returns:
        {api_group_key: ProbeResult} 形式の dict。
    """
    all_sources = get_all_sources()
    source_to_group = _build_source_to_group_map()

    group_results: dict[str, ProbeResult] = {}

    with ThreadPoolExecutor(max_workers=7) as executor:
        futures = {
            executor.submit(
                source.search, keywords, max_results=_PROBE_MAX_RESULTS
            ): key
            for key, source in all_sources.items()
        }
        for future in as_completed(futures):
            source_key = futures[future]
            try:
                result = future.result()
                api_group = source_to_group.get(source_key, source_key)
                has_content = any(
                    getattr(doc, "raw_text", None)
                    for doc in result.documents
                )
                total_hits = getattr(result, "total_hits", 0) or 0

                existing = group_results.get(api_group)
                if existing:
                    # 同一グループ内で合算
                    group_results[api_group] = ProbeResult(
                        has_content=existing.has_content or has_content,
                        total_hits=existing.total_hits + total_hits,
                    )
                else:
                    group_results[api_group] = ProbeResult(
                        has_content=has_content,
                        total_hits=total_hits,
                    )
            except Exception:
                logger.debug(
                    "プローブ失敗 (source=%s): %s",
                    source_key,
                    future.exception(),
                )

    return dict(group_results)


def probe_all_themes(themes: list[dict]) -> list[dict]:
    """全テーマをプローブし、coverage_score と primary_apis を付与する。

    Args:
        themes: Curator が生成したテーマ dict のリスト

    Returns:
        coverage_score, primary_apis, probe_hits が付与されたテーマリスト
    """
    for theme in themes:
        # probe_keywords が未出力の場合はストップワード除去後のキーワードにフォールバック
        probe_kws = theme.get("probe_keywords") or _extract_fallback_keywords(
            theme["theme"]
        )
        hits = probe_theme(probe_kws)
        score, apis = calculate_coverage_score(hits)
        theme["coverage_score"] = score
        theme["primary_apis"] = apis
        # dict 形式でシリアライズ（フロントエンド互換）
        theme["probe_hits"] = {
            api: {"has_content": pr.has_content, "total_hits": pr.total_hits}
            for api, pr in hits.items()
        }

    return themes
