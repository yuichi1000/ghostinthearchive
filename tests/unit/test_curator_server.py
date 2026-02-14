"""Unit tests for services/curator.py (FastAPI HTTP wrapper).

Updated for English-first: Curator returns English suggestions,
then Translator adds Japanese translations.
"""

import json
import logging
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


@pytest.fixture
def mock_run_curator():
    """Mock the run_curator function to return English suggestions."""
    sample_suggestions = [
        {
            "theme": "Ghost Ship Legends and Maritime Accident Records in 1850s Boston Harbor",
            "description": "Cross-referencing ghost ship sightings around Boston Harbor with actual maritime accident records reveals intriguing contradictions.",
            "category": "OCC",
        },
        {
            "theme": "The Voodoo Queen of New Orleans and 1870s Epidemic Records",
            "description": "Exploring the connection between the legend of Marie Laveau and actual epidemic records.",
            "category": "FLK",
        },
    ]
    with patch("services.curator.run_curator", new_callable=AsyncMock, return_value=sample_suggestions) as mock:
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

    with patch("services.curator.translate_suggestions", new_callable=AsyncMock, side_effect=_translate) as mock:
        yield mock


@pytest.fixture
def client(mock_run_curator, mock_translate_suggestions):
    """Create FastAPI test client with mocked dependencies."""
    from fastapi.testclient import TestClient

    from services.curator import app

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
        with patch("services.curator.translate_suggestions", new_callable=AsyncMock,
                    side_effect=Exception("Translation error")):
            from fastapi.testclient import TestClient
            from services.curator import app
            client = TestClient(app)

            response = client.post("/suggest-theme")
            assert response.status_code == 200
            data = response.json()
            assert len(data["suggestions"]) == 2
            # English fields should be present
            assert "theme" in data["suggestions"][0]

    def test_suggest_theme_handles_json_parse_error(self, client):
        with patch(
            "services.curator.run_curator",
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
            "services.curator.run_curator",
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

        with patch("curator_agents.queries.get_firestore_client", return_value=mock_db):
            from curator_agents.queries import get_existing_titles

            titles = get_existing_titles()
            assert titles == ["Mystery A", "Mystery B"]

    def test_returns_empty_list_on_error(self):
        with patch(
            "curator_agents.queries.get_firestore_client",
            side_effect=Exception("Connection failed"),
        ):
            from curator_agents.queries import get_existing_titles

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

        with patch("curator_agents.queries.get_firestore_client", return_value=mock_db):
            from curator_agents.queries import get_existing_titles

            titles = get_existing_titles()
            assert titles == ["Mystery A"]


class TestGetCategoryDistribution:
    """Tests for get_category_distribution helper."""

    def test_counts_categories_from_mystery_ids(self):
        mock_docs = []
        ids = [
            "HIS-MA-617-20260101120000",
            "HIS-NY-212-20260102120000",
            "OCC-PA-215-20260103120000",
            "FLK-LA-504-20260104120000",
        ]
        for mid in ids:
            doc = MagicMock()
            doc.to_dict.return_value = {"mystery_id": mid}
            mock_docs.append(doc)

        mock_db = MagicMock()
        mock_db.collection.return_value.select.return_value.stream.return_value = mock_docs

        with patch("curator_agents.queries.get_firestore_client", return_value=mock_db):
            from curator_agents.queries import get_category_distribution

            dist = get_category_distribution()
            assert dist == {"HIS": 2, "OCC": 1, "FLK": 1}

    def test_returns_empty_dict_on_error(self):
        with patch(
            "curator_agents.queries.get_firestore_client",
            side_effect=Exception("Connection failed"),
        ):
            from curator_agents.queries import get_category_distribution

            dist = get_category_distribution()
            assert dist == {}

    def test_skips_invalid_mystery_ids(self):
        mock_docs = []
        # 有効な ID
        doc1 = MagicMock()
        doc1.to_dict.return_value = {"mystery_id": "CRM-IL-312-20260101120000"}
        mock_docs.append(doc1)
        # 空の mystery_id
        doc2 = MagicMock()
        doc2.to_dict.return_value = {"mystery_id": ""}
        mock_docs.append(doc2)
        # mystery_id フィールドなし
        doc3 = MagicMock()
        doc3.to_dict.return_value = {}
        mock_docs.append(doc3)
        # 不正なプレフィックス
        doc4 = MagicMock()
        doc4.to_dict.return_value = {"mystery_id": "XXX-MA-617-20260101120000"}
        mock_docs.append(doc4)

        mock_db = MagicMock()
        mock_db.collection.return_value.select.return_value.stream.return_value = mock_docs

        with patch("curator_agents.queries.get_firestore_client", return_value=mock_db):
            from curator_agents.queries import get_category_distribution

            dist = get_category_distribution()
            assert dist == {"CRM": 1}


class TestFormatCategoryDistribution:
    """Tests for format_category_distribution helper."""

    def test_empty_distribution_returns_cold_start_message(self):
        from curator_agents.queries import format_category_distribution

        result = format_category_distribution({})
        assert "fresh start" in result
        assert "HIS" in result
        assert "LOC" in result

    def test_with_data_shows_all_categories(self):
        from curator_agents.queries import format_category_distribution

        dist = {"HIS": 3, "OCC": 2, "FLK": 1}
        result = format_category_distribution(dist)
        # 全8カテゴリが表示される
        for cat in ["HIS", "FLK", "ANT", "OCC", "URB", "CRM", "REL", "LOC"]:
            assert cat in result
        assert "3 article(s)" in result
        assert "0 article(s)" in result

    def test_identifies_underrepresented_categories(self):
        from curator_agents.queries import format_category_distribution

        # 平均 = 8/8 = 1.0 → 0件のカテゴリが underrepresented
        dist = {"HIS": 3, "OCC": 2, "FLK": 1, "ANT": 1, "URB": 1}
        result = format_category_distribution(dist)
        assert "Underrepresented" in result
        # CRM, REL, LOC が0件なので underrepresented
        assert "CRM" in result
        assert "REL" in result
        assert "LOC" in result

    def test_uniform_distribution_no_underrepresented(self):
        from curator_agents.queries import format_category_distribution

        # 全カテゴリ同数 → underrepresented なし
        dist = {cat: 2 for cat in ["HIS", "FLK", "ANT", "OCC", "URB", "CRM", "REL", "LOC"]}
        result = format_category_distribution(dist)
        assert "Underrepresented" not in result


class TestTranslateSuggestionsMerge:
    """translate_suggestions のマージロジックが Translator 出力のキー名を正しく参照するかテスト。"""

    @pytest.mark.asyncio
    async def test_merges_translator_output_with_correct_keys(self):
        """Translator が返す {suggestions: [{theme, description}]} 形式を正しくマージする。"""
        # Curator の出力には category が含まれる（実フロー準拠）
        en_suggestions = [
            {"theme": "Ghost Ships", "description": "Maritime mysteries", "category": "OCC"},
            {"theme": "Voodoo Queen", "description": "New Orleans legends", "category": "FLK"},
        ]
        # Translator エージェントの出力形式: サフィックスなしの素のフィールド名
        translator_output = json.dumps({
            "suggestions": [
                {"theme": "幽霊船", "description": "海の怪異"},
                {"theme": "ヴードゥーの女王", "description": "ニューオーリンズの伝説"},
            ]
        })

        # Runner.run_async をモックし、Translator の出力をシミュレート
        mock_event = MagicMock()
        mock_part = MagicMock()
        mock_part.text = translator_output
        mock_event.content.parts = [mock_part]

        captured_messages = []

        async def mock_run_async(**kwargs):
            # Translator に送信されるメッセージをキャプチャ
            if "new_message" in kwargs:
                captured_messages.append(kwargs["new_message"])
            yield mock_event

        with patch("services.curator.Runner") as MockRunner, \
             patch("services.curator.InMemorySessionService") as MockSessionService:
            mock_runner_instance = MagicMock()
            mock_runner_instance.run_async = mock_run_async
            MockRunner.return_value = mock_runner_instance
            mock_session = AsyncMock()
            MockSessionService.return_value = mock_session

            from services.curator import translate_suggestions
            result = await translate_suggestions(en_suggestions)

        # Translator への入力に category が含まれないことを検証
        assert len(captured_messages) == 1
        sent_text = captured_messages[0].parts[0].text
        sent_json = json.loads(sent_text.split("\n\n", 1)[1])
        for s in sent_json["suggestions"]:
            assert "category" not in s, "Translator 入力に category が混入している"

        assert len(result) == 2
        assert result[0]["theme"] == "Ghost Ships"
        assert result[0]["theme_ja"] == "幽霊船"
        assert result[0]["description_ja"] == "海の怪異"
        assert result[1]["theme_ja"] == "ヴードゥーの女王"
        assert result[1]["description_ja"] == "ニューオーリンズの伝説"

    @pytest.mark.asyncio
    async def test_returns_english_only_when_json_parse_fails(self, caplog):
        """Translator が不正な JSON を返した場合、警告ログを出力し英語のみのリストをそのまま返す。"""
        en_suggestions = [
            {"theme": "Ghost Ships", "description": "Maritime mysteries"},
        ]

        mock_event = MagicMock()
        mock_part = MagicMock()
        mock_part.text = "not valid json"
        mock_event.content.parts = [mock_part]

        async def mock_run_async(**kwargs):
            yield mock_event

        with patch("services.curator.Runner") as MockRunner, \
             patch("services.curator.InMemorySessionService") as MockSessionService:
            mock_runner_instance = MagicMock()
            mock_runner_instance.run_async = mock_run_async
            MockRunner.return_value = mock_runner_instance
            mock_session = AsyncMock()
            MockSessionService.return_value = mock_session

            from services.curator import translate_suggestions
            with caplog.at_level(logging.WARNING, logger="services.curator"):
                result = await translate_suggestions(en_suggestions)

        assert len(result) == 1
        assert result[0]["theme"] == "Ghost Ships"
        assert "theme_ja" not in result[0]
        # 警告ログが出力されていることを検証
        assert any("JSON パース失敗" in record.message for record in caplog.records)
