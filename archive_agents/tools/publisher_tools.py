"""LLM-facing tool functions for the Publisher Agent.

Writes mystery data to Firestore and uploads images to Cloud Storage.
Supports both Firebase emulator (local dev) and production environments.
"""

import json
import os
from datetime import datetime, timezone
from pathlib import Path

from shared.firestore import get_firestore_client, get_storage_bucket


def _generate_mystery_id(db, era: str, city: str) -> str:
    """Generate a unique mystery_id by counting existing documents.

    Args:
        db: Firestore client instance.
        era: The era/year of the mystery (e.g., "1842").
        city: The city name (e.g., "BOSTON").

    Returns:
        Auto-generated mystery_id (e.g., "MYSTERY-1842-BOSTON-002").
    """
    prefix = f"MYSTERY-{era}-{city.upper()}-"

    # Count existing documents with the same era-city prefix
    docs = db.collection("mysteries").stream()

    max_seq = 0
    for doc in docs:
        doc_id = doc.id
        if doc_id.startswith(prefix):
            seq_str = doc_id[len(prefix):]
            try:
                max_seq = max(max_seq, int(seq_str))
            except ValueError:
                continue

    return f"{prefix}{max_seq + 1:03d}"


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

        db = get_firestore_client()

        # Auto-generate mystery_id from era and city
        era = data.get("era")
        city = data.get("city")

        if era and city:
            # Generate mystery_id automatically
            mystery_id = _generate_mystery_id(db, str(era), city)
            data["mystery_id"] = mystery_id
        else:
            # Fallback: try to extract era/city from provided mystery_id
            mystery_id = data.get("mystery_id")
            if mystery_id and mystery_id.startswith("MYSTERY-"):
                parts = mystery_id.split("-")
                if len(parts) >= 4:
                    era = parts[1]
                    city = parts[2]
                    mystery_id = _generate_mystery_id(db, era, city)
                    data["mystery_id"] = mystery_id

        if not data.get("mystery_id"):
            return json.dumps({
                "status": "error",
                "error": "era and city are required for mystery_id generation",
            }, ensure_ascii=False)

        now = datetime.now(timezone.utc)

        # Set timestamps and status
        data["status"] = data.get("status", "pending")
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
        data.setdefault("pipeline_log", [])

        mystery_id = data["mystery_id"]
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

        bucket = get_storage_bucket()
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
