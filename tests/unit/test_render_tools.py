"""Unit tests for alchemist_agents/tools/render_tools.py - generate_design_asset."""

import json
from unittest.mock import patch, MagicMock

from alchemist_agents.tools.render_tools import (
    generate_design_asset,
    _remove_background,
    PRODUCT_ASPECT_RATIOS,
    CHROMA_COLORS,
    STYLE_CHROMA_ORDER,
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

    @patch("google.genai.Client")
    def test_replaces_magenta_with_transparency(self, mock_client_cls, tmp_path):
        """マゼンタ背景がアルファ 0 に変換される。"""
        from PIL import Image as PILImage
        import numpy as np
        import io

        # マゼンタ背景 + 赤い前景のテスト画像を作成
        img = PILImage.new("RGB", (10, 10), (255, 0, 255))  # 全面マゼンタ
        # 中央 4px を赤に（前景）
        for x in range(4, 6):
            for y in range(4, 6):
                img.putpixel((x, y), (255, 0, 0))
        filepath = str(tmp_path / "test.png")
        img.save(filepath, "PNG")

        # Edit API が返す画像バイト列（同じ画像 = 背景がマゼンタになった想定）
        buf = io.BytesIO()
        img.save(buf, "PNG")
        edited_bytes = buf.getvalue()

        mock_image = MagicMock()
        mock_image.image_bytes = edited_bytes

        mock_response = MagicMock()
        mock_response.generated_images = [MagicMock(image=mock_image)]

        mock_client = MagicMock()
        mock_client.models.edit_image.return_value = mock_response
        mock_client_cls.return_value = mock_client

        path, success = _remove_background(filepath)

        assert path == filepath
        assert success is True

        # 結果画像を検証
        result_img = PILImage.open(filepath).convert("RGBA")
        data = np.array(result_img)

        # マゼンタ領域（背景）は透明になっている
        assert data[0, 0, 3] == 0  # 左上（元マゼンタ）→ 透明
        # 赤い領域（前景）は不透明のまま
        assert data[4, 4, 3] == 255  # 中央（赤）→ 不透明

    @patch("google.genai.Client")
    def test_returns_original_on_empty_response(self, mock_client_cls, tmp_path):
        """Edit API が全色で空レスポンスを返した場合、元画像を維持する。"""
        from PIL import Image as PILImage

        filepath = str(tmp_path / "test.png")
        PILImage.new("RGB", (4, 4), (100, 100, 100)).save(filepath, "PNG")

        mock_response = MagicMock()
        mock_response.generated_images = []

        mock_client = MagicMock()
        mock_client.models.edit_image.return_value = mock_response
        mock_client_cls.return_value = mock_client

        path, success = _remove_background(filepath)

        assert path == filepath
        assert success is False
        # 空レスポンスでも2色分試行する
        assert mock_client.models.edit_image.call_count == 2

    @patch(_PATCH_GENERATE_IMAGE)
    @patch("alchemist_agents.tools.render_tools._remove_background")
    def test_generate_calls_remove_background_on_success(self, mock_remove_bg, mock_gen):
        """generate_design_asset が成功時に _remove_background を style/region 付きで呼び出す。"""
        mock_gen.return_value = json.dumps({
            "status": "success",
            "filepath": "/tmp/test.png",
        })
        mock_remove_bg.return_value = ("/tmp/test.png", True)

        result_json = generate_design_asset(
            prompt="Test", product_type="tshirt",
        )
        result = json.loads(result_json)

        mock_remove_bg.assert_called_once_with("/tmp/test.png", style="auto", region="EU")
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

        mock_remove_bg.assert_called_once_with("/tmp/test.png", style="auto", region="EU")
        assert result["transparent_background"] is False

    @patch("google.genai.Client")
    def test_returns_false_when_no_transparent_pixels(self, mock_client_cls, tmp_path):
        """全色でクロマキー検出が0ピクセルの場合 False を返す（2色リトライ後に失敗）。"""
        from PIL import Image as PILImage
        import io

        # クロマキー色を含まない画像（全面赤）
        img = PILImage.new("RGB", (10, 10), (255, 0, 0))
        filepath = str(tmp_path / "no_chroma.png")
        img.save(filepath, "PNG")

        # Edit API が返す画像もクロマキー色なし（同じ赤画像）
        buf = io.BytesIO()
        img.save(buf, "PNG")
        edited_bytes = buf.getvalue()

        mock_image = MagicMock()
        mock_image.image_bytes = edited_bytes

        mock_response = MagicMock()
        mock_response.generated_images = [MagicMock(image=mock_image)]

        mock_client = MagicMock()
        mock_client.models.edit_image.return_value = mock_response
        mock_client_cls.return_value = mock_client

        path, success = _remove_background(filepath)

        assert path == filepath
        assert success is False
        # デフォルト(auto)は2色試行するため、edit_image が2回呼ばれる
        assert mock_client.models.edit_image.call_count == 2

    @patch("google.genai.Client")
    def test_folklore_style_uses_green_prompt(self, mock_client_cls, tmp_path):
        """style="folklore" で Imagen API がグリーンバックプロンプトで呼ばれる。"""
        from PIL import Image as PILImage
        import numpy as np
        import io

        # グリーン背景 + 赤い前景のテスト画像を作成
        img = PILImage.new("RGB", (10, 10), (0, 255, 0))  # 全面グリーン
        for x in range(4, 6):
            for y in range(4, 6):
                img.putpixel((x, y), (255, 0, 0))
        filepath = str(tmp_path / "folklore.png")
        img.save(filepath, "PNG")

        buf = io.BytesIO()
        img.save(buf, "PNG")
        edited_bytes = buf.getvalue()

        mock_image = MagicMock()
        mock_image.image_bytes = edited_bytes

        mock_response = MagicMock()
        mock_response.generated_images = [MagicMock(image=mock_image)]

        mock_client = MagicMock()
        mock_client.models.edit_image.return_value = mock_response
        mock_client_cls.return_value = mock_client

        path, success = _remove_background(filepath, style="folklore")

        assert success is True
        # 1回目の呼び出しがグリーンバックプロンプト
        first_call = mock_client.models.edit_image.call_args_list[0]
        assert "green screen" in first_call[1]["prompt"]
        assert "chroma key green" in first_call[1]["prompt"]

    @patch("google.genai.Client")
    def test_retries_with_next_color_on_zero_transparent(self, mock_client_cls, tmp_path):
        """1色目が透過0ピクセルで失敗し、2色目で成功する。"""
        from PIL import Image as PILImage
        import io

        filepath = str(tmp_path / "retry.png")
        PILImage.new("RGB", (10, 10), (128, 128, 128)).save(filepath, "PNG")

        # 1回目: マゼンタなし画像（全面赤 → 透過0ピクセル）
        img_red = PILImage.new("RGB", (10, 10), (255, 0, 0))
        buf1 = io.BytesIO()
        img_red.save(buf1, "PNG")

        # 2回目: グリーン画像（全面グリーン → 透過成功）
        img_green = PILImage.new("RGB", (10, 10), (0, 255, 0))
        buf2 = io.BytesIO()
        img_green.save(buf2, "PNG")

        mock_img1 = MagicMock()
        mock_img1.image_bytes = buf1.getvalue()
        mock_resp1 = MagicMock()
        mock_resp1.generated_images = [MagicMock(image=mock_img1)]

        mock_img2 = MagicMock()
        mock_img2.image_bytes = buf2.getvalue()
        mock_resp2 = MagicMock()
        mock_resp2.generated_images = [MagicMock(image=mock_img2)]

        mock_client = MagicMock()
        # style="auto" → ["magenta", "green"]: 1回目マゼンタ失敗、2回目グリーン成功
        mock_client.models.edit_image.side_effect = [mock_resp1, mock_resp2]
        mock_client_cls.return_value = mock_client

        path, success = _remove_background(filepath, style="auto")

        assert success is True
        assert mock_client.models.edit_image.call_count == 2

    @patch("google.genai.Client")
    def test_returns_false_after_all_retries_exhausted(self, mock_client_cls, tmp_path):
        """全色でリトライしても透過0ピクセルの場合 (filepath, False) を返す。"""
        from PIL import Image as PILImage
        import io

        filepath = str(tmp_path / "exhausted.png")
        PILImage.new("RGB", (10, 10), (128, 128, 128)).save(filepath, "PNG")

        # 全回: 赤画像（どのクロマキー色にもマッチしない）
        img_red = PILImage.new("RGB", (10, 10), (255, 0, 0))
        buf = io.BytesIO()
        img_red.save(buf, "PNG")

        mock_image = MagicMock()
        mock_image.image_bytes = buf.getvalue()
        mock_response = MagicMock()
        mock_response.generated_images = [MagicMock(image=mock_image)]

        mock_client = MagicMock()
        mock_client.models.edit_image.return_value = mock_response
        mock_client_cls.return_value = mock_client

        path, success = _remove_background(filepath, style="folklore")

        assert path == filepath
        assert success is False
        # folklore は ["green", "blue"] の2色
        assert mock_client.models.edit_image.call_count == 2
