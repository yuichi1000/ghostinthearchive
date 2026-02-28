"""AggregatorAgent のユニットテスト。

raw_search_results からの言語別集約ロジックを検証する。
"""


from mystery_agents.agents.aggregator import _format_documents, create_aggregator


class TestFormatDocuments:
    """_format_documents のテスト。"""

    def test_empty_docs_returns_no_documents_found(self):
        """空のドキュメントリストで NO_DOCUMENTS_FOUND を返す。"""
        result = _format_documents("en", [])
        assert "NO_DOCUMENTS_FOUND" in result

    def test_formats_single_document(self):
        """単一ドキュメントが正しくフォーマットされる。"""
        docs = [
            {
                "title": "Test Document",
                "date": "1842-03-15",
                "source_url": "https://example.com/doc1",
                "summary": "A test summary",
                "language": "en",
                "location": "Boston, MA",
                "source_type": "nypl",
                "keywords_matched": ["ghost", "mystery"],
            }
        ]
        result = _format_documents("en", docs)
        assert "Test Document" in result
        assert "1842-03-15" in result
        assert "nypl" in result
        assert "Boston, MA" in result
        assert "ghost, mystery" in result
        assert "1 documents" in result

    def test_deduplicates_by_url(self):
        """同一 URL のドキュメントが重複除去される。"""
        docs = [
            {
                "title": "Doc A",
                "source_url": "https://example.com/same",
                "summary": "First",
                "language": "en",
                "source_type": "nypl",
            },
            {
                "title": "Doc B",
                "source_url": "https://example.com/same",
                "summary": "Duplicate",
                "language": "en",
                "source_type": "nypl",
            },
        ]
        result = _format_documents("en", docs)
        assert "Doc A" in result
        assert "Doc B" not in result
        assert "1 documents" in result

    def test_truncates_long_excerpt(self):
        """raw_text が長い場合 3000 文字 + ... に切り詰める。"""
        long_text = "x" * 5000
        docs = [
            {
                "title": "Long Doc",
                "source_url": "https://example.com/long",
                "summary": "Has long text",
                "language": "en",
                "source_type": "internet_archive",
                "raw_text": long_text,
            }
        ]
        result = _format_documents("en", docs)
        assert "..." in result
        assert "x" * 3000 in result

    def test_language_name_in_header(self):
        """ヘッダーに言語名が含まれる。"""
        docs = [
            {
                "title": "Dokument",
                "source_url": "https://example.com/de",
                "summary": "Ein Test",
                "language": "de",
                "source_type": "europeana",
            }
        ]
        result = _format_documents("de", docs)
        assert "German" in result

    def test_japanese_language_name(self):
        """日本語ドキュメントのヘッダーに Japanese が含まれる。"""
        docs = [
            {
                "title": "テスト文書",
                "source_url": "https://example.com/ja",
                "summary": "テスト",
                "language": "ja",
                "source_type": "ndl",
            }
        ]
        result = _format_documents("ja", docs)
        assert "Japanese" in result

    def test_unknown_language_name_in_header(self):
        """未知の言語コードでもヘッダーに言語名が表示される。"""
        docs = [
            {
                "title": "Dokument po polsku",
                "source_url": "https://example.com/pl",
                "summary": "Polski tekst",
                "language": "pl",
                "source_type": "europeana",
            }
        ]
        result = _format_documents("pl", docs)
        assert "Polish" in result

    def test_italian_language_name(self):
        """イタリア語ドキュメントのヘッダーに Italian が含まれる。"""
        docs = [
            {
                "title": "Documento",
                "source_url": "https://example.com/it",
                "summary": "Un test",
                "language": "it",
                "source_type": "europeana",
            }
        ]
        result = _format_documents("it", docs)
        assert "Italian" in result


class TestCreateAggregator:
    """create_aggregator ファクトリのテスト。"""

    def test_creates_base_agent(self):
        """AggregatorAgent が BaseAgent インスタンスとして生成される。"""
        from google.adk.agents import BaseAgent

        agg = create_aggregator()
        assert isinstance(agg, BaseAgent)

    def test_agent_name(self):
        """エージェント名が 'aggregator' である。"""
        agg = create_aggregator()
        assert "aggregator" in repr(agg)
