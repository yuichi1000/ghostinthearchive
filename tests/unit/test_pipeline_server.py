"""Unit tests for services/mystery_pipeline.py (FastAPI HTTP wrapper for pipelines)."""

from unittest.mock import AsyncMock, patch

import pytest


@pytest.fixture
def mock_create_pipeline_run():
    """Mock create_pipeline_run to return a fake run_id."""
    with patch(
        "services.mystery_pipeline.create_pipeline_run",
        return_value="test-run-id-123",
    ) as mock:
        yield mock


@pytest.fixture
def mock_create_pipeline_run_failure():
    """Mock create_pipeline_run that raises an exception."""
    with patch(
        "services.mystery_pipeline.create_pipeline_run",
        side_effect=Exception("Firestore unavailable"),
    ) as mock:
        yield mock


@pytest.fixture
def mock_investigate():
    """Mock the investigate function."""
    with patch(
        "services.mystery_pipeline._run_investigate",
        new_callable=AsyncMock,
    ) as mock:
        yield mock


@pytest.fixture
def mock_generate_script():
    """Mock the generate script function."""
    with patch(
        "services.mystery_pipeline._run_generate_script",
        new_callable=AsyncMock,
    ) as mock:
        yield mock


@pytest.fixture
def mock_generate_audio():
    """Mock the generate audio function."""
    with patch(
        "services.mystery_pipeline._run_generate_audio",
        new_callable=AsyncMock,
    ) as mock:
        yield mock


@pytest.fixture
def mock_create_podcast():
    """Mock create_podcast（generate_script_endpoint 内で遅延 import される）."""
    with patch(
        "podcast_agents.tools.firestore_tools.create_podcast",
        return_value="test-podcast-id-456",
    ) as mock:
        yield mock


@pytest.fixture
def client(mock_create_pipeline_run, mock_investigate, mock_generate_script, mock_generate_audio, mock_create_podcast):
    """Create FastAPI test client with mocked dependencies."""
    from fastapi.testclient import TestClient

    from services.mystery_pipeline import app

    return TestClient(app)


class TestHealthEndpoint:
    """Tests for GET /health."""

    def test_health_returns_ok(self, client):
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}


class TestInvestigateEndpoint:
    """Tests for POST /investigate."""

    def test_returns_accepted_with_run_id(self, client, mock_create_pipeline_run):
        response = client.post(
            "/investigate",
            json={"query": "Boston 1840s mystery"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "accepted"
        assert data["run_id"] == "test-run-id-123"

    def test_calls_create_pipeline_run(self, client, mock_create_pipeline_run):
        client.post("/investigate", json={"query": "test query"})
        mock_create_pipeline_run.assert_called_once_with("blog", query="test query")

    def test_missing_query_returns_422(self, client):
        response = client.post("/investigate", json={})
        assert response.status_code == 422

    def test_invalid_query_type_returns_422(self, client):
        response = client.post("/investigate", json={"query": 123})
        assert response.status_code == 422

    def test_create_pipeline_run_failure_returns_500(
        self, mock_create_pipeline_run_failure, mock_investigate
    ):
        from fastapi.testclient import TestClient

        from services.mystery_pipeline import app

        client = TestClient(app)
        response = client.post(
            "/investigate",
            json={"query": "test"},
        )
        assert response.status_code == 500
        assert "error" in response.json()


class TestGenerateScriptEndpoint:
    """Tests for POST /podcast/generate-script."""

    def test_returns_accepted_with_run_id_and_podcast_id(self, client, mock_create_pipeline_run):
        response = client.post(
            "/podcast/generate-script",
            json={"mystery_id": "OCC-MA-617-20260207143025"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "accepted"
        assert data["run_id"] == "test-run-id-123"
        assert data["podcast_id"] == "test-podcast-id-456"

    def test_accepts_custom_instructions(self, client, mock_create_pipeline_run):
        response = client.post(
            "/podcast/generate-script",
            json={
                "mystery_id": "OCC-MA-617-20260207143025",
                "custom_instructions": "ジョーク多めで",
            },
        )
        assert response.status_code == 200

    def test_calls_create_pipeline_run(self, client, mock_create_pipeline_run):
        client.post(
            "/podcast/generate-script",
            json={"mystery_id": "OCC-MA-617-20260207143025"},
        )
        mock_create_pipeline_run.assert_called_once_with(
            "podcast", mystery_id="OCC-MA-617-20260207143025"
        )

    def test_missing_mystery_id_returns_422(self, client):
        response = client.post("/podcast/generate-script", json={})
        assert response.status_code == 422

    def test_create_pipeline_run_failure_returns_500(
        self, mock_create_pipeline_run_failure, mock_generate_script, mock_create_podcast
    ):
        from fastapi.testclient import TestClient

        from services.mystery_pipeline import app

        client = TestClient(app)
        response = client.post(
            "/podcast/generate-script",
            json={"mystery_id": "TEST-ID"},
        )
        assert response.status_code == 500
        assert "error" in response.json()


class TestGenerateAudioEndpoint:
    """Tests for POST /podcast/generate-audio."""

    def test_returns_accepted(self, client):
        response = client.post(
            "/podcast/generate-audio",
            json={"podcast_id": "podcast-123"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "accepted"
        assert data["podcast_id"] == "podcast-123"

    def test_accepts_script_override(self, client):
        response = client.post(
            "/podcast/generate-audio",
            json={
                "podcast_id": "podcast-123",
                "script": {
                    "episode_title": "Test",
                    "segments": [{"type": "intro", "text": "Hello"}],
                },
            },
        )
        assert response.status_code == 200

    def test_accepts_voice_name(self, client):
        response = client.post(
            "/podcast/generate-audio",
            json={
                "podcast_id": "podcast-123",
                "voice_name": "en-US-Wavenet-D",
            },
        )
        assert response.status_code == 200

    def test_missing_podcast_id_returns_422(self, client):
        response = client.post("/podcast/generate-audio", json={})
        assert response.status_code == 422
