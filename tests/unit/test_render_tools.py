"""Unit tests for alchemist_agents/tools/render_tools.py - generate_design_asset."""

import json
from unittest.mock import patch

from alchemist_agents.tools.render_tools import generate_design_asset, PRODUCT_ASPECT_RATIOS
from tests.fakes import make_tool_context

# generate_image は関数内で遅延 import されるため、import 元をパッチする
_PATCH_GENERATE_IMAGE = "mystery_agents.tools.illustrator_tools.generate_image"


class TestGenerateDesignAsset:
    """Tests for generate_design_asset()."""

    def _mock_generate_success(self, filepath="/tmp/merch_tshirt_background.png"):
        """generate_image のモック戻り値（成功）。"""
        return json.dumps({
            "status": "success",
            "filepath": filepath,
            "message": "Image generated",
        })

    @patch(_PATCH_GENERATE_IMAGE)
    def test_auto_determines_tshirt_aspect_ratio(self, mock_gen):
        """tshirt の場合 aspect_ratio=1:1 が自動決定される。"""
        mock_gen.return_value = self._mock_generate_success()

        generate_design_asset(
            prompt="Dark mandala pattern",
            product_type="tshirt",
        )

        call_kwargs = mock_gen.call_args[1]
        assert call_kwargs["aspect_ratio"] == "1:1"

    @patch(_PATCH_GENERATE_IMAGE)
    def test_auto_determines_mug_aspect_ratio(self, mock_gen):
        """mug の場合 aspect_ratio=16:9 が自動決定される。"""
        mock_gen.return_value = self._mock_generate_success()

        generate_design_asset(
            prompt="Misty library corridor",
            product_type="mug",
        )

        call_kwargs = mock_gen.call_args[1]
        assert call_kwargs["aspect_ratio"] == "16:9"

    @patch(_PATCH_GENERATE_IMAGE)
    def test_unknown_product_type_defaults_to_1_1(self, mock_gen):
        """未知の product_type はデフォルト 1:1 にフォールバックする。"""
        mock_gen.return_value = self._mock_generate_success()

        generate_design_asset(
            prompt="Test pattern",
            product_type="poster",
        )

        call_kwargs = mock_gen.call_args[1]
        assert call_kwargs["aspect_ratio"] == "1:1"

    @patch(_PATCH_GENERATE_IMAGE)
    def test_accumulates_assets_in_session_state(self, mock_gen):
        """セッション状態に design_assets を累積保存する。"""
        mock_gen.return_value = self._mock_generate_success("/tmp/merch_tshirt_background.png")
        ctx = make_tool_context()

        generate_design_asset(
            prompt="Dark pattern",
            product_type="tshirt",
            asset_layer="background",
            tool_context=ctx,
        )

        assert len(ctx.state["design_assets"]) == 1
        asset = ctx.state["design_assets"][0]
        assert asset["product_type"] == "tshirt"
        assert asset["layer"] == "background"
        assert asset["aspect_ratio"] == "1:1"
        assert asset["status"] == "success"
        assert asset["filepath"] == "/tmp/merch_tshirt_background.png"

    @patch(_PATCH_GENERATE_IMAGE)
    def test_accumulates_multiple_assets(self, mock_gen):
        """複数回呼び出しでアセットが累積する。"""
        mock_gen.return_value = self._mock_generate_success()
        ctx = make_tool_context()

        generate_design_asset(
            prompt="First", product_type="tshirt", asset_layer="background", tool_context=ctx,
        )
        generate_design_asset(
            prompt="Second", product_type="tshirt", asset_layer="decorative", tool_context=ctx,
        )

        assert len(ctx.state["design_assets"]) == 2

    @patch(_PATCH_GENERATE_IMAGE)
    def test_attaches_metadata_to_result(self, mock_gen):
        """結果 JSON に product_type, asset_layer, aspect_ratio を付加する。"""
        mock_gen.return_value = self._mock_generate_success()

        result_json = generate_design_asset(
            prompt="Test",
            product_type="mug",
            asset_layer="decorative",
        )
        result = json.loads(result_json)

        assert result["product_type"] == "mug"
        assert result["asset_layer"] == "decorative"
        assert result["aspect_ratio"] == "16:9"

    @patch(_PATCH_GENERATE_IMAGE)
    def test_passes_negative_prompt(self, mock_gen):
        """negative_prompt を generate_image に渡す。"""
        mock_gen.return_value = self._mock_generate_success()

        generate_design_asset(
            prompt="Test",
            product_type="tshirt",
            negative_prompt="faces, text, watermark",
        )

        call_kwargs = mock_gen.call_args[1]
        assert call_kwargs["negative_prompt"] == "faces, text, watermark"

    @patch(_PATCH_GENERATE_IMAGE)
    def test_default_negative_prompt(self, mock_gen):
        """negative_prompt 未指定時はデフォルト値を使用する。"""
        mock_gen.return_value = self._mock_generate_success()

        generate_design_asset(
            prompt="Test",
            product_type="tshirt",
        )

        call_kwargs = mock_gen.call_args[1]
        assert "people" in call_kwargs["negative_prompt"]
        assert "text" in call_kwargs["negative_prompt"]

    @patch(_PATCH_GENERATE_IMAGE)
    def test_passes_style_and_region(self, mock_gen):
        """style と region を generate_image に渡す。"""
        mock_gen.return_value = self._mock_generate_success()

        generate_design_asset(
            prompt="Test",
            product_type="tshirt",
            style="folklore",
            region="JP",
        )

        call_kwargs = mock_gen.call_args[1]
        assert call_kwargs["style"] == "folklore"
        assert call_kwargs["region"] == "JP"

    @patch(_PATCH_GENERATE_IMAGE)
    def test_constructs_filename_hint(self, mock_gen):
        """filename_hint を product_type + asset_layer から構成する。"""
        mock_gen.return_value = self._mock_generate_success()

        generate_design_asset(
            prompt="Test",
            product_type="mug",
            asset_layer="background",
        )

        call_kwargs = mock_gen.call_args[1]
        assert call_kwargs["filename_hint"] == "merch_mug_background"

    @patch(_PATCH_GENERATE_IMAGE, side_effect=Exception("API error"))
    def test_returns_error_on_generate_failure(self, mock_gen):
        """generate_image が例外を投げた場合にエラーを返す。"""
        result_json = generate_design_asset(
            prompt="Test",
            product_type="tshirt",
        )
        result = json.loads(result_json)

        assert result["status"] == "error"
        assert "API error" in result["error"]
        assert result["product_type"] == "tshirt"

    @patch(_PATCH_GENERATE_IMAGE, side_effect=Exception("API error"))
    def test_does_not_accumulate_on_exception(self, mock_gen):
        """例外時はセッション状態に累積しない。"""
        ctx = make_tool_context()

        generate_design_asset(
            prompt="Test",
            product_type="tshirt",
            tool_context=ctx,
        )

        assert "design_assets" not in ctx.state

    @patch(_PATCH_GENERATE_IMAGE)
    def test_no_accumulation_without_tool_context(self, mock_gen):
        """tool_context が None の場合はセッション状態に書き込まない。"""
        mock_gen.return_value = self._mock_generate_success()

        result_json = generate_design_asset(
            prompt="Test",
            product_type="tshirt",
            tool_context=None,
        )
        result = json.loads(result_json)

        # エラーなく完了する
        assert result["status"] == "success"

    def test_product_aspect_ratios_mapping(self):
        """PRODUCT_ASPECT_RATIOS の定義を検証する。"""
        assert PRODUCT_ASPECT_RATIOS["tshirt"] == "1:1"
        assert PRODUCT_ASPECT_RATIOS["mug"] == "16:9"
