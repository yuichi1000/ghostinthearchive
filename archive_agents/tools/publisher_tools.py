"""LLM-facing tool functions for the Publisher Agent.

Writes mystery data to Firestore and uploads images to Cloud Storage.
Supports both Firebase emulator (local dev) and production environments.
"""

import json
import os
from datetime import datetime, timezone
from pathlib import Path

from shared.firestore import get_firestore_client, get_storage_bucket


def _generate_mystery_id(classification: str, state_code: str, area_code: str) -> str:
    """Generate a unique mystery_id with timestamp.

    Args:
        classification: 3-letter classification code (e.g., "OCC", "HIS", "FLK").
        state_code: 2-letter US state code (e.g., "MA", "NY").
        area_code: 3-digit telephone area code (e.g., "617", "212").

    Returns:
        Mystery ID in format: {CLS}-{ST}-{AREA}-{YYYYMMDDHHMMSS}
        Example: OCC-MA-617-20260207143025
    """
    now = datetime.now(timezone.utc)
    timestamp = now.strftime("%Y%m%d%H%M%S")
    return f"{classification.upper()}-{state_code.upper()}-{area_code}-{timestamp}"


def publish_mystery(mystery_json: str) -> str:
    """Save a mystery document to Firestore.

    Writes the complete mystery data to the 'mysteries' collection in Firestore.
    Automatically generates mystery_id from classification, state_code, and area_code.

    Args:
        mystery_json: JSON string containing the full mystery data.
            Required fields for ID generation:
            - classification: 3-letter code (HIS, FLK, ANT, OCC, URB, CRM, REL, LOC)
            - state_code: 2-letter US state code (MA, NY, CA, etc.)
            - area_code: 3-digit telephone area code (617, 212, etc.)

            Other required fields: title, summary, discrepancy_detected,
            discrepancy_type, evidence_a, evidence_b, hypothesis,
            alternative_hypotheses, confidence_level, historical_context,
            research_questions, story_hooks.

    Returns:
        JSON string with status and document ID.
    """
    try:
        data = json.loads(mystery_json, strict=False)

        db = get_firestore_client()

        # Auto-generate mystery_id from classification, state_code, and area_code
        classification = data.get("classification")
        state_code = data.get("state_code")
        area_code = data.get("area_code")

        if classification and state_code and area_code:
            # Generate mystery_id automatically
            mystery_id = _generate_mystery_id(classification, state_code, str(area_code))
            data["mystery_id"] = mystery_id
        else:
            return json.dumps({
                "status": "error",
                "error": "classification, state_code, and area_code are required for mystery_id generation",
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
        data["additional_evidence"] = data["additional_evidence"][:5]
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

            # Rename file to mystery_id-based name
            variant_suffix = ""
            for label in ("_sm", "_md", "_lg", "_xl"):
                if p.stem.endswith(label):
                    variant_suffix = label
                    break
            new_filename = f"{mystery_id}{variant_suffix}{p.suffix}"
            blob_name = f"images/{mystery_id}/{new_filename}"
            blob = bucket.blob(blob_name)
            content_type_map = {".png": "image/png", ".webp": "image/webp", ".jpg": "image/jpeg", ".jpeg": "image/jpeg"}
            content_type = content_type_map.get(p.suffix.lower(), "image/png")
            blob.upload_from_filename(str(p), content_type=content_type)

            # エミュレータではmake_public()が使えないため、URLを直接構築
            storage_host = os.environ.get("STORAGE_EMULATOR_HOST", "")
            if storage_host:
                public_url = f"{storage_host}/v0/b/{bucket.name}/o/{blob_name.replace('/', '%2F')}?alt=media"
            else:
                public_url = f"https://storage.googleapis.com/{bucket.name}/{blob_name}"

            uploaded.append({
                "path": local_path,
                "label": variant_suffix.lstrip("_") if variant_suffix else "original",
                "status": "success",
                "storage_path": f"gs://{bucket.name}/{blob_name}",
                "public_url": public_url,
            })

        # Build structured images object for direct use in Firestore
        images = {}
        variants = {}
        for entry in uploaded:
            if entry["status"] != "success":
                continue
            lbl = entry["label"]
            if lbl == "original":
                images["hero"] = entry["public_url"]
            else:
                variants[lbl] = entry["public_url"]
        if variants:
            # Use lg variant as hero if available (higher quality)
            if "lg" in variants:
                images["hero"] = variants["lg"]
            images["variants"] = variants

        return json.dumps({
            "status": "success",
            "mystery_id": mystery_id,
            "uploaded": uploaded,
            "images": images,
        }, ensure_ascii=False)

    except Exception as e:
        return json.dumps({
            "status": "error",
            "error": str(e),
        }, ensure_ascii=False)
