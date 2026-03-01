"""API カバレッジメタデータ — Curator プロンプト + プローブスコア算出の両方で使用。

各 API グループの言語・地域・全文信頼度を宣言し、
Curator プロンプトへの動的テーブル挿入とプローブスコア算出ロジックを提供する。

api_key は Librarian エージェントの API グループキー（api_librarians.py の API_CONFIGS と一致）、
source_keys は source_registry のキー（nypl, chronicling_america 等）へのマッピング。
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ApiCoverage:
    """1 API グループのカバレッジメタデータ。"""

    api_key: str
    display_name: str
    source_keys: tuple[str, ...]
    languages: tuple[str, ...]
    regions: tuple[str, ...]
    time_period: str
    fulltext_reliability: str  # "HIGH" / "MEDIUM" / "LOW"
    fulltext_era: str


API_COVERAGE_REGISTRY: dict[str, ApiCoverage] = {
    "us_archives": ApiCoverage(
        api_key="us_archives",
        display_name="US Digital Archives (NYPL + Chronicling America)",
        source_keys=("nypl", "chronicling_america"),
        languages=("en",),
        regions=("United States",),
        time_period="1690-1963",
        fulltext_reliability="HIGH",
        fulltext_era="1770-1963 OCR",
    ),
    "europeana": ApiCoverage(
        api_key="europeana",
        display_name="Europeana",
        source_keys=("europeana",),
        languages=("de", "es", "fr", "nl", "pt"),
        regions=("Europe (50+ countries)",),
        time_period="Antiquity-present",
        fulltext_reliability="LOW",
        fulltext_era="Newspapers only full-text",
    ),
    "internet_archive": ApiCoverage(
        api_key="internet_archive",
        display_name="Internet Archive",
        source_keys=("internet_archive",),
        languages=("en", "de", "es", "fr", "nl", "pt", "ja"),
        regions=("Global",),
        time_period="All eras",
        fulltext_reliability="HIGH",
        fulltext_era="All eras, books/periodicals OCR",
    ),
    "ndl": ApiCoverage(
        api_key="ndl",
        display_name="NDL Search (National Diet Library, Japan)",
        source_keys=("ndl",),
        languages=("ja",),
        regions=("Japan",),
        time_period="Edo-Showa",
        fulltext_reliability="MEDIUM",
        fulltext_era="Meiji-Showa digitized",
    ),
    "delpher": ApiCoverage(
        api_key="delpher",
        display_name="KB/Delpher (Dutch National Library)",
        source_keys=("delpher",),
        languages=("nl",),
        regions=("Netherlands", "Dutch colonies"),
        time_period="1618-present",
        fulltext_reliability="HIGH",
        fulltext_era="1600s-1990s OCR",
    ),
    "trove": ApiCoverage(
        api_key="trove",
        display_name="Trove (National Library of Australia)",
        source_keys=("trove",),
        languages=("en",),
        regions=("Australia", "Oceania"),
        time_period="1803-present",
        fulltext_reliability="HIGH",
        fulltext_era="1800s-1950s newspaper OCR",
    ),
    "ndl_search": ApiCoverage(
        api_key="ndl_search",
        display_name="NDL Search (duplicate check)",
        source_keys=("ndl",),
        languages=("ja",),
        regions=("Japan",),
        time_period="Edo-Showa",
        fulltext_reliability="MEDIUM",
        fulltext_era="Meiji-Showa digitized",
    ),
}

# ndl_search は source_registry のキー "ndl" と api_librarians の "ndl" が一致するため、
# 重複エントリは削除し ndl のみ残す
del API_COVERAGE_REGISTRY["ndl_search"]

VALID_API_KEYS: frozenset[str] = frozenset(API_COVERAGE_REGISTRY)


def build_coverage_prompt_table() -> str:
    """Curator プロンプト用の API カバレッジテーブルを動的生成する。

    Returns:
        マークダウンテーブル形式の文字列
    """
    header = (
        "| API | Languages | Regions | Coverage | "
        "Full-text Reliability | Full-text Era |"
    )
    separator = (
        "|-----|-----------|---------|----------|"
        "----------------------|---------------|"
    )
    rows = [header, separator]
    for cov in API_COVERAGE_REGISTRY.values():
        langs = ", ".join(cov.languages)
        regions = ", ".join(cov.regions)
        rows.append(
            f"| {cov.display_name} | {langs} | {regions} | "
            f"{cov.time_period} | {cov.fulltext_reliability} | {cov.fulltext_era} |"
        )
    return "\n".join(rows)


def calculate_coverage_score(
    probe_results: dict,
) -> tuple[str, list[str]]:
    """プローブ結果からスコアと有効 API リストを算出する。

    Args:
        probe_results: {api_key: ProbeResult} または {api_key: bool}（後方互換）形式

    Returns:
        (score, primary_apis) タプル。
        score は "HIGH" / "MEDIUM" / "LOW"。
        primary_apis は全文取得可能だった API キーのリスト。
    """
    from curator_agents.probe import ProbeResult

    # 後方互換: bool 値を ProbeResult に変換
    normalized: dict[str, ProbeResult] = {}
    for k, v in probe_results.items():
        if isinstance(v, bool):
            normalized[k] = ProbeResult(has_content=v, total_hits=0)
        else:
            normalized[k] = v

    # 全文取得可能な API を抽出
    hit_apis = [k for k, pr in normalized.items() if pr.has_content]
    hit_count = len(hit_apis)

    # 全文信頼度 HIGH の API がヒットに含まれるか
    has_high_reliability = any(
        API_COVERAGE_REGISTRY[k].fulltext_reliability == "HIGH"
        for k in hit_apis
        if k in API_COVERAGE_REGISTRY
    )

    # いずれかの API で total_hits >= 50 のディープヒットがあるか
    has_deep_hits = any(
        normalized[k].total_hits >= 50
        for k in hit_apis
    )

    if hit_count >= 3 and has_high_reliability:
        score = "HIGH"
    elif hit_count >= 2 and has_high_reliability and has_deep_hits:
        # 2 API でも HIGH 信頼度 + ディープヒットがあれば HIGH に昇格
        score = "HIGH"
    elif hit_count >= 2:
        score = "MEDIUM"
    else:
        score = "LOW"

    return score, hit_apis
