"""Pytest fixtures for Ghost in the Archive tests."""

import sys
from unittest.mock import MagicMock

# =============================================================================
# Mock Google ADK and genai before any imports that might use it
# =============================================================================
# This allows unit tests to run without google-adk or google-genai installed

mock_adk = MagicMock()
mock_adk.agents = MagicMock()
mock_adk.agents.LlmAgent = MagicMock
mock_adk.agents.SequentialAgent = MagicMock
mock_adk.tools = MagicMock()
mock_adk.tools.FunctionTool = MagicMock
mock_adk.tools.base_tool = MagicMock()
mock_adk.tools.tool_context = MagicMock()
mock_adk.agents.run_config = MagicMock()
mock_adk.runners = MagicMock()
mock_adk.sessions = MagicMock()
sys.modules["google.adk"] = mock_adk
sys.modules["google.adk.agents"] = mock_adk.agents
sys.modules["google.adk.agents.run_config"] = mock_adk.agents.run_config
sys.modules["google.adk.runners"] = mock_adk.runners
sys.modules["google.adk.sessions"] = mock_adk.sessions
sys.modules["google.adk.tools"] = mock_adk.tools
sys.modules["google.adk.tools.base_tool"] = mock_adk.tools.base_tool
sys.modules["google.adk.tools.tool_context"] = mock_adk.tools.tool_context

mock_genai = MagicMock()
mock_genai.Client = MagicMock
mock_genai.types = MagicMock()
sys.modules["google.genai"] = mock_genai
sys.modules["google.genai.types"] = mock_genai.types

# Mock firebase_admin
mock_firebase_admin = MagicMock()
mock_firebase_admin.credentials = MagicMock()
mock_firebase_admin.firestore = MagicMock()
mock_firebase_admin.storage = MagicMock()
mock_firebase_admin._apps = {}
sys.modules["firebase_admin"] = mock_firebase_admin
sys.modules["firebase_admin.credentials"] = mock_firebase_admin.credentials
sys.modules["firebase_admin.firestore"] = mock_firebase_admin.firestore
sys.modules["firebase_admin.storage"] = mock_firebase_admin.storage

# Mock google.cloud modules
mock_firestore = MagicMock()
mock_storage = MagicMock()
sys.modules["google.cloud.firestore"] = mock_firestore
sys.modules["google.cloud.storage"] = mock_storage

# Mock google.cloud.firestore_v1 (used by shared/pipeline_run.py for ArrayUnion)
mock_firestore_v1 = MagicMock()
sys.modules["google.cloud.firestore_v1"] = mock_firestore_v1

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict
from unittest.mock import patch

import pytest

# Fixture directory
FIXTURES_DIR = Path(__file__).parent / "fixtures"


# =============================================================================
# Sample Data Fixtures
# =============================================================================


@pytest.fixture
def sample_archive_document_data() -> Dict[str, Any]:
    """Sample data for creating an ArchiveDocument."""
    return {
        "title": "Mystery of the Lost Ship",
        "date": "1842-03-15",
        "source_url": "https://chroniclingamerica.loc.gov/lccn/sn12345/1842-03-15/",
        "summary": "A newspaper article about a missing vessel",
        "language": "en",
        "location": "Boston, Massachusetts",
        "source_type": "newspaper",
        "raw_text": "Full article text here...",
        "record_group": "RG-45",
        "keywords_matched": ["shipwreck", "mystery"],
    }


@pytest.fixture
def sample_evidence_data() -> Dict[str, Any]:
    """Sample data for creating an Evidence object."""
    return {
        "source_type": "newspaper",
        "source_language": "en",
        "source_title": "Boston Daily Advertiser",
        "source_date": "1842-03-15",
        "source_url": "https://chroniclingamerica.loc.gov/lccn/sn12345/",
        "relevant_excerpt": "The vessel was last seen departing the harbor...",
        "location_context": "Boston Harbor",
    }


