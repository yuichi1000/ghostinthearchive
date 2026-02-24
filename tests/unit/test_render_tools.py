"""Unit tests for alchemist_agents/tools/render_tools.py - generate_design_asset."""

import json
import sys
import types as stdlib_types
from unittest.mock import patch, MagicMock

# rembg がインストールされていない環境でもテストを実行できるよう、
# 未インストール時は mock モジュールを sys.modules に注入する
if "rembg" not in sys.modules:
    _mock_rembg = stdlib_types.ModuleType("rembg")
    _mock_rembg.remove = MagicMock()
    _mock_rembg.new_session = MagicMock()
    sys.modules["rembg"] = _mock_rembg

from alchemist_agents.tools.render_tools import (
    generate_design_asset,
    _remove_background,
    PRODUCT_ASPECT_RATIOS,
)
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
    def test_appends_transparent_background_to_prompt(self, mock_gen):
        """生成プロンプトに背景透過指示が追加される。"""
        mock_gen.return_value = self._mock_generate_success()

        generate_design_asset(
            prompt="Dark mandala pattern",
            product_type="tshirt",
        )

        call_kwargs = mock_gen.call_args[1]
        assert "transparent background" in call_kwargs["prompt"]
        assert "no background" in call_kwargs["prompt"]
        assert call_kwargs["prompt"].startswith("Dark mandala pattern")

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


class TestRemoveBackground:
    """Tests for _remove_background()."""

    def test_returns_original_path_on_error(self):
        """ファイルが存在しない場合、元のパスと False をフォールバックで返す。"""
        path, success = _remove_background("/nonexistent/path.png")
        assert path == "/nonexistent/path.png"
        assert success is False

    def test_skips_rembg_when_already_transparent(self, tmp_path):
        """既に透過ピクセルがある場合、rembg を呼ばずに成功を返す。"""
        from PIL import Image as PILImage
        import numpy as np

        # 透過済み画像（背景=透明、前景=赤）
        img = PILImage.new("RGBA", (10, 10), (0, 0, 0, 0))
        for x in range(4, 6):
            for y in range(4, 6):
                img.putpixel((x, y), (255, 0, 0, 255))
        filepath = str(tmp_path / "already_transparent.png")
        img.save(filepath, "PNG")

        path, success = _remove_background(filepath)

        assert path == filepath
        assert success is True

    @patch("rembg.new_session")
    @patch("rembg.remove")
    def test_rembg_fallback_when_not_transparent(self, mock_remove, mock_new_session, tmp_path):
        """透過ピクセルがない場合、rembg でフォールバック処理する。"""
        from PIL import Image as PILImage
        import numpy as np

        # 不透過画像（赤い前景 + 緑の背景）
        img = PILImage.new("RGBA", (10, 10), (0, 255, 0, 255))
        for x in range(4, 6):
            for y in range(4, 6):
                img.putpixel((x, y), (255, 0, 0, 255))
        filepath = str(tmp_path / "test.png")
        img.save(filepath, "PNG")

        # rembg が返す透過済み画像
        output_img = PILImage.new("RGBA", (10, 10), (0, 0, 0, 0))
        for x in range(4, 6):
            for y in range(4, 6):
                output_img.putpixel((x, y), (255, 0, 0, 255))
        mock_remove.return_value = output_img
        mock_new_session.return_value = MagicMock()

        path, success = _remove_background(filepath)

        assert path == filepath
        assert success is True
        mock_new_session.assert_called_once_with("u2netp")

        # 結果画像を検証
        result_img = PILImage.open(filepath).convert("RGBA")
        data = np.array(result_img)
        assert data[0, 0, 3] == 0       # 背景 → 透明
        assert data[4, 4, 3] == 255     # 前景 → 不透明

    @patch("rembg.new_session")
    @patch("rembg.remove")
    def test_rembg_returns_false_when_no_transparent_pixels(self, mock_remove, mock_new_session, tmp_path):
        """rembg が透過なし画像を返す場合、False を返す。"""
        from PIL import Image as PILImage

        # 不透過画像
        img = PILImage.new("RGBA", (10, 10), (255, 0, 0, 255))
        filepath = str(tmp_path / "test.png")
        img.save(filepath, "PNG")

        # rembg が透過ピクセルなしの画像を返す（背景除去に失敗した想定）
        output_img = PILImage.new("RGBA", (10, 10), (255, 0, 0, 255))
        mock_remove.return_value = output_img
        mock_new_session.return_value = MagicMock()

        path, success = _remove_background(filepath)

        assert path == filepath
        assert success is False

    @patch(_PATCH_GENERATE_IMAGE)
    @patch("alchemist_agents.tools.render_tools._remove_background")
    def test_generate_calls_remove_background_on_success(self, mock_remove_bg, mock_gen):
        """generate_design_asset が成功時に _remove_background を呼び出す。"""
        mock_gen.return_value = json.dumps({
            "status": "success",
            "filepath": "/tmp/test.png",
        })
        mock_remove_bg.return_value = ("/tmp/test.png", True)

        result_json = generate_design_asset(
            prompt="Test", product_type="tshirt",
        )
        result = json.loads(result_json)

        mock_remove_bg.assert_called_once_with("/tmp/test.png")
        assert result["transparent_background"] is True

    @patch(_PATCH_GENERATE_IMAGE)
    @patch("alchemist_agents.tools.render_tools._remove_background")
    def test_generate_skips_remove_background_on_error(self, mock_remove_bg, mock_gen):
        """generate_design_asset がエラー時に _remove_background を呼び出さない。"""
        mock_gen.return_value = json.dumps({
            "status": "error",
            "error": "Generation failed",
        })

        generate_design_asset(prompt="Test", product_type="tshirt")

        mock_remove_bg.assert_not_called()

    @patch(_PATCH_GENERATE_IMAGE)
    @patch("alchemist_agents.tools.render_tools._remove_background")
    def test_transparent_background_false_when_removal_fails(self, mock_remove_bg, mock_gen):
        """背景透過に失敗した場合、transparent_background が False になる。"""
        mock_gen.return_value = json.dumps({
            "status": "success",
            "filepath": "/tmp/test.png",
        })
        mock_remove_bg.return_value = ("/tmp/test.png", False)

        result_json = generate_design_asset(
            prompt="Test", product_type="tshirt",
        )
        result = json.loads(result_json)

        mock_remove_bg.assert_called_once_with("/tmp/test.png")
        assert result["transparent_background"] is False

    def test_returns_false_on_import_error(self):
        """rembg 未インストール時のフェイルオープン。"""
        # rembg モジュールを一時的に無効化して ImportError を発生させる
        with patch.dict(sys.modules, {"rembg": None}):
            path, success = _remove_background("/tmp/test.png")

        assert path == "/tmp/test.png"
        assert success is False
