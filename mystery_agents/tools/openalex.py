"""OpenAlex 学術論文検索ツール — Armchair Polymath 専用。

OpenAlex API を使用して学術論文のメタデータを検索し、
言語分布・年代分布・主要概念タグを返す。
Polymath が学術界のカバレッジと盲点を客観的に評価するために使用する。

API ドキュメント: https://docs.openalex.org/
"""

import json
import logging
import os
import time
from collections import Counter

from shared.http_retry import create_retry_session

logger = logging.getLogger(__name__)

OPENALEX_BASE_URL = "https://api.openalex.org"

# レートリミット: API 呼び出し間の最小間隔（秒）
_RATE_LIMIT_INTERVAL = 1.0


def _build_params(
    query: str,
    api_key: str,
    *,
    language: str | None = None,
    year_from: str | None = None,
    year_to: str | None = None,
) -> dict:
    """共通クエリパラメータを構築する。"""
    params: dict[str, str] = {
        "search": query,
        "api_key": api_key,
    }

    # フィルタ条件の構築
    filters: list[str] = []
    if language:
        filters.append(f"language:{language}")
    if year_from and year_to:
        filters.append(f"publication_year:{year_from}-{year_to}")
    elif year_from:
        filters.append(f"publication_year:{year_from}-")
    elif year_to:
        filters.append(f"publication_year:-{year_to}")

    if filters:
        params["filter"] = ",".join(filters)

    return params


def _aggregate_temporal(year_counts: dict[str, int]) -> dict[str, int]:
    """個別年を3つの時代区分に集約する。

    - pre-1950: 1949年以前
    - 1950-1999: 1950〜1999年
    - 2000-present: 2000年以降
    """
    aggregated: dict[str, int] = {"pre-1950": 0, "1950-1999": 0, "2000-present": 0}
    for year_str, count in year_counts.items():
        try:
            year = int(year_str)
        except ValueError:
            continue
        if year < 1950:
            aggregated["pre-1950"] += count
        elif year < 2000:
            aggregated["1950-1999"] += count
        else:
            aggregated["2000-present"] += count
    return aggregated


def _extract_key_concepts(works: list[dict], max_concepts: int = 5) -> list[str]:
    """上位論文から頻出概念タグを抽出する。

    各論文の topics[].display_name と keywords[].display_name を集計し、
    出現頻度上位の概念を返す。
    """
    concept_counter: Counter[str] = Counter()

    for work in works:
        # topics から概念を抽出
        for topic in work.get("topics", []):
            name = topic.get("display_name")
            if name:
                concept_counter[name] += 1

        # keywords から概念を抽出
        for keyword in work.get("keywords", []):
            name = keyword.get("display_name")
            if name:
                concept_counter[name] += 1

    return [name for name, _ in concept_counter.most_common(max_concepts)]


def search_academic_papers(
    query: str,
    language: str | None = None,
    year_from: str | None = None,
    year_to: str | None = None,
) -> str:
    """OpenAlex API で学術論文を検索し、カバレッジ分析用データを返す。

    3回の API 呼び出しで効率的にデータを取得:
    1. 言語分布（group_by=language）
    2. 年代分布（group_by=publication_year）
    3. 被引用数上位5件の論文（概念タグ抽出用）

    Args:
        query: 検索クエリ（テーマ・キーワード）
        language: 言語フィルタ（ISO 639-1、例: "en", "de"）
        year_from: 開始年フィルタ（例: "1900"）
        year_to: 終了年フィルタ（例: "2020"）

    Returns:
        JSON 文字列（論文数、言語分布、年代分布、主要概念、上位論文）
    """
    api_key = os.environ.get("OPENALEX_API_KEY")
    if not api_key:
        return json.dumps({
            "status": "error",
            "error": "OPENALEX_API_KEY environment variable is not set. "
                     "Register for a free API key at https://openalex.org/",
        })

    session = create_retry_session()
    base_params = _build_params(
        query, api_key,
        language=language, year_from=year_from, year_to=year_to,
    )

    try:
        # 1. 言語分布を取得
        lang_params = {**base_params, "group_by": "language"}
        resp_lang = session.get(f"{OPENALEX_BASE_URL}/works", params=lang_params)
        if resp_lang.status_code != 200:
            return json.dumps({
                "status": "error",
                "error": f"OpenAlex API error (language distribution): HTTP {resp_lang.status_code}",
            })
        lang_data = resp_lang.json()

        # 論文総数と言語分布の集計
        papers_found = 0
        language_distribution: dict[str, int] = {}
        for group in lang_data.get("group_by", []):
            key = group.get("key", "unknown")
            count = group.get("count", 0)
            language_distribution[key] = count
            papers_found += count

        time.sleep(_RATE_LIMIT_INTERVAL)

        # 2. 年代分布を取得
        year_params = {**base_params, "group_by": "publication_year"}
        resp_year = session.get(f"{OPENALEX_BASE_URL}/works", params=year_params)
        if resp_year.status_code != 200:
            return json.dumps({
                "status": "error",
                "error": f"OpenAlex API error (temporal distribution): HTTP {resp_year.status_code}",
            })
        year_data = resp_year.json()

        year_counts: dict[str, int] = {}
        for group in year_data.get("group_by", []):
            key = str(group.get("key", ""))
            count = group.get("count", 0)
            year_counts[key] = count

        temporal_distribution = _aggregate_temporal(year_counts)

        time.sleep(_RATE_LIMIT_INTERVAL)

        # 3. 被引用数上位5件の論文を取得
        top_params = {**base_params, "per_page": "5", "sort": "cited_by_count:desc"}
        resp_top = session.get(f"{OPENALEX_BASE_URL}/works", params=top_params)
        if resp_top.status_code != 200:
            return json.dumps({
                "status": "error",
                "error": f"OpenAlex API error (top papers): HTTP {resp_top.status_code}",
            })
        top_data = resp_top.json()

        works = top_data.get("results", [])
        key_concepts = _extract_key_concepts(works)

        top_papers = []
        for work in works:
            top_papers.append({
                "title": work.get("title", ""),
                "publication_year": work.get("publication_year"),
                "cited_by_count": work.get("cited_by_count", 0),
                "doi": work.get("doi"),
                "language": work.get("language"),
            })

        return json.dumps({
            "status": "ok",
            "papers_found": papers_found,
            "language_distribution": language_distribution,
            "temporal_distribution": temporal_distribution,
            "key_concepts": key_concepts,
            "top_papers": top_papers,
        })

    except Exception as e:
        logger.error("OpenAlex 検索エラー: %s", e)
        return json.dumps({
            "status": "error",
            "error": f"OpenAlex search failed: {e}",
        })
