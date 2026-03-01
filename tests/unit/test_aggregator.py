"""AggregatorAgent のユニットテスト。

raw_search_results からの言語別集約ロジックを検証する。
"""


from mystery_agents.agents.aggregator import (
    _compute_fulltext_metrics,
    _format_documents,
    create_aggregator,
)


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
        """raw_text が長い場合 5000 文字 + ... に切り詰める。"""
        long_text = "x" * 6000
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
        assert "x" * 5000 in result

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


class TestFulltextMetrics:
    """全文テキスト取得メトリクス関連のテスト。"""

    def test_header_includes_fulltext_metrics(self):
        """ヘッダーに全文/メタデータ専用の内訳が含まれる。"""
        docs = [
            {
                "title": "Doc with text",
                "source_url": "https://example.com/1",
                "language": "en",
                "source_type": "loc",
                "raw_text": "Full text content here",
            },
            {
                "title": "Doc without text",
                "source_url": "https://example.com/2",
                "language": "en",
                "source_type": "loc",
            },
        ]
        result = _format_documents(
            "en", docs, lang_fulltext=1, lang_metadata_only=1, global_fulltext=5,
        )
        assert "(1 with full text, 1 metadata-only)" in result

    def test_metadata_only_label(self):
        """raw_text なしドキュメントにメタデータ専用ラベルが付く。"""
        docs = [
            {
                "title": "Metadata Only Doc",
                "source_url": "https://example.com/meta",
                "language": "en",
                "source_type": "loc",
            },
        ]
        result = _format_documents("en", docs)
        assert "[metadata only — full text not available]" in result

    def test_limited_evidence_note(self):
        """全言語合計の全文ドキュメントが 1-2 件の場合、限定的証拠の注記が出る。"""
        docs = [
            {
                "title": "Sole Doc",
                "source_url": "https://example.com/sole",
                "language": "en",
                "source_type": "loc",
                "raw_text": "Some text",
            },
        ]
        result = _format_documents(
            "en", docs, lang_fulltext=1, lang_metadata_only=0, global_fulltext=1,
        )
        assert "Only 1 document(s) with full text available" in result

    def test_no_limited_note_when_enough_fulltext(self):
        """全文ドキュメントが 3+ 件の場合、限定的証拠の注記は出ない。"""
        docs = [
            {
                "title": "Doc",
                "source_url": "https://example.com/doc",
                "language": "en",
                "source_type": "loc",
                "raw_text": "Text",
            },
        ]
        result = _format_documents(
            "en", docs, lang_fulltext=1, lang_metadata_only=0, global_fulltext=5,
        )
        assert "Only" not in result
        assert "limited" not in result.lower()


class TestComputeFulltextMetrics:
    """_compute_fulltext_metrics のテスト。"""

    def test_mixed_docs(self):
        """全文あり/なしが混在するケースでメトリクスが正しく算出される。"""
        docs_by_lang = {
            "en": [
                {"source_url": "https://a.com/1", "raw_text": "text"},
                {"source_url": "https://a.com/2"},
                {"source_url": "https://a.com/3", "raw_text": "more text"},
            ],
            "de": [
                {"source_url": "https://b.com/1"},
                {"source_url": "https://b.com/2"},
            ],
        }
        metrics = _compute_fulltext_metrics(docs_by_lang, ["en", "de"])
        assert metrics["total_documents"] == 5
        assert metrics["fulltext_documents"] == 2
        assert metrics["metadata_only_documents"] == 3
        assert metrics["by_language"]["en"]["fulltext"] == 2
        assert metrics["by_language"]["de"]["metadata_only"] == 2


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
