"""文書インベントリツール。

raw_search_results から全文書のアーカイブ別カタログを生成する。
Polymath が Scholar のテキスト経由ではなく、直接どのアーカイブに
どの文書があるかを確認できるようにする。

summary / raw_text は意図的に除外する。含めると Polymath が
メタデータの情報量で判断してしまうため。
"""

from __future__ import annotations

import json
import logging
from collections import defaultdict
from typing import Any, Optional

from google.adk.tools.tool_context import ToolContext

from shared.state_keys import RAW_SEARCH_RESULTS

logger = logging.getLogger(__name__)

# アーカイブ名マッピング（source_type → 表示名）
_ARCHIVE_NAMES: dict[str, str] = {
    "loc_digital": "LOC Digital Collections",
    "dpla": "DPLA",
    "nypl": "NYPL Digital Collections",
    "internet_archive": "Internet Archive",
    "ddb": "Deutsche Digitale Bibliothek",
    "europeana": "Europeana",
    "trove": "Trove (Australia)",
    "delpher": "Delpher (Netherlands)",
    "ndl": "NDL (National Diet Library, Japan)",
    "wellcome": "Wellcome Collection",
    "newspaper": "Historical Newspapers",
    "chronicling_america": "Chronicling America",
}

_NO_DATA_RESPONSE = {
    "status": "no_data",
    "message": "No raw_search_results found in session state.",
    "total_documents": 0,
    "by_archive": {},
    "archive_summary": "",
}


def _extract_documents_from_result(result: dict[str, Any]) -> list[dict[str, Any]]:
    """検索結果エントリからドキュメントリストを抽出する。"""
    docs = result.get("documents", [])
    if not isinstance(docs, list):
        return []
    return docs


def _get_archive_name(source_type: str) -> str:
    """source_type からアーカイブ表示名を取得する。"""
    return _ARCHIVE_NAMES.get(source_type, source_type)


def get_document_inventory(tool_context: Optional[ToolContext] = None) -> str:
    """Librarian が収集した全文書のカタログを返す。

    各文書について以下の情報のみ返す（summary/raw_text は意図的に除外）:
    - title: 文書タイトル
    - source_url: 原本URL
    - archive: アーカイブ名（LOC, Europeana, Internet Archive 等）
    - source_type: API ソースキー
    - date: 日付
    - language: 言語コード

    Args:
        tool_context: ADK tool context（セッション状態アクセス用）

    Returns:
        JSON: アーカイブ別にグループ化された文書カタログ
    """
    if tool_context is None:
        return json.dumps(_NO_DATA_RESPONSE, ensure_ascii=False)

    state = tool_context.state

    # raw_search_results と raw_search_results_{lang} を収集
    all_results: list[dict[str, Any]] = []

    # ベースキー
    base_results = state.get(RAW_SEARCH_RESULTS)
    if base_results and isinstance(base_results, list):
        for r in base_results:
            if isinstance(r, dict):
                all_results.append(r)

    # 言語別キー
    state_dict = state.to_dict() if hasattr(state, "to_dict") else state
    for key in list(state_dict.keys()):
        if key.startswith(RAW_SEARCH_RESULTS + "_") and key != RAW_SEARCH_RESULTS:
            lang_results = state.get(key)
            if lang_results and isinstance(lang_results, list):
                for r in lang_results:
                    if isinstance(r, dict):
                        all_results.append(r)

    if not all_results:
        return json.dumps(_NO_DATA_RESPONSE, ensure_ascii=False)

    # 全文書を抽出してアーカイブ別にグループ化
    by_archive: dict[str, list[dict[str, Any]]] = defaultdict(list)
    seen_urls: set[str] = set()
    total = 0

    for result in all_results:
        docs = _extract_documents_from_result(result)
        for doc in docs:
            url = doc.get("source_url", "")
            if not url or url in seen_urls:
                continue
            seen_urls.add(url)

            source_type = doc.get("source_type", "unknown")
            archive_name = _get_archive_name(source_type)

            # メタデータのみ抽出（summary/raw_text は除外）
            entry = {
                "title": doc.get("title", ""),
                "source_url": url,
                "date": doc.get("date"),
                "language": doc.get("language", ""),
            }
            by_archive[archive_name].append(entry)
            total += 1

    # サマリ文字列の生成
    archive_counts = sorted(by_archive.items(), key=lambda x: len(x[1]), reverse=True)
    summary_parts = [f"{name}: {len(docs)} docs" for name, docs in archive_counts]
    archive_summary = ", ".join(summary_parts)

    # inventory 参照済みフラグをセット（save_structured_report が確認する）
    tool_context.state["_inventory_consulted"] = True

    response = {
        "status": "ok",
        "total_documents": total,
        "by_archive": dict(by_archive),
        "archive_summary": archive_summary,
    }

    return json.dumps(response, ensure_ascii=False)
