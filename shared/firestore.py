"""Shared Firebase infrastructure.

Provides singleton Firestore client and Cloud Storage bucket
used by both mystery_agents and podcast_agents.
"""

import os
from pathlib import Path

from dotenv import load_dotenv

# Load .env from project root
load_dotenv(Path(__file__).parent.parent / ".env")

import firebase_admin
from firebase_admin import firestore, storage


def get_firestore_client():
    """Get a Firestore client, initializing Firebase Admin if needed."""
    if not firebase_admin._apps:
        project_id = os.environ.get("GOOGLE_CLOUD_PROJECT", "ghostinthearchive")
        firebase_admin.initialize_app(
            options={
                "projectId": project_id,
                "storageBucket": f"{project_id}.firebasestorage.app",
            }
        )
    return firestore.client()


def get_storage_bucket():
    """Get a Cloud Storage bucket.

    Emulator モードでは firebase_admin.storage を経由せず、
    AnonymousCredentials で直接 google.cloud.storage.Client を生成する。
    firebase_admin は ADC 認証情報を内部で使い回すため、
    STORAGE_EMULATOR_HOST を設定しても emulator に接続できない問題を回避する。
    """
    storage_host = os.environ.get("STORAGE_EMULATOR_HOST", "")
    if storage_host:
        # Emulator モード: firebase_admin の認証を回避し anonymous credentials で接続
        from google.auth.credentials import AnonymousCredentials
        from google.cloud import storage as gcs_storage

        api_endpoint = storage_host if storage_host.startswith("http") else f"http://{storage_host}"
        project_id = os.environ.get("GOOGLE_CLOUD_PROJECT", "ghostinthearchive")
        client = gcs_storage.Client(
            project=project_id,
            credentials=AnonymousCredentials(),
            client_options={"api_endpoint": api_endpoint},
        )
        return client.bucket(f"{project_id}.firebasestorage.app")
    else:
        # 本番モード: firebase_admin 経由
        if not firebase_admin._apps:
            get_firestore_client()
        return storage.bucket()
