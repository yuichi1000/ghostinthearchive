"""Firestore tools for the Translator pipeline.

Reads mystery data from Firestore and writes translation results back.
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


def _extract_translatable_evidence(evidence: dict) -> dict:
    """Extract translatable fields from an Evidence object.

    Args:
        evidence: Evidence dictionary from Firestore.

    Returns:
        Dictionary with evidence fields for translation.
    """
    return {
        "source_type": evidence.get("source_type", ""),
        "source_language": evidence.get("source_language", ""),
        "source_title": evidence.get("source_title", ""),
        "source_date": evidence.get("source_date"),
        "source_url": evidence.get("source_url", ""),
        "relevant_excerpt": evidence.get("relevant_excerpt", ""),
        "location_context": evidence.get("location_context"),
    }


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

    # Extract translatable fields
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
        "evidence_a": _extract_translatable_evidence(data.get("evidence_a", {})),
        "evidence_b": _extract_translatable_evidence(data.get("evidence_b", {})),
        "additional_evidence": [
            _extract_translatable_evidence(ev)
            for ev in data.get("additional_evidence", [])
        ],
    }


def save_translation_result(mystery_id: str, translation_json: str) -> str:
    """Save translation results to Firestore and publish the mystery.

    Updates the mystery document with English translations,
    sets status to "published", and triggers ISR revalidation.

    Args:
        mystery_id: The mystery document ID.
        translation_json: JSON string with translation results.

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
            "title_en": translation.get("title_en", ""),
            "summary_en": translation.get("summary_en", ""),
            "narrative_content_en": translation.get("narrative_content_en", ""),
            "discrepancy_detected_en": translation.get("discrepancy_detected_en", ""),
            "hypothesis_en": translation.get("hypothesis_en", ""),
            "alternative_hypotheses_en": translation.get("alternative_hypotheses_en", []),
            "historical_context_en": {
                "political_climate": translation.get("political_climate_en", ""),
            },
            "story_hooks_en": translation.get("story_hooks_en", []),
            "evidence_a_en": translation.get("evidence_a_en", {}),
            "evidence_b_en": translation.get("evidence_b_en", {}),
            "additional_evidence_en": translation.get("additional_evidence_en", []),
            "status": "published",
            "translatedAt": now,
            "publishedAt": now,
            "updatedAt": now,
        }

        db.collection("mysteries").document(mystery_id).update(update_data)

        # Trigger ISR revalidation
        _trigger_revalidation(mystery_id)

        return json.dumps({
            "status": "success",
            "mystery_id": mystery_id,
            "message": "Translation saved and mystery published",
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
    """Trigger ISR revalidation for the published mystery.

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
