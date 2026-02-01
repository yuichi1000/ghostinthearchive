"""LLM-facing tool functions for the Publisher Agent.

Writes mystery data to Firestore and uploads images to Cloud Storage.
Supports both Firebase emulator (local dev) and production environments.
"""

import json
import os
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv

# .env を読み込んでエミュレータ設定を反映
load_dotenv(Path(__file__).parent.parent / ".env")

# Storage エミュレータの場合、http:// プレフィックスが必要
_storage_host = os.environ.get("STORAGE_EMULATOR_HOST", "")
if _storage_host and not _storage_host.startswith("http"):
    os.environ["STORAGE_EMULATOR_HOST"] = f"http://{_storage_host}"

import firebase_admin
from firebase_admin import credentials, firestore, storage


def _get_firestore_client():
    """Get a Firestore client, initializing Firebase Admin if needed."""
    if not firebase_admin._apps:
        # エミュレータ使用時はプロジェクトIDのみで初期化
        project_id = os.environ.get("GOOGLE_CLOUD_PROJECT", "ghostinthearchive")
        firebase_admin.initialize_app(
            options={
                "projectId": project_id,
                "storageBucket": f"{project_id}.appspot.com",
            }
        )
    return firestore.client()


def _get_storage_bucket():
    """Get a Cloud Storage bucket."""
    if not firebase_admin._apps:
        _get_firestore_client()  # ensure initialized
    return storage.bucket()


def publish_mystery(mystery_json: str) -> str:
    """Save a mystery document to Firestore.

    Writes the complete mystery data to the 'mysteries' collection in Firestore.
    Automatically sets timestamps and status fields.

    Args:
        mystery_json: JSON string containing the full mystery data.
            Required fields: mystery_id, title, summary, discrepancy_detected,
            discrepancy_type, evidence_a, evidence_b, hypothesis,
            alternative_hypotheses, confidence_level, historical_context,
            research_questions, story_hooks.

    Returns:
        JSON string with status and document ID.
    """
    try:
        data = json.loads(mystery_json, strict=False)

        mystery_id = data.get("mystery_id")
        if not mystery_id:
            return json.dumps({
                "status": "error",
                "error": "mystery_id is required",
            }, ensure_ascii=False)

        now = datetime.now(timezone.utc)

        # Set timestamps and status
        data["status"] = data.get("status", "published")
        data["createdAt"] = now
        data["updatedAt"] = now
        if data["status"] == "published":
            data["publishedAt"] = now
        data["analysis_timestamp"] = data.get("analysis_timestamp", now.isoformat())

        # Ensure required list fields exist
        data.setdefault("additional_evidence", [])
        data.setdefault("alternative_hypotheses", [])
        data.setdefault("research_questions", [])
        data.setdefault("story_hooks", [])

        db = _get_firestore_client()
        db.collection("mysteries").document(mystery_id).set(data)

        return json.dumps({
            "status": "success",
            "mystery_id": mystery_id,
            "firestore_path": f"mysteries/{mystery_id}",
        }, ensure_ascii=False)

    except Exception as e:
        return json.dumps({
            "status": "error",
            "error": str(e),
        }, ensure_ascii=False)


def upload_images(mystery_id: str, image_paths: str) -> str:
    """Upload generated images to Cloud Storage.

    Copies image files from local storage to the Cloud Storage bucket
    (or Storage emulator for local development).

    Args:
        mystery_id: The mystery ID to use as the storage prefix.
        image_paths: JSON string containing a list of local file paths to upload.
            Example: '["data/images/boston_harbor_20260201.png"]'

    Returns:
        JSON string with upload results including public URLs.
    """
    try:
        paths = json.loads(image_paths)
        if isinstance(paths, str):
            paths = [paths]

        bucket = _get_storage_bucket()
        uploaded = []

        for local_path in paths:
            p = Path(local_path)
            if not p.is_absolute():
                p = Path(__file__).parent.parent / p
            if not p.exists():
                uploaded.append({
                    "path": local_path,
                    "status": "error",
                    "error": f"File not found: {p}",
                })
                continue

            blob_name = f"images/{mystery_id}/{p.name}"
            blob = bucket.blob(blob_name)
            blob.upload_from_filename(str(p), content_type="image/png")

            # エミュレータではmake_public()が使えないため、URLを直接構築
            storage_host = os.environ.get("STORAGE_EMULATOR_HOST", "")
            if storage_host:
                public_url = f"{storage_host}/v0/b/{bucket.name}/o/{blob_name.replace('/', '%2F')}?alt=media"
            else:
                public_url = f"https://storage.googleapis.com/{bucket.name}/{blob_name}"

            uploaded.append({
                "path": local_path,
                "status": "success",
                "storage_path": f"gs://{bucket.name}/{blob_name}",
                "public_url": public_url,
            })

        return json.dumps({
            "status": "success",
            "mystery_id": mystery_id,
            "uploaded": uploaded,
        }, ensure_ascii=False)

    except Exception as e:
        return json.dumps({
            "status": "error",
            "error": str(e),
        }, ensure_ascii=False)
