"""Migration script: English-First Content Generation.

Migrates existing Firestore mystery documents from the old field naming
(base = Japanese, *_en = English translations) to the new English-first
naming convention (base = English, *_ja = Japanese).

Migration steps for each document:
  1. Copy title (Japanese) → title_ja, then title_en → title (English)
  2. Copy summary (Japanese) → summary_ja, then summary_en → summary
  3. Repeat for all translatable fields
  4. Mark document as migrated with a timestamp

Usage:
    # Dry run (read-only, prints planned changes)
    python scripts/migrate_english_first.py --dry-run

    # Execute migration
    python scripts/migrate_english_first.py

    # Migrate a single document
    python scripts/migrate_english_first.py --mystery-id OCC-MA-617-20260208143025
"""

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from shared.firestore import get_firestore_client


# Fields to migrate: (base_field, en_suffix_field, ja_suffix_field)
TRANSLATABLE_FIELDS = [
    ("title", "title_en", "title_ja"),
    ("summary", "summary_en", "summary_ja"),
    ("narrative_content", "narrative_content_en", "narrative_content_ja"),
    ("discrepancy_detected", "discrepancy_detected_en", "discrepancy_detected_ja"),
    ("hypothesis", "hypothesis_en", "hypothesis_ja"),
    ("alternative_hypotheses", "alternative_hypotheses_en", "alternative_hypotheses_ja"),
    ("story_hooks", "story_hooks_en", "story_hooks_ja"),
]

# Nested fields under historical_context
CONTEXT_FIELDS = [
    ("political_climate", "historical_context_en", "historical_context_ja"),
]


def migrate_document(doc_ref, data: dict, dry_run: bool = True) -> dict:
    """Migrate a single document to English-first field naming.

    Args:
        doc_ref: Firestore document reference.
        data: Current document data.
        dry_run: If True, only print planned changes without writing.

    Returns:
        Dict with migration status and details.
    """
    mystery_id = doc_ref.id
    update_data = {}
    changes = []

    # Already migrated?
    if data.get("_migrated_english_first"):
        return {"mystery_id": mystery_id, "status": "skipped", "reason": "already migrated"}

    # Check if English translations exist
    has_english = any(data.get(f[1]) for f in TRANSLATABLE_FIELDS)
    if not has_english:
        return {
            "mystery_id": mystery_id,
            "status": "skipped",
            "reason": "no English translations found (*_en fields empty)",
        }

    # Migrate translatable fields
    for base_field, en_field, ja_field in TRANSLATABLE_FIELDS:
        current_base = data.get(base_field)
        en_value = data.get(en_field)

        if en_value:
            # Move current base (Japanese) → *_ja
            if current_base and not data.get(ja_field):
                update_data[ja_field] = current_base
                changes.append(f"  {base_field} (JA) → {ja_field}")

            # Move *_en (English) → base field
            update_data[base_field] = en_value
            changes.append(f"  {en_field} → {base_field}")

    # Migrate historical_context.political_climate
    historical_context = data.get("historical_context", {})
    historical_context_en = data.get("historical_context_en", {})

    if historical_context_en and historical_context_en.get("political_climate"):
        ja_political_climate = historical_context.get("political_climate", "")

        # Save Japanese political_climate to historical_context_ja
        if ja_political_climate and not data.get("historical_context_ja"):
            update_data["historical_context_ja"] = {
                "political_climate": ja_political_climate,
            }
            changes.append("  historical_context.political_climate (JA) → historical_context_ja.political_climate")

        # Update historical_context with English political_climate
        new_context = dict(historical_context)
        new_context["political_climate"] = historical_context_en["political_climate"]
        update_data["historical_context"] = new_context
        changes.append("  historical_context_en.political_climate → historical_context.political_climate")

    # Migrate story_hooks_en
    story_hooks_en = data.get("story_hooks_en")
    if story_hooks_en:
        current_hooks = data.get("story_hooks", [])
        if current_hooks and not data.get("story_hooks_ja"):
            update_data["story_hooks_ja"] = current_hooks
            changes.append("  story_hooks (JA) → story_hooks_ja")
        update_data["story_hooks"] = story_hooks_en
        changes.append("  story_hooks_en → story_hooks")

    # Migrate evidence_*_en fields
    for ev_field in ("evidence_a_en", "evidence_b_en", "additional_evidence_en"):
        en_evidence = data.get(ev_field)
        if en_evidence:
            # Evidence is kept in English, no _ja needed
            # Just note that _en fields exist for cleanup later
            changes.append(f"  {ev_field}: exists (no migration needed, evidence stays in English)")

    if not changes:
        return {"mystery_id": mystery_id, "status": "skipped", "reason": "no changes needed"}

    # Add migration marker and timestamp
    update_data["_migrated_english_first"] = True
    update_data["_migrated_at"] = datetime.now(timezone.utc)
    update_data["updatedAt"] = datetime.now(timezone.utc)

    result = {
        "mystery_id": mystery_id,
        "status": "dry_run" if dry_run else "migrated",
        "changes": changes,
        "fields_updated": len(update_data) - 3,  # Exclude metadata fields
    }

    if dry_run:
        print(f"\n{'='*60}")
        print(f"[DRY RUN] {mystery_id}")
        print(f"{'='*60}")
        for change in changes:
            print(change)
        print(f"  Total fields to update: {result['fields_updated']}")
    else:
        doc_ref.update(update_data)
        print(f"[MIGRATED] {mystery_id} ({result['fields_updated']} fields)")

    return result


