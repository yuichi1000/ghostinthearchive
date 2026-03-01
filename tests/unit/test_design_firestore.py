"""Unit tests for alchemist_agents/tools/firestore_tools.py - Design Firestore ツール."""

from unittest.mock import MagicMock, patch

import pytest

from alchemist_agents.tools.firestore_tools import (
    load_mystery,
    create_design,
    get_design,
    save_design_result,
    save_render_result,
    set_design_status,
)


@pytest.fixture
def mock_db():
    """Mock Firestore client."""
    with patch("alchemist_agents.tools.firestore_tools.get_firestore_client") as mock:
        client = MagicMock()
        mock.return_value = client
        yield client


class TestLoadMystery:
    """Tests for load_mystery()."""

    def test_returns_mystery_data(self, mock_db):
        """存在するドキュメントのデータを返す。"""
        mock_doc = MagicMock()
        mock_doc.exists = True
        mock_doc.to_dict.return_value = {"title": "Test Mystery", "narrative_content": "..."}
        mock_db.collection.return_value.document.return_value.get.return_value = mock_doc

        result = load_mystery("OCC-MA-617-20260207143025")

        assert result["title"] == "Test Mystery"
        mock_db.collection.assert_called_with("mysteries")

    def test_returns_none_for_missing(self, mock_db):
        """存在しないドキュメントは None を返す。"""
        mock_doc = MagicMock()
        mock_doc.exists = False
        mock_db.collection.return_value.document.return_value.get.return_value = mock_doc

        result = load_mystery("NONEXISTENT")
        assert result is None


class TestCreateDesign:
    """Tests for create_design()."""

    def test_creates_document_with_correct_fields(self, mock_db):
        """正しいフィールドでドキュメントを作成する。"""
        # load_mystery のモック
        mock_mystery_doc = MagicMock()
        mock_mystery_doc.exists = True
        mock_mystery_doc.to_dict.return_value = {"title": "The Vanishing Ship"}

        mock_doc_ref = MagicMock()
        mock_doc_ref.id = "generated-design-id"
        mock_db.collection.return_value.document.return_value.get.return_value = mock_mystery_doc
        mock_db.collection.return_value.add.return_value = (None, mock_doc_ref)

        result = create_design("OCC-MA-617-20260207143025", "ダークカラーで")

        assert result == "generated-design-id"

        # add() に渡されたデータを検証
        call_args = mock_db.collection.return_value.add.call_args[0][0]
        assert call_args["mystery_id"] == "OCC-MA-617-20260207143025"
        assert call_args["mystery_title"] == "The Vanishing Ship"
        assert call_args["status"] == "designing"
        assert call_args["custom_instructions"] == "ダークカラーで"
        assert call_args["proposal"] is None
        assert call_args["assets"] is None
        assert call_args["pipeline_run_id"] is None

    def test_creates_document_with_pipeline_run_id(self, mock_db):
        """pipeline_run_id を指定した場合、即座に紐付けされる。"""
        mock_mystery_doc = MagicMock()
        mock_mystery_doc.exists = True
        mock_mystery_doc.to_dict.return_value = {"title": "The Vanishing Ship"}

        mock_doc_ref = MagicMock()
        mock_doc_ref.id = "generated-design-id"
        mock_db.collection.return_value.document.return_value.get.return_value = mock_mystery_doc
        mock_db.collection.return_value.add.return_value = (None, mock_doc_ref)

        result = create_design(
            "OCC-MA-617-20260207143025", pipeline_run_id="run-123"
        )

        assert result == "generated-design-id"
        call_args = mock_db.collection.return_value.add.call_args[0][0]
        assert call_args["pipeline_run_id"] == "run-123"

    def test_uses_mystery_id_as_title_when_mystery_not_found(self, mock_db):
        """mystery が見つからない場合は ID をタイトルとして使用する。"""
        mock_mystery_doc = MagicMock()
        mock_mystery_doc.exists = False

        mock_doc_ref = MagicMock()
        mock_doc_ref.id = "design-id"
        mock_db.collection.return_value.document.return_value.get.return_value = mock_mystery_doc
        mock_db.collection.return_value.add.return_value = (None, mock_doc_ref)

        result = create_design("MISSING-ID")
        assert result == "design-id"

        call_args = mock_db.collection.return_value.add.call_args[0][0]
        assert call_args["mystery_title"] == "MISSING-ID"

    def test_extracts_region_from_mystery_id(self, mock_db):
        """mystery_id から国コードを抽出する。"""
        mock_mystery_doc = MagicMock()
        mock_mystery_doc.exists = True
        mock_mystery_doc.to_dict.return_value = {"title": "Test"}

        mock_doc_ref = MagicMock()
        mock_doc_ref.id = "design-id"
        mock_db.collection.return_value.document.return_value.get.return_value = mock_mystery_doc
        mock_db.collection.return_value.add.return_value = (None, mock_doc_ref)

        create_design("OCC-US-BOS-20260207143025")

        call_args = mock_db.collection.return_value.add.call_args[0][0]
        assert call_args["region"] == "US"