@pytest.fixture
def sample_historical_context_data() -> Dict[str, Any]:
    """Sample data for creating a HistoricalContext object."""
    return {
        "time_period": "Early 19th Century",
        "geographic_scope": ["Boston", "New York", "Havana"],
        "relevant_events": ["War of 1812 aftermath", "Maritime trade expansion"],
        "key_figures": ["Captain John Smith", "Governor Thomas Gage"],
        "political_climate": "Tensions between US and Spain over Florida",
    }


@pytest.fixture
def sample_mystery_report_data(
    sample_evidence_data: Dict[str, Any],
    sample_historical_context_data: Dict[str, Any],
) -> Dict[str, Any]:
    """Sample data for creating a MysteryReport."""
    return {
        "mystery_id": "MYSTERY-1842-BOSTON-001",
        "title": "The Vanishing of the Santa Maria",
        "summary": "A Spanish merchant vessel disappeared near Boston Harbor in 1842.",
        "discrepancy_detected": "English newspapers report the ship sank, but Spanish records show it arrived in Havana",
        "discrepancy_type": "event_outcome",
        "evidence_a": sample_evidence_data,
        "evidence_b": {
            **sample_evidence_data,
            "source_language": "es",
            "source_title": "Diario de la Marina",
            "relevant_excerpt": "El buque llegó a La Habana sin incidentes...",
        },
        "additional_evidence": [],
        "hypothesis": "The ship may have faked its sinking to smuggle cargo",
        "alternative_hypotheses": ["Mistaken identity", "Clerical error in records"],
        "confidence_level": "medium",
        "historical_context": sample_historical_context_data,
        "research_questions": ["What cargo was the ship carrying?"],
        "story_hooks": ["Ghost ship that never sank"],
    }


@pytest.fixture
def sample_search_results_data(sample_archive_document_data: Dict[str, Any]) -> Dict[str, Any]:
    """Sample data for creating a SearchResults object."""
    return {
        "theme": "Boston maritime mysteries 1840s",
        "documents": [sample_archive_document_data],
        "total_found": 1,
        "sources_searched": ["chronicling_america", "loc_digital"],
    }


# =============================================================================
# Mock Fixtures
# =============================================================================


@pytest.fixture
def mock_firestore_client():
    """Mock Firestore client for unit tests."""
    mock_client = MagicMock()
    mock_collection = MagicMock()
    mock_document = MagicMock()

    mock_client.collection.return_value = mock_collection
    mock_collection.document.return_value = mock_document
    mock_document.set.return_value = None
    mock_document.get.return_value = MagicMock(exists=True, to_dict=lambda: {})

    return mock_client


@pytest.fixture
def mock_storage_bucket():
    """Mock Cloud Storage bucket for unit tests."""
    mock_bucket = MagicMock()
    mock_blob = MagicMock()

    mock_bucket.blob.return_value = mock_blob
    mock_blob.upload_from_filename.return_value = None
    mock_blob.make_public.return_value = None
    mock_blob.public_url = "https://storage.googleapis.com/test-bucket/image.png"

    return mock_bucket


@pytest.fixture
def patch_firestore(mock_firestore_client):
    """Patch Firestore client in shared module."""
    with patch("shared.firestore.get_firestore_client", return_value=mock_firestore_client):
        yield mock_firestore_client


@pytest.fixture
def patch_storage(mock_storage_bucket):
    """Patch Storage bucket in shared module."""
    with patch("shared.firestore.get_storage_bucket", return_value=mock_storage_bucket):
        yield mock_storage_bucket


# =============================================================================
# Time Fixtures
# =============================================================================


@pytest.fixture
def frozen_time():
    """Return a fixed datetime for testing timestamps."""
    return datetime(2024, 1, 15, 12, 0, 0, tzinfo=timezone.utc)


# =============================================================================
# File Fixtures
# =============================================================================


@pytest.fixture
def load_fixture():
    """Factory fixture to load JSON fixtures from the fixtures directory."""
    def _load(filename: str) -> Dict[str, Any]:
        filepath = FIXTURES_DIR / filename
        if not filepath.exists():
            raise FileNotFoundError(f"Fixture not found: {filepath}")
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    return _load
