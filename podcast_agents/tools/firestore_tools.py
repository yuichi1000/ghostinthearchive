"""Firestore tools for the Podcast pipeline.

`podcasts` コレクション（新設）を操作するツール群。
脚本生成と音声生成の2フェーズに対応。

既存の `mysteries` コレクションからの記事読み込み（load_mystery）も維持。
"""

import json
import logging
from datetime import datetime, timezone

from shared.firestore import get_firestore_client

logger = logging.getLogger(__name__)

PODCASTS_COLLECTION = "podcasts"


def load_mystery(mystery_id: str) -> dict | None:
    """Load a mystery document from Firestore.

    Args:
        mystery_id: The mystery document ID.

    Returns:
        The mystery document data, or None if not found.
    """
    db = get_firestore_client()
    doc = db.collection("mysteries").document(mystery_id).get()
    if not doc.exists:
        return None
    return doc.to_dict()


def create_podcast(mystery_id: str, custom_instructions: str = "") -> str:
    """podcasts コレクションに新規ドキュメントを作成する。

    Args:
        mystery_id: 元記事の mystery ID
        custom_instructions: 管理者からのカスタム指示

    Returns:
        作成された podcast_id
    """
    db = get_firestore_client()
    now = datetime.now(timezone.utc)

    # mystery からタイトルを取得
    mystery = load_mystery(mystery_id)
    mystery_title = mystery.get("title", mystery_id) if mystery else mystery_id

    doc_data = {
        "mystery_id": mystery_id,
        "mystery_title": mystery_title,
        "status": "script_generating",
        "custom_instructions": custom_instructions,
        "script": None,
        "script_ja": None,
        "audio": None,
        "pipeline_run_id": None,
        "created_at": now,
        "updated_at": now,
        "error_message": None,
    }

    _, doc_ref = db.collection(PODCASTS_COLLECTION).add(doc_data)
    podcast_id = doc_ref.id
    logger.info("Podcast created: %s (mystery=%s)", podcast_id, mystery_id)
    return podcast_id


def get_podcast(podcast_id: str) -> dict | None:
    """podcast ドキュメントを取得する。

    Args:
        podcast_id: Podcast ドキュメント ID

    Returns:
        ドキュメントデータ、存在しない場合は None
    """
    db = get_firestore_client()
    doc = db.collection(PODCASTS_COLLECTION).document(podcast_id).get()
    if not doc.exists:
        return None
    data = doc.to_dict()
    data["podcast_id"] = doc.id
    return data


def save_script_result(
    podcast_id: str,
    structured_script: dict,
    script_ja: str,
) -> None:
    """脚本生成結果を保存し、ステータスを script_ready に更新する。

    Args:
        podcast_id: Podcast ドキュメント ID
        structured_script: 構造化脚本 JSON
        script_ja: 日本語訳テキスト
    """
    db = get_firestore_client()
    db.collection(PODCASTS_COLLECTION).document(podcast_id).update({
        "script": structured_script,
        "script_ja": script_ja,
        "status": "script_ready",
        "updated_at": datetime.now(timezone.utc),
        "error_message": None,
    })
    logger.info("Script saved for podcast %s", podcast_id)


def save_audio_result(podcast_id: str, audio_metadata: dict) -> None:
    """音声生成結果を保存し、ステータスを audio_ready に更新する。

    Args:
        podcast_id: Podcast ドキュメント ID
        audio_metadata: 音声メタデータ
            {"gcs_path", "public_url", "duration_seconds", "voice_name", "format"}
    """
    db = get_firestore_client()
    db.collection(PODCASTS_COLLECTION).document(podcast_id).update({
        "audio": audio_metadata,
        "status": "audio_ready",
        "updated_at": datetime.now(timezone.utc),
        "error_message": None,
    })
    logger.info("Audio saved for podcast %s", podcast_id)


def set_podcast_status(
    podcast_id: str,
    status: str,
    error_message: str | None = None,
) -> None:
    """Podcast のステータスを更新する。

    Args:
        podcast_id: Podcast ドキュメント ID
        status: 新しいステータス
        error_message: エラーメッセージ（エラー時のみ）
    """
    db = get_firestore_client()
    update_data: dict = {
        "status": status,
        "updated_at": datetime.now(timezone.utc),
    }
    if error_message is not None:
        update_data["error_message"] = error_message[:500]
    db.collection(PODCASTS_COLLECTION).document(podcast_id).update(update_data)
    logger.info("Podcast %s status → %s", podcast_id, status)