class TestGetDesign:
    """Tests for get_design()."""

    def test_returns_design_with_id(self, mock_db):
        """ドキュメントデータに design_id を付与して返す。"""
        mock_doc = MagicMock()
        mock_doc.exists = True
        mock_doc.id = "design-123"
        mock_doc.to_dict.return_value = {
            "mystery_id": "OCC-MA-617-20260207143025",
            "status": "design_ready",
        }
        mock_db.collection.return_value.document.return_value.get.return_value = mock_doc

        result = get_design("design-123")

        assert result["design_id"] == "design-123"
        assert result["status"] == "design_ready"
        mock_db.collection.assert_called_with("product_designs")

    def test_returns_none_for_missing(self, mock_db):
        """存在しない場合は None を返す。"""
        mock_doc = MagicMock()
        mock_doc.exists = False
        mock_db.collection.return_value.document.return_value.get.return_value = mock_doc

        result = get_design("nonexistent")
        assert result is None


class TestSaveDesignResult:
    """Tests for save_design_result()."""

    def test_updates_document_with_proposal(self, mock_db):
        """デザイン提案とステータスを更新する。"""
        proposal = {
            "products": [
                {"product_type": "tshirt", "catchphrase_en": "Test"},
            ],
        }

        save_design_result("design-123", proposal)

        mock_db.collection.assert_called_with("product_designs")
        update_call = mock_db.collection.return_value.document.return_value.update
        update_call.assert_called_once()

        update_data = update_call.call_args[0][0]
        assert update_data["proposal"] == proposal
        assert update_data["status"] == "design_ready"
        assert update_data["error_message"] is None


class TestSaveRenderResult:
    """Tests for save_render_result()."""

    def test_updates_document_with_assets(self, mock_db):
        """アセットメタデータとステータスを更新する。"""
        assets = [
            {
                "product_type": "tshirt",
                "layer": "background",
                "gcs_path": "gs://bucket/designs/m1/d1/bg.png",
                "public_url": "https://example.com/bg.png",
                "aspect_ratio": "1:1",
            },
        ]

        save_render_result("design-123", assets)

        update_data = mock_db.collection.return_value.document.return_value.update.call_args[0][0]
        assert update_data["assets"] == assets
        assert update_data["status"] == "render_ready"
        assert update_data["error_message"] is None


class TestSetDesignStatus:
    """Tests for set_design_status()."""

    def test_updates_status(self, mock_db):
        """ステータスを更新する。"""
        set_design_status("design-123", "rendering")

        update_data = mock_db.collection.return_value.document.return_value.update.call_args[0][0]
        assert update_data["status"] == "rendering"

    def test_includes_error_message(self, mock_db):
        """エラーメッセージを含めて更新する。"""
        set_design_status("design-123", "error", "Imagen generation failed")

        update_data = mock_db.collection.return_value.document.return_value.update.call_args[0][0]
        assert update_data["status"] == "error"
        assert update_data["error_message"] == "Imagen generation failed"

    def test_truncates_long_error_message(self, mock_db):
        """長いエラーメッセージを500文字に切り詰める。"""
        long_error = "E" * 1000
        set_design_status("design-123", "error", long_error)

        update_data = mock_db.collection.return_value.document.return_value.update.call_args[0][0]
        assert len(update_data["error_message"]) == 500
