"""Librarian 検索メトリクスの抽出・Firestore 永続化。

セッション状態の raw_search_results / raw_search_results_{lang} から
API ソース別の検索統計を抽出し、pipeline_runs ドキュメントに保存する。
パイプライン終了後のデータ分析・改善に活用する。
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger(__name__)


def _extract_from_single_result(result: dict[str, Any]) -> dict[str, Any]:
    """単一の検索結果エントリからメタデータを抽出する。

    search_newspapers 形式と search_archives 形式の両方に対応。
    mystery_agents/tools/search_metadata.py の同名関数と同一ロジック。
    shared → mystery_agents の逆方向 import を避けるためインライン。

    Returns:
        per_api: api_name → {total_hits, documents_returned} の dict
        errors: api_name → エラーメッセージ の dict
        fallback_used: フォールバック検索が使用されたか
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


def extract_search_metrics(session_state: dict) -> dict | None:
    """セッション状態から検索メトリクスを抽出する。

    raw_search_results（ベースキー: 新聞検索等）と
    raw_search_results_{lang}（言語別アーカイブ検索）を走査し、
    コンパクトなメトリクス dict を返す。

    Args:
        session_state: パイプラインのセッション状態 dict

    Returns:
        検索メトリクス dict、データなしなら None
    """
    # raw_search_results と raw_search_results_{lang} を収集
    all_results: list[tuple[str, list]] = []

    # ベースキー（新聞検索等）
    base_results = session_state.get("raw_search_results")
    if base_results and isinstance(base_results, list):
        all_results.append(("newspapers", base_results))

    # 言語別キー
    languages: list[str] = []
    for key in list(session_state.keys()):
        if key.startswith("raw_search_results_") and key != "raw_search_results":
            lang = key.replace("raw_search_results_", "")
            lang_results = session_state.get(key)
            if lang_results and isinstance(lang_results, list):
                all_results.append((lang, lang_results))
                languages.append(lang)

    if not all_results:
        return None

    # 言語別 × API 別の内訳
    by_language: dict[str, dict[str, dict[str, int]]] = {}
    # 全言語横断の API 集約
    by_api: dict[str, dict[str, int]] = {}
    all_errors: dict[str, str] = {}
    any_fallback = False
    total_documents = 0

    for label, results_list in all_results:
        lang_apis: dict[str, dict[str, int]] = {}

        for result in results_list:
            if not isinstance(result, dict):
                continue
            extracted = _extract_from_single_result(result)

            for api_name, stats in extracted["per_api"].items():
                # 言語別集約
                if api_name in lang_apis:
                    lang_apis[api_name]["total_hits"] += stats["total_hits"]
                    lang_apis[api_name]["documents_returned"] += stats["documents_returned"]
                else:
                    lang_apis[api_name] = dict(stats)

                # 全言語横断集約
                if api_name in by_api:
                    by_api[api_name]["total_hits"] += stats["total_hits"]
                    by_api[api_name]["documents_returned"] += stats["documents_returned"]
                else:
                    by_api[api_name] = dict(stats)

            all_errors.update(extracted["errors"])
            if extracted["fallback_used"]:
                any_fallback = True

        if lang_apis:
            by_language[label] = lang_apis
            total_documents += sum(
                s["documents_returned"] for s in lang_apis.values()
            )

    metrics: dict[str, Any] = {
        "languages": sorted(languages),
        "total_documents": total_documents,
        "by_language": by_language,
        "by_api": by_api,
    }
    if all_errors:
        metrics["errors"] = all_errors
    if any_fallback:
        metrics["fallback_used"] = True

    return metrics


def save_search_metrics(run_id: str | None, metrics: dict | None) -> None:
    """検索メトリクスを pipeline_runs ドキュメントに保存する（非ブロッキング）。

    Args:
        run_id: パイプライン実行ドキュメントの ID
        metrics: extract_search_metrics() の戻り値。None なら何もしない。
    """
    if not run_id or metrics is None:
        return
    try:
        from shared.firestore import get_firestore_client

        db = get_firestore_client()
        db.collection("pipeline_runs").document(run_id).update({
            "search_metrics": metrics,
            "updated_at": datetime.now(timezone.utc),
        })
        logger.info(
            "検索メトリクス保存: %s (API数=%d, 文書数=%d)",
            run_id,
            len(metrics.get("by_api", {})),
            metrics.get("total_documents", 0),
        )
    except Exception:
        # メトリクス保存失敗はパイプラインをブロックしない
        logger.warning("Failed to save search metrics to Firestore", exc_info=True)
