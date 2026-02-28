"""Unit tests for podcast_agents/cli.py — _format_evidence_summary ヘルパー関数。

仕様:
- Evidence 型フィールドを人間可読テキストに整形する
- フルデータ / 部分データ / 空データの3パターンで正しく動作する
"""

from podcast_agents.cli import _format_evidence_summary


class TestFormatEvidenceSummary:
    """_format_evidence_summary() のテスト。"""

    def test_full_data(self):
        """Should format all evidence fields when fully populated."""
        mystery = {
            "evidence_a": {
                "source_title": "Boston Globe Archive",
                "source_date": "1892-03-15",
                "source_type": "newspaper",
                "source_language": "en",
                "relevant_excerpt": "The ship was last seen leaving the harbor at dawn.",
                "source_url": "https://example.com/globe",
                "location_context": "Boston Harbor, Massachusetts",
            },
            "evidence_b": {
                "source_title": "Harbor Master's Log",
                "source_date": "1892-03-15",
                "source_type": "official_record",
                "source_language": "en",
                "relevant_excerpt": "No vessel recorded entering or leaving port on this date.",
                "source_url": "https://example.com/harbor",
                "location_context": "Boston Harbor, Massachusetts",
            },
            "additional_evidence": [
                {
                    "source_title": "Local Folklore Collection",
                    "source_date": "1920",
                    "source_type": "folklore",
                    "source_language": "en",
                    "relevant_excerpt": "Old fishermen spoke of a ghost ship.",
                    "source_url": "https://example.com/folklore",
                    "location_context": "Coastal New England",
                },
            ],
        }
        result = _format_evidence_summary(mystery)

        # Evidence A のフィールドが含まれる
        assert "Boston Globe Archive" in result
        assert "1892-03-15" in result
        assert "The ship was last seen leaving the harbor at dawn." in result

        # Evidence B のフィールドが含まれる
        assert "Harbor Master's Log" in result
        assert "No vessel recorded entering or leaving port on this date." in result

        # Additional evidence が含まれる
        assert "Local Folklore Collection" in result
        assert "Old fishermen spoke of a ghost ship." in result

    def test_partial_data_only_evidence_a(self):
        """Should handle mystery with only evidence_a (no evidence_b or additional)."""
        mystery = {
            "evidence_a": {
                "source_title": "Archive Record",
                "relevant_excerpt": "A single piece of evidence.",
            },
        }
        result = _format_evidence_summary(mystery)

        assert "Archive Record" in result
        assert "A single piece of evidence." in result
        # evidence_b / additional がなくてもエラーにならない
        assert result != ""

    def test_empty_mystery(self):
        """Should return empty string when mystery has no evidence fields."""
        result = _format_evidence_summary({})
        assert result == ""

    def test_empty_evidence_objects(self):
        """Should return empty string when evidence fields are empty dicts."""
        mystery = {
            "evidence_a": {},
            "evidence_b": {},
            "additional_evidence": [],
        }
        result = _format_evidence_summary(mystery)
        assert result == ""

    def test_additional_evidence_multiple_items(self):
        """Should format all items in additional_evidence list."""
        mystery = {
            "additional_evidence": [
                {
                    "source_title": "Source One",
                    "relevant_excerpt": "First excerpt.",
                },
                {
                    "source_title": "Source Two",
                    "relevant_excerpt": "Second excerpt.",
                },
            ],
        }
        result = _format_evidence_summary(mystery)
        assert "Source One" in result
        assert "Source Two" in result
        assert "First excerpt." in result
        assert "Second excerpt." in result
