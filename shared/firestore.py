"""Shared Firebase infrastructure.

Provides singleton Firestore client and Cloud Storage bucket
used by both mystery_agents and podcast_agents.
"""

import os
from pathlib import Path

from dotenv import load_dotenv

# Load .env from project root
load_dotenv(Path(__file__).parent.parent / ".env")

# Storage emulator requires http:// prefix
_storage_host = os.environ.get("STORAGE_EMULATOR_HOST", "")
if _storage_host and not _storage_host.startswith("http"):
    os.environ["STORAGE_EMULATOR_HOST"] = f"http://{_storage_host}"

import firebase_admin
from firebase_admin import firestore, storage


def get_firestore_client():
    """Get a Firestore client, initializing Firebase Admin if needed."""
    if not firebase_admin._apps:
        project_id = os.environ.get("GOOGLE_CLOUD_PROJECT", "ghostinthearchive")
        firebase_admin.initialize_app(
            options={
                "projectId": project_id,
                "storageBucket": f"{project_id}.appspot.com",
            }
        )
    return firestore.client()


def get_storage_bucket():
    """Get a Cloud Storage bucket."""
    if not firebase_admin._apps:
        get_firestore_client()  # ensure initialized
    return storage.bucket()