def run_migration(dry_run: bool = True, mystery_id: str | None = None):
    """Run the migration on all or a single document.

    Args:
        dry_run: If True, only print planned changes.
        mystery_id: Optional specific mystery ID to migrate.
    """
    db = get_firestore_client()
    collection = db.collection("mysteries")

    print("=" * 60)
    print("English-First Content Generation Migration")
    print(f"Mode: {'DRY RUN' if dry_run else 'LIVE MIGRATION'}")
    print("=" * 60)

    if mystery_id:
        doc_ref = collection.document(mystery_id)
        doc = doc_ref.get()
        if not doc.exists:
            print(f"Error: Document {mystery_id} not found")
            return
        docs = [(doc_ref, doc.to_dict())]
    else:
        docs = [(doc.reference, doc.to_dict()) for doc in collection.stream()]

    print(f"Documents to process: {len(docs)}")

    results = {"migrated": 0, "skipped": 0, "errors": 0, "dry_run": 0}

    for doc_ref, data in docs:
        try:
            result = migrate_document(doc_ref, data, dry_run=dry_run)
            status = result["status"]
            if status in results:
                results[status] += 1
        except Exception as e:
            print(f"[ERROR] {doc_ref.id}: {e}")
            results["errors"] += 1

    print()
    print("=" * 60)
    print("Migration Summary")
    print("=" * 60)
    if dry_run:
        print(f"  Would migrate: {results['dry_run']}")
    else:
        print(f"  Migrated: {results['migrated']}")
    print(f"  Skipped: {results['skipped']}")
    print(f"  Errors: {results['errors']}")

    if dry_run:
        print()
        print("This was a DRY RUN. No changes were made.")
        print("Run without --dry-run to execute the migration.")


def main():
    parser = argparse.ArgumentParser(
        description="Migrate Firestore documents to English-first field naming."
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        default=True,
        help="Print planned changes without writing (default: True)",
    )
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Execute the migration (overrides --dry-run)",
    )
    parser.add_argument(
        "--mystery-id",
        type=str,
        help="Migrate a single mystery document by ID",
    )

    args = parser.parse_args()

    dry_run = not args.execute

    if not dry_run:
        confirm = input(
            "\nThis will modify Firestore documents. Are you sure? (yes/no): "
        )
        if confirm.lower() != "yes":
            print("Migration cancelled.")
            return

    run_migration(dry_run=dry_run, mystery_id=args.mystery_id)


if __name__ == "__main__":
    main()
