"""Firestore tools for the Translator pipeline.

Reads mystery data from Firestore and writes Japanese translation results back.
Used for standalone translation of already-published mysteries (legacy flow).
In the new English-first flow, translation happens within the blog pipeline
before publishing, so these tools are mainly for the standalone translate_main.py.
"""

import json
import os
import re
from datetime import datetime, timezone

import requests

from shared.firestore import get_firestore_client


def _extract_json_from_markdown(text: str) -> str:
    """Extract JSON from Markdown code block if present.

    The Translator agent sometimes wraps JSON output in Markdown code blocks
    like ```json ... ```. This function extracts the JSON content.

    Args:
        text: Raw text that may contain Markdown code blocks.

    Returns:
        Extracted JSON string without Markdown formatting.
    """
    if not text:
        return text

    # Match ```json ... ``` or ``` ... ```
    pattern = r'```(?:json)?\s*([\s\S]*?)\s*```'
    match = re.search(pattern, text)
    if match:
        return match.group(1).strip()
    return text.strip()


def load_mystery_for_translation(mystery_id: str) -> dict | None:
    """Load a mystery document from Firestore for translation.

    Args:
        mystery_id: The mystery document ID.

    Returns:
        Dictionary with fields to translate, or None if not found.
    """
    db = get_firestore_client()
    doc = db.collection("mysteries").document(mystery_id).get()
    if not doc.exists:
        return None

    data = doc.to_dict()

    # Extract translatable fields (English base fields)
    historical_context = data.get("historical_context", {})

    return {
        "mystery_id": mystery_id,
        "title": data.get("title", ""),
        "summary": data.get("summary", ""),
        "narrative_content": data.get("narrative_content", ""),
        "discrepancy_detected": data.get("discrepancy_detected", ""),
        "hypothesis": data.get("hypothesis", ""),
        "alternative_hypotheses": data.get("alternative_hypotheses", []),
        "political_climate": historical_context.get("political_climate", ""),
        "story_hooks": data.get("story_hooks", []),
    }


def save_translation_result(mystery_id: str, translation_json: str) -> str:
    """Save Japanese translation results to Firestore.

    Updates the mystery document with Japanese translations (*_ja fields).
    Does NOT change the status — in the new flow, articles are published
    with both EN and JA content from the start.

    Args:
        mystery_id: The mystery document ID.
        translation_json: JSON string with translation results (*_ja fields).

    Returns:
        JSON string with status.
    """
    try:
        db = get_firestore_client()
        now = datetime.now(timezone.utc)

        # Parse translation result (extract from Markdown code block if present)
        try:
            clean_json = _extract_json_from_markdown(translation_json)
            translation = json.loads(clean_json)
        except (json.JSONDecodeError, TypeError) as e:
            raise ValueError(f"Invalid translation JSON: {e}")

        update_data = {
            "title_ja": translation.get("title_ja", ""),
            "summary_ja": translation.get("summary_ja", ""),
            "narrative_content_ja": translation.get("narrative_content_ja", ""),
            "discrepancy_detected_ja": translation.get("discrepancy_detected_ja", ""),
            "hypothesis_ja": translation.get("hypothesis_ja", ""),
            "alternative_hypotheses_ja": translation.get("alternative_hypotheses_ja", []),
            "historical_context_ja": {
                "political_climate": translation.get("historical_context_ja", {}).get(
                    "political_climate",
                    translation.get("political_climate_ja", ""),
                ),
            },
            "story_hooks_ja": translation.get("story_hooks_ja", []),
            "translatedAt": now,
            "updatedAt": now,
        }

        db.collection("mysteries").document(mystery_id).update(update_data)

        # Trigger ISR revalidation
        _trigger_revalidation(mystery_id)

        return json.dumps({
            "status": "success",
            "mystery_id": mystery_id,
            "message": "Japanese translation saved",
        }, ensure_ascii=False)

    except Exception as e:
        # Mark as error
        set_translation_error(mystery_id)

        return json.dumps({
            "status": "error",
            "mystery_id": mystery_id,
            "error": str(e),
        }, ensure_ascii=False)


def set_translation_error(mystery_id: str) -> None:
    """Set mystery status to error when translation fails.

    Args:
        mystery_id: The mystery document ID.
    """
    try:
        db = get_firestore_client()
        db.collection("mysteries").document(mystery_id).update({
            "status": "error",
            "updatedAt": datetime.now(timezone.utc),
        })
    except Exception:
        pass  # Best effort


def _trigger_revalidation(mystery_id: str) -> None:
    """Trigger ISR revalidation for the mystery.

    Args:
        mystery_id: The mystery document ID.
    """
    web_url = os.environ.get("WEB_URL", "http://localhost:3000")
    revalidate_secret = os.environ.get("REVALIDATE_SECRET", "")

    if not revalidate_secret:
        return  # Skip revalidation if secret not configured

    try:
        requests.post(
            f"{web_url}/api/revalidate",
            json={
                "mysteryId": mystery_id,
                "secret": revalidate_secret,
            },
            timeout=10,
        )
    except Exception:
        pass  # Best effort, don't fail translation on revalidation error
