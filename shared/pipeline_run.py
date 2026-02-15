"""Pipeline Run Tracker - パイプライン実行進捗の Firestore 管理

`pipeline_runs` コレクションを通じてパイプラインの実行状況をリアルタイムに記録し、
管理画面からのポーリングによる進捗表示を可能にする。

全書き込みは try/except で囲み、進捗トラッキングの失敗がパイプライン本体を阻害しないようにする。
"""

import logging
from datetime import datetime, timezone

from google.cloud.firestore_v1 import ArrayUnion

from shared.firestore import get_firestore_client

logger = logging.getLogger(__name__)

COLLECTION = "pipeline_runs"


def create_pipeline_run(
    run_type: str,
    *,
    query: str | None = None,
    mystery_id: str | None = None,
) -> str | None:
    """パイプライン実行ドキュメントを作成する。

    Args:
        run_type: パイプライン種別 ("blog", "translate", "podcast")
        query: 調査テーマ (blog のみ)
        mystery_id: 記事ID (translate/podcast)

    Returns:
        作成されたドキュメントの ID、失敗時は None
    """
    try:
        db = get_firestore_client()
        now = datetime.now(timezone.utc)
        doc_data = {
            "type": run_type,
            "status": "running",
            "query": query,
            "mystery_id": mystery_id,
            "current_agent": None,
            "pipeline_log": [],
            "started_at": now,
            "updated_at": now,
            "completed_at": None,
            "error_message": None,
        }
        _, doc_ref = db.collection(COLLECTION).add(doc_data)
        logger.info("Pipeline run created: %s (type=%s)", doc_ref.id, run_type)
        return doc_ref.id
    except Exception:
        logger.exception("Failed to create pipeline run")
        return None


def update_agent_started(
    run_id: str | None,
    agent_name: str,
    log_entry: dict,
) -> int | None:
    """エージェント開始をログに追加する。

    ArrayUnion でアトミックに追加する。

    Args:
        run_id: パイプライン実行ドキュメントの ID
        agent_name: エージェント名
        log_entry: PipelineLogger 形式のログエントリ

    Returns:
        追加されたログエントリのインデックス（完了時の更新用）、失敗時は None
    """
    if not run_id:
        return None
    try:
        db = get_firestore_client()
        doc_ref = db.collection(COLLECTION).document(run_id)
        doc_ref.update({
            "current_agent": agent_name,
            "pipeline_log": ArrayUnion([log_entry]),
            "updated_at": datetime.now(timezone.utc),
        })
        # ArrayUnion 後のインデックスを取得するために read
        doc = doc_ref.get()
        if doc.exists:
            logs = doc.to_dict().get("pipeline_log", [])
            return len(logs) - 1
        return None
    except Exception:
        logger.exception("Failed to update agent started: %s", agent_name)
        return None


def update_agent_completed(
    run_id: str | None,
    log_index: int | None,
    updated_entry: dict,
) -> None:
    """エージェント完了でログエントリを更新する。

    配列要素の更新は Firestore の制約上 read-then-write。

    Args:
        run_id: パイプライン実行ドキュメントの ID
        log_index: 更新するログエントリのインデックス
        updated_entry: 更新後のログエントリ
    """
    if not run_id or log_index is None:
        return
    try:
        db = get_firestore_client()
        doc_ref = db.collection(COLLECTION).document(run_id)
        doc = doc_ref.get()
        if not doc.exists:
            return
        logs = doc.to_dict().get("pipeline_log", [])
        if log_index < len(logs):
            logs[log_index] = updated_entry
            doc_ref.update({
                "current_agent": None,
                "pipeline_log": logs,
                "updated_at": datetime.now(timezone.utc),
            })
    except Exception:
        logger.exception("Failed to update agent completed at index %s", log_index)


def complete_pipeline_run(
    run_id: str | None,
    *,
    mystery_id: str | None = None,
) -> None:
    """パイプライン実行を完了としてマークする。

    Args:
        run_id: パイプライン実行ドキュメントの ID
        mystery_id: 記事ID（blog パイプラインで Publisher 完了後にセット）
    """
    if not run_id:
        return
    try:
        db = get_firestore_client()
        now = datetime.now(timezone.utc)
        update_data: dict = {
            "status": "completed",
            "current_agent": None,
            "updated_at": now,
            "completed_at": now,
        }
        if mystery_id is not None:
            update_data["mystery_id"] = mystery_id
        db.collection(COLLECTION).document(run_id).update(update_data)
        logger.info("Pipeline run completed: %s", run_id)
    except Exception:
        logger.exception("Failed to complete pipeline run: %s", run_id)


def error_pipeline_run(
    run_id: str | None,
    error_message: str,
    error_detail: dict | None = None,
) -> None:
    """パイプライン実行をエラーとしてマークする。

    Args:
        run_id: パイプライン実行ドキュメントの ID
        error_message: エラーメッセージ
        error_detail: デバッグ用の詳細情報（セッション状態サマリ等）
    """
    if not run_id:
        return
    try:
        db = get_firestore_client()
        now = datetime.now(timezone.utc)
        update_data: dict = {
            "status": "error",
            "current_agent": None,
            "updated_at": now,
            "completed_at": now,
            "error_message": error_message[:500],
        }
        if error_detail:
            update_data["error_detail"] = error_detail
        db.collection(COLLECTION).document(run_id).update(update_data)
        logger.info("Pipeline run errored: %s", run_id)
    except Exception:
        logger.exception("Failed to mark pipeline run as error: %s", run_id)
