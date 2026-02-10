"""Unit tests for curator_server.py (FastAPI HTTP wrapper).

Updated for English-first: Curator returns English suggestions,
then Translator adds Japanese translations.
"""

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


@pytest.fixture
def mock_run_curator():
    """Mock the run_curator function to return English suggestions."""
    sample_suggestions = [
        {
            "theme": "Ghost Ship Legends and Maritime Accident Records in 1850s Boston Harbor",
            "description": "Cross-referencing ghost ship sightings around Boston Harbor with actual maritime accident records reveals intriguing contradictions.",
        },
        {
            "theme": "The Voodoo Queen of New Orleans and 1870s Epidemic Records",
            "description": "Exploring the connection between the legend of Marie Laveau and actual epidemic records.",
        },
    ]
    with patch("curator_server.run_curator", new_callable=AsyncMock, return_value=sample_suggestions) as mock:
        yield mock


@pytest.fixture
def mock_translate_suggestions():
    """Mock translate_suggestions to return bilingual suggestions."""
    async def _translate(suggestions):
        bilingual = []
        for s in suggestions:
            bilingual.append({
                "theme": s["theme"],
                "description": s["description"],
                "theme_ja": f"[JA] {s['theme']}",
                "description_ja": f"[JA] {s['description']}",
            })
        return bilingual

    with patch("curator_server.translate_suggestions", new_callable=AsyncMock, side_effect=_translate) as mock:
        yield mock


@pytest.fixture
def client(mock_run_curator, mock_translate_suggestions):
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

    def test_suggest_theme_returns_bilingual_suggestions(self, client, mock_run_curator):
        response = client.post("/suggest-theme")
        assert response.status_code == 200
        data = response.json()
        assert "suggestions" in data
        assert len(data["suggestions"]) == 2
        # English fields
        assert data["suggestions"][0]["theme"] == "Ghost Ship Legends and Maritime Accident Records in 1850s Boston Harbor"
        assert "description" in data["suggestions"][0]
        # Japanese fields
        assert "theme_ja" in data["suggestions"][0]
        assert "description_ja" in data["suggestions"][0]

    def test_suggest_theme_calls_run_curator(self, client, mock_run_curator):
        client.post("/suggest-theme")
        mock_run_curator.assert_called_once()

    def test_suggest_theme_falls_back_to_english_when_translation_fails(self, mock_run_curator):
        """Should return English-only suggestions when translation fails."""
        with patch("curator_server.translate_suggestions", new_callable=AsyncMock,
                    side_effect=Exception("Translation error")):
            from fastapi.testclient import TestClient
            from curator_server import app
            client = TestClient(app)

            response = client.post("/suggest-theme")
            assert response.status_code == 200
            data = response.json()
            assert len(data["suggestions"]) == 2
            # English fields should be present
            assert "theme" in data["suggestions"][0]

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
