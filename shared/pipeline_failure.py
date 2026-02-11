"""パイプライン失敗ログの Firestore 記録。

パイプラインの各段で失敗が検出された場合に Firestore の
pipeline_failures コレクションに記録する。
Curator が類似テーマの再提案を回避するために使用する。
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Optional

logger = logging.getLogger(__name__)


def log_pipeline_failure(
    theme: str,
    stage: str,
    reason: str,
    run_id: Optional[str] = None,
) -> None:
    """パイプライン失敗を Firestore に記録する（非ブロッキング）。

    Args:
        theme: 調査テーマ
        stage: 失敗した段階（librarian, scholar, polymath, storyteller）
        reason: 失敗理由
        run_id: パイプライン実行 ID（任意）
    """
    try:
        from shared.firestore import get_firestore_client

        db = get_firestore_client()
        doc_ref = db.collection("pipeline_failures").document()
        data = {
            "theme": theme,
            "stage": stage,
            "reason": reason,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        if run_id:
            data["run_id"] = run_id
        doc_ref.set(data)
    except Exception:
        # Firestore への書き込み失敗はパイプラインをブロックしない
        logger.warning("Failed to log pipeline failure to Firestore", exc_info=True)


def get_recent_failures(limit: int = 20) -> list[dict]:
    """最近のパイプライン失敗をFirestoreから取得する。

    Args:
        limit: 取得する最大件数

    Returns:
        失敗記録のリスト（theme, stage, reason, timestamp）
    """
    try:
        from shared.firestore import get_firestore_client

        db = get_firestore_client()
        query = (
            db.collection("pipeline_failures")
            .order_by("timestamp", direction="DESCENDING")
            .limit(limit)
        )
        return [doc.to_dict() for doc in query.stream()]
    except Exception:
        logger.warning("Failed to fetch recent pipeline failures", exc_info=True)
        return []
