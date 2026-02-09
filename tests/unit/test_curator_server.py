"""Unit tests for curator_server.py (FastAPI HTTP wrapper)."""

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


@pytest.fixture
def mock_run_curator():
    """Mock the run_curator function to avoid ADK/Firestore dependencies."""
    sample_suggestions = [
        {
            "theme": "1850年代ボストン港の幽霊船伝説と海難事故記録の矛盾",
            "description": "ボストン港周辺の幽霊船目撃談と実際の海難事故記録を照合すると興味深い矛盾が浮かび上がる。",
        },
        {
            "theme": "ニューオーリンズのブードゥー女王と1870年代の疫病記録",
            "description": "マリー・ラヴォーの伝説と実際の疫病記録の関連性を探る。",
        },
    ]
    with patch("curator_server.run_curator", new_callable=AsyncMock, return_value=sample_suggestions) as mock:
        yield mock


@pytest.fixture
def client(mock_run_curator):
    """Create FastAPI test client with mocked dependencies."""
    from fastapi.testclient import TestClient

    from curator_server import app

    return TestClient(app)


class TestHealthEndpoint:
    """Tests for GET /health."""

    def test_health_returns_ok(self, client):
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}


class TestSuggestThemeEndpoint:
    """Tests for POST /suggest-theme."""

    def test_suggest_theme_returns_suggestions(self, client, mock_run_curator):
        response = client.post("/suggest-theme")
        assert response.status_code == 200
        data = response.json()
        assert "suggestions" in data
        assert len(data["suggestions"]) == 2
        assert data["suggestions"][0]["theme"] == "1850年代ボストン港の幽霊船伝説と海難事故記録の矛盾"

    def test_suggest_theme_calls_run_curator(self, client, mock_run_curator):
        client.post("/suggest-theme")
        mock_run_curator.assert_called_once()

    def test_suggest_theme_handles_json_parse_error(self, client):
        with patch(
            "curator_server.run_curator",
            new_callable=AsyncMock,
            side_effect=json.JSONDecodeError("Expecting value", "", 0),
        ):
            response = client.post("/suggest-theme")
            assert response.status_code == 500
            data = response.json()
            assert "error" in data
            assert "parse" in data["error"].lower()

    def test_suggest_theme_handles_unexpected_error(self, client):
        with patch(
            "curator_server.run_curator",
            new_callable=AsyncMock,
            side_effect=RuntimeError("Agent failed"),
        ):
            response = client.post("/suggest-theme")
            assert response.status_code == 500
            data = response.json()
            assert "error" in data


class TestGetExistingTitles:
    """Tests for get_existing_titles helper."""

    def test_returns_titles_from_firestore(self):
        mock_doc1 = MagicMock()
        mock_doc1.to_dict.return_value = {"title": "Mystery A"}
        mock_doc2 = MagicMock()
        mock_doc2.to_dict.return_value = {"title": "Mystery B"}

        mock_db = MagicMock()
        mock_db.collection.return_value.select.return_value.stream.return_value = [
            mock_doc1,
            mock_doc2,
        ]

        with patch("curator_server.get_firestore_client", return_value=mock_db):
            from curator_server import get_existing_titles

            titles = get_existing_titles()
            assert titles == ["Mystery A", "Mystery B"]

    def test_returns_empty_list_on_error(self):
        with patch(
            "curator_server.get_firestore_client",
            side_effect=Exception("Connection failed"),
        ):
            from curator_server import get_existing_titles

            titles = get_existing_titles()
            assert titles == []

    def test_skips_documents_without_title(self):
        mock_doc1 = MagicMock()
        mock_doc1.to_dict.return_value = {"title": "Mystery A"}
        mock_doc2 = MagicMock()
        mock_doc2.to_dict.return_value = {}

        mock_db = MagicMock()
        mock_db.collection.return_value.select.return_value.stream.return_value = [
            mock_doc1,
            mock_doc2,
        ]

        with patch("curator_server.get_firestore_client", return_value=mock_db):
            from curator_server import get_existing_titles

            titles = get_existing_titles()
            assert titles == ["Mystery A"]
