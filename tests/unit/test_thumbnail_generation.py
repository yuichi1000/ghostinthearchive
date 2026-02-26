"""Unit tests for thumbnail generation."""

from pathlib import Path

from PIL import Image as PILImage

from mystery_agents.tools.image_processing import _generate_thumbnail


class TestGenerateThumbnail:
    """_generate_thumbnail のテスト。"""

    def test_generates_400x400_webp(self, tmp_path):
        """16:9 ソースから 400×400 WebP が生成される。"""
        # 1600×900 の 16:9 テスト画像を作成
        src = tmp_path / "header_test.png"
        img = PILImage.new("RGB", (1600, 900), color="red")
        img.save(str(src))

        result = _generate_thumbnail(str(src))

        assert result is not None
        assert result["width"] == 400
        assert result["height"] == 400
        assert result["filename"] == "header_test_thumb.webp"
        assert Path(result["filepath"]).exists()

        # 生成されたファイルが実際に 400×400 であることを確認
        thumb = PILImage.open(result["filepath"])
        assert thumb.size == (400, 400)
        assert thumb.format == "WEBP"

    def test_center_crop_landscape(self, tmp_path):
        """横長画像の中央クロップが正しい。"""
        # 1600×400 の極端な横長画像
        src = tmp_path / "wide.png"
        img = PILImage.new("RGB", (1600, 400), color="blue")
        img.save(str(src))

        result = _generate_thumbnail(str(src))

        assert result is not None
        thumb = PILImage.open(result["filepath"])
        assert thumb.size == (400, 400)

    def test_center_crop_square(self, tmp_path):
        """正方形画像はクロップなしでリサイズのみ。"""
        src = tmp_path / "square.png"
        img = PILImage.new("RGB", (800, 800), color="green")
        img.save(str(src))

        result = _generate_thumbnail(str(src))

        assert result is not None
        thumb = PILImage.open(result["filepath"])
        assert thumb.size == (400, 400)

    def test_small_source_still_works(self, tmp_path):
        """400px 未満のソースでも動作する（アップスケール）。"""
        src = tmp_path / "small.png"
        img = PILImage.new("RGB", (200, 100), color="yellow")
        img.save(str(src))

        result = _generate_thumbnail(str(src))

        assert result is not None
        thumb = PILImage.open(result["filepath"])
        assert thumb.size == (400, 400)

    def test_nonexistent_source_returns_none(self):
        """存在しないソースで None を返す。"""
        result = _generate_thumbnail("/nonexistent/image.png")
        assert result is None

    def test_output_in_same_directory(self, tmp_path):
        """出力ファイルがソースと同じディレクトリに作成される。"""
        src = tmp_path / "header.png"
        img = PILImage.new("RGB", (1920, 1080), color="white")
        img.save(str(src))

        result = _generate_thumbnail(str(src))

        assert result is not None
        assert Path(result["filepath"]).parent == tmp_path
