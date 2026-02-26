"""Unit tests for archival image pipeline (schema, session state, publisher extraction)."""

import re


from mystery_agents.schemas.document import ArchiveDocument, SourceLanguage


class TestArchiveDocumentImageFields:
    """ArchiveDocument の画像フィールドのテスト。"""

    def test_create_with_both_image_urls(self):
        """thumbnail_url と image_url の両方を指定してインスタンス生成できる。"""
        doc = ArchiveDocument(
            title="Test Document",
            source_url="https://example.com/doc",
            summary="Test summary",
            language=SourceLanguage.EN,
            location="Boston",
            source_type="loc_digital",
            thumbnail_url="https://example.com/thumb.jpg",
            image_url="https://example.com/full.jpg",
        )
        assert doc.thumbnail_url == "https://example.com/thumb.jpg"
        assert doc.image_url == "https://example.com/full.jpg"

    def test_create_without_image_urls(self):
        """画像URL なしでもインスタンス生成できる（後方互換）。"""
        doc = ArchiveDocument(
            title="Test Document",
            source_url="https://example.com/doc",
            summary="Test summary",
            language=SourceLanguage.EN,
            location="Boston",
            source_type="loc_digital",
        )
        assert doc.thumbnail_url is None
        assert doc.image_url is None

    def test_model_dump_includes_image_fields(self):
        """model_dump() に画像フィールドが含まれる。"""
        doc = ArchiveDocument(
            title="Test",
            source_url="https://example.com",
            summary="Summary",
            language=SourceLanguage.EN,
            location="NY",
            source_type="nypl",
            thumbnail_url="https://example.com/thumb.jpg",
        )
        data = doc.model_dump()
        assert "thumbnail_url" in data
        assert "image_url" in data
        assert data["thumbnail_url"] == "https://example.com/thumb.jpg"
        assert data["image_url"] is None


class TestPublisherImageInsertsExtraction:
    """Publisher の images.inserts 抽出ロジックのテスト。"""

    # Publisher の正規表現を直接テスト
    _PATTERN = re.compile(r'!\[.*?\]\((https?://[^)]+)\)')

    def test_extract_single_image(self):
        """単一の Markdown 画像から URL を抽出できる。"""
        content = "Some text.\n\n![A newspaper scan — Source: LOC](https://www.loc.gov/image.jpg)\n\nMore text."
        urls = self._PATTERN.findall(content)
        assert urls == ["https://www.loc.gov/image.jpg"]

    def test_extract_multiple_images(self):
        """複数の Markdown 画像から URL を抽出できる。"""
        content = (
            "## Section 1\n\nText.\n\n"
            "![Cap A — Source: LOC](https://loc.gov/a.jpg)\n\n"
            "## Section 2\n\nText.\n\n"
            "![Cap B — Source: Europeana](https://europeana.eu/b.png)\n\n"
            "## Section 3\n\nText.\n\n"
            "![Cap C — Source: DPLA](http://dp.la/c.webp)\n\n"
            "## Section 4\n\nConclusion."
        )
        urls = self._PATTERN.findall(content)
        assert len(urls) == 3
        assert urls[0] == "https://loc.gov/a.jpg"
        assert urls[2] == "http://dp.la/c.webp"

    def test_no_images(self):
        """画像なしのコンテンツでは空リストを返す。"""
        content = "## Section 1\n\nJust text, no images."
        urls = self._PATTERN.findall(content)
        assert urls == []

    def test_does_not_match_regular_links(self):
        """通常のリンク [text](url) は抽出しない。"""
        content = "See [the archive](https://example.com) for details."
        urls = self._PATTERN.findall(content)
        assert urls == []

    def test_alt_text_with_special_characters(self):
        """キャプションに特殊文字を含む画像から URL を抽出できる。"""
        content = '![A "haunted" map (1842) — Source: NYPL](https://images.nypl.org/map.jpg)'
        urls = self._PATTERN.findall(content)
        assert urls == ["https://images.nypl.org/map.jpg"]
