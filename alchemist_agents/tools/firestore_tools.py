"""Firestore tools for the Merch Design pipeline.

`product_designs` コレクションを操作するツール群。
デザイン企画とレンダリングの2フェーズに対応。

podcast_agents/tools/firestore_tools.py と同パターン。
"""

import logging
from datetime import datetime, timezone

from shared.firestore import get_firestore_client

logger = logging.getLogger(__name__)

DESIGNS_COLLECTION = "product_designs"


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


def create_design(
    mystery_id: str,
    custom_instructions: str = "",
    *,
    pipeline_run_id: str | None = None,
) -> str:
    """product_designs コレクションに新規ドキュメントを作成する。

    Args:
        mystery_id: 元記事の mystery ID
        custom_instructions: 管理者からのカスタム指示
        pipeline_run_id: 事前作成済みの pipeline_run ID

    Returns:
        作成された design_id
    """
    db = get_firestore_client()
    now = datetime.now(timezone.utc)

    # mystery からタイトル・リージョンを取得
    mystery = load_mystery(mystery_id)
    mystery_title = mystery.get("title", mystery_id) if mystery else mystery_id
    region = ""
    if mystery:
        # mystery_id のフォーマットから国コードを抽出（例: OCC-US-BOS-...）
        parts = mystery_id.split("-")
        if len(parts) >= 2:
            region = parts[1]

    doc_data = {
        "mystery_id": mystery_id,
        "mystery_title": mystery_title,
        "region": region,
        "status": "designing",
        "custom_instructions": custom_instructions,
        "proposal": None,
        "assets": None,
        "pipeline_run_id": pipeline_run_id,
        "created_at": now,
        "updated_at": now,
        "error_message": None,
    }

    _, doc_ref = db.collection(DESIGNS_COLLECTION).add(doc_data)
    design_id = doc_ref.id
    logger.info("Design created: %s (mystery=%s)", design_id, mystery_id)
    return design_id


def get_design(design_id: str) -> dict | None:
    """design ドキュメントを取得する。

    Args:
        design_id: Design ドキュメント ID

    Returns:
        ドキュメントデータ、存在しない場合は None
    """
    db = get_firestore_client()
    doc = db.collection(DESIGNS_COLLECTION).document(design_id).get()
    if not doc.exists:
        return None
    data = doc.to_dict()
    data["design_id"] = doc.id
    return data


def save_design_result(
    design_id: str,
    proposal: dict,
) -> None:
    """デザイン提案結果を保存し、ステータスを design_ready に更新する。

    Args:
        design_id: Design ドキュメント ID
        proposal: 構造化デザイン提案 JSON
    """
    db = get_firestore_client()
    db.collection(DESIGNS_COLLECTION).document(design_id).update({
        "proposal": proposal,
        "status": "design_ready",
        "updated_at": datetime.now(timezone.utc),
        "error_message": None,
    })
    logger.info("Design proposal saved for %s", design_id)


def save_render_result(design_id: str, assets: list[dict]) -> None:
    """レンダリング結果を保存し、ステータスを render_ready に更新する。

    Args:
        design_id: Design ドキュメント ID
        assets: アセットメタデータのリスト
            各要素: {"product_type", "layer", "gcs_path", "public_url", "aspect_ratio"}
    """
    db = get_firestore_client()
    db.collection(DESIGNS_COLLECTION).document(design_id).update({
        "assets": assets,
        "status": "render_ready",
        "updated_at": datetime.now(timezone.utc),
        "error_message": None,
    })
    logger.info("Render result saved for %s (%d assets)", design_id, len(assets))


def set_design_status(
    design_id: str,
    status: str,
    error_message: str | None = None,
) -> None:
    """Design のステータスを更新する。

    Args:
        design_id: Design ドキュメント ID
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
    db.collection(DESIGNS_COLLECTION).document(design_id).update(update_data)
    logger.info("Design %s status → %s", design_id, status)


def upload_design_assets(
    mystery_id: str,
    design_id: str,
    asset_paths: list[dict],
) -> list[dict]:
    """デザインアセットを Cloud Storage にアップロードする。

    Args:
        mystery_id: Mystery ID（GCS パス構成用）
        design_id: Design ID（GCS パス構成用）
        asset_paths: ローカルファイルパス + メタデータのリスト
            各要素: {"filepath", "product_type", "layer", "aspect_ratio"}

    Returns:
        アップロード結果のリスト
            各要素: {"product_type", "layer", "gcs_path", "public_url", "aspect_ratio"}
    """
    from shared.firestore import get_storage_bucket
    from pathlib import Path

    bucket = get_storage_bucket()
    results = []

    for asset in asset_paths:
        filepath = Path(asset["filepath"])
        if not filepath.exists():
            logger.warning("Asset file not found: %s", filepath)
            continue

        # GCS パス: designs/{mystery_id}/{design_id}/{filename}
        gcs_path = f"designs/{mystery_id}/{design_id}/{filepath.name}"
        blob = bucket.blob(gcs_path)

        # Content-Type を推定
        suffix = filepath.suffix.lower()
        content_type = {
            ".png": "image/png",
            ".webp": "image/webp",
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
        }.get(suffix, "image/png")

        blob.upload_from_filename(str(filepath), content_type=content_type)
        blob.make_public()

        results.append({
            "product_type": asset.get("product_type", ""),
            "layer": asset.get("layer", ""),
            "gcs_path": f"gs://{bucket.name}/{gcs_path}",
            "public_url": blob.public_url,
            "aspect_ratio": asset.get("aspect_ratio", ""),
        })

        logger.info("Uploaded: %s → %s", filepath.name, gcs_path)

    return results
