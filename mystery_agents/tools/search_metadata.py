"""検索メタデータ取得ツール。

raw_search_results から API 検索状況のコンパクトなサマリを生成する。
raw_search_results はドキュメント全文を含み巨大なため、
ツール経由で必要なメタデータのみ抽出する。
"""

from __future__ import annotations

import json
import logging
from typing import Any, Optional

from google.adk.tools.tool_context import ToolContext

logger = logging.getLogger(__name__)

# 検索結果がない場合のレスポンス
_NO_DATA_RESPONSE = {
    "status": "no_data",
    "message": "No raw_search_results found in session state.",
    "apis_searched": [],
    "apis_with_results": [],
    "apis_without_results": [],
    "per_api_stats": {},
    "languages_searched": [],
}


def _extract_from_single_result(result: dict[str, Any]) -> dict[str, Any]:
    """単一の検索結果エントリからメタデータを抽出する。

    search_newspapers 形式と search_archives 形式の両方に対応。

    Returns:
        api_name → {total_hits, documents_returned} の dict、
        および errors / fallback_used 情報
    """
    per_api: dict[str, dict[str, int]] = {}
    errors: dict[str, str] = {}
    fallback_used = False

    # search_newspapers 形式: source フィールドで API を識別
    source = result.get("source")
    if source and source != "none":
        per_api[source] = {
            "total_hits": result.get("total_hits", 0),
            "documents_returned": result.get("documents_returned", 0),
        }
        if result.get("error"):
            errors[source] = result["error"]

    # search_archives 形式: sources_searched dict で各 API の統計を取得
    sources_searched = result.get("sources_searched")
    if sources_searched and isinstance(sources_searched, dict):
        for api_key, stats in sources_searched.items():
            if isinstance(stats, dict):
                per_api[api_key] = {
                    "total_hits": stats.get("total_hits", 0),
                    "documents_returned": stats.get("documents_returned", 0),
                }

    # search_archives のエラー情報
    result_errors = result.get("errors")
    if result_errors and isinstance(result_errors, dict):
        errors.update(result_errors)

    # fallback_used
    if result.get("fallback_used"):
        fallback_used = True

    return {
        "per_api": per_api,
        "errors": errors,
        "fallback_used": fallback_used,
    }


def get_search_metadata(tool_context: Optional[ToolContext] = None) -> str:
    """raw_search_results から API 検索状況のサマリを生成する。

    セッション状態の raw_search_results / raw_search_results_{lang} を読み取り、
    どの API が検索され、どの API で結果が得られたかのコンパクトなサマリを返す。

    Args:
        tool_context: ADK tool context（セッション状態アクセス用）

    Returns:
        JSON 文字列: apis_searched, apis_with_results, apis_without_results,
                     per_api_stats, languages_searched
    """
    if tool_context is None:
        return json.dumps(_NO_DATA_RESPONSE, ensure_ascii=False)

    state = tool_context.state

    # raw_search_results と raw_search_results_{lang} を収集
    all_results: list[tuple[str, list]] = []

    # ベースキー
    base_results = state.get("raw_search_results")
    if base_results and isinstance(base_results, list):
        all_results.append(("base", base_results))

    # 言語別キー
    languages_searched: list[str] = []
    for key in list(state.keys()):
        if key.startswith("raw_search_results_") and key != "raw_search_results":
            lang = key.replace("raw_search_results_", "")
            lang_results = state.get(key)
            if lang_results and isinstance(lang_results, list):
                all_results.append((lang, lang_results))
                languages_searched.append(lang)

    if not all_results:
        return json.dumps(_NO_DATA_RESPONSE, ensure_ascii=False)

    # 全結果を集約
    per_api_stats: dict[str, dict[str, int]] = {}
    all_errors: dict[str, str] = {}
    any_fallback = False

    for _label, results_list in all_results:
        for result in results_list:
            if not isinstance(result, dict):
                continue
            extracted = _extract_from_single_result(result)
            # per_api を集約（同じ API は hits/docs を加算）
            for api_name, stats in extracted["per_api"].items():
                if api_name in per_api_stats:
                    per_api_stats[api_name]["total_hits"] += stats["total_hits"]
                    per_api_stats[api_name]["documents_returned"] += stats["documents_returned"]
                else:
                    per_api_stats[api_name] = dict(stats)
            all_errors.update(extracted["errors"])
            if extracted["fallback_used"]:
                any_fallback = True

    apis_searched = sorted(per_api_stats.keys())
    apis_with_results = sorted(
        api for api, stats in per_api_stats.items()
        if stats["documents_returned"] > 0
    )
    apis_without_results = sorted(
        api for api, stats in per_api_stats.items()
        if stats["documents_returned"] == 0
    )

    response = {
        "status": "ok",
        "apis_searched": apis_searched,
        "apis_with_results": apis_with_results,
        "apis_without_results": apis_without_results,
        "per_api_stats": per_api_stats,
        "languages_searched": sorted(languages_searched),
    }
    if all_errors:
        response["errors"] = all_errors
    if any_fallback:
        response["fallback_used"] = True

    return json.dumps(response, ensure_ascii=False)
