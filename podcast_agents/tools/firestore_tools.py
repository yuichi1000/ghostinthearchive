"""Firestore tools for the Podcast pipeline.

Reads mystery data from Firestore and writes podcast results back.
"""

import json
from datetime import datetime, timezone

from shared.firestore import get_firestore_client


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


def save_podcast_result(mystery_id: str, podcast_script: str, audio_assets: str) -> str:
    """Save podcast generation results to Firestore.

    Updates the mystery document with podcast_script, audio_assets,
    and sets podcast_status to "completed".

    Args:
        mystery_id: The mystery document ID.
        podcast_script: The generated podcast script text.
        audio_assets: JSON string of audio asset metadata.

    Returns:
        JSON string with status.
    """
    try:
        db = get_firestore_client()
        now = datetime.now(timezone.utc)

        update_data = {
            "podcast_script": podcast_script,
            "podcast_status": "completed",
            "updatedAt": now,
        }

        if audio_assets:
            try:
                update_data["audio_assets"] = json.loads(audio_assets)
            except (json.JSONDecodeError, TypeError):
                update_data["audio_assets"] = audio_assets

        db.collection("mysteries").document(mystery_id).update(update_data)

        return json.dumps({
            "status": "success",
            "mystery_id": mystery_id,
        }, ensure_ascii=False)

    except Exception as e:
        # Mark as error
        try:
            db = get_firestore_client()
            db.collection("mysteries").document(mystery_id).update({
                "podcast_status": "error",
                "updatedAt": datetime.now(timezone.utc),
            })
        except Exception:
            pass

        return json.dumps({
            "status": "error",
            "error": str(e),
        }, ensure_ascii=False)


def set_podcast_status(mystery_id: str, status: str) -> None:
    """Update podcast_status field in Firestore.

    Args:
        mystery_id: The mystery document ID.
        status: One of "generating", "completed", "error".
    """
    db = get_firestore_client()
    db.collection("mysteries").document(mystery_id).update({
        "podcast_status": status,
        "updatedAt": datetime.now(timezone.utc),
    })
