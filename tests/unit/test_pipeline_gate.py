"""Tests for pipeline gate callbacks.

パイプラインゲートが前段エージェントの出力を判定し、
有意なデータがない場合に後続をスキップすることを検証する。
"""

from mystery_agents.agents.pipeline_gate import (
    _is_meaningful,
    make_post_story_gate,
    make_scholar_gate,
    make_storyteller_gate,
)


class MockCallbackContext:
    """CallbackContext の軽量モック。"""

    def __init__(self, state: dict):
        self.state = state


class TestIsMeaningful:
    """_is_meaningful のテスト。"""

    def test_empty_string_is_not_meaningful(self):
        assert _is_meaningful("") is False

    def test_none_is_not_meaningful(self):
        assert _is_meaningful(None) is False

    def test_no_documents_found_is_not_meaningful(self):
        assert _is_meaningful("NO_DOCUMENTS_FOUND: No English-language documents found.") is False

    def test_insufficient_data_is_not_meaningful(self):
        assert _is_meaningful("INSUFFICIENT_DATA: All sources returned empty.") is False

    def test_no_content_is_not_meaningful(self):
        assert _is_meaningful("NO_CONTENT: No story content available.") is False

    def test_not_available_is_not_meaningful(self):
        assert _is_meaningful("Not available") is False

    def test_real_content_is_meaningful(self):
        assert _is_meaningful("The Bell Witch haunting of Adams, Tennessee...") is True

    def test_trailing_failure_marker_is_still_meaningful(self):
        """ドキュメント本文の末尾に失敗マーカーがあっても有意と判定する。

        Librarian が資料を見つけたが、特定のサブ検索で見つからなかった場合に
        出力末尾に NO_DOCUMENTS_FOUND を付加するケースの再現。
        """
        text = (
            "**Document 1**\n"
            "- **Title**: A history of Block Island\n"
            "- **Source URL**: https://www.loc.gov/item/rc01002999/\n"
            "\n---\n\n"
            "NO_DOCUMENTS_FOUND: No English-language documents found for "
            '"Palatine Light" in newspapers.'
        )
        assert _is_meaningful(text) is True

    def test_whitespace_before_failure_marker_is_not_meaningful(self):
        """先頭に空白があっても失敗マーカーで始まれば無意味と判定する。"""
        assert _is_meaningful("  NO_DOCUMENTS_FOUND: nothing.") is False


class TestScholarGate:
    """make_scholar_gate のテスト。"""

    def test_all_librarians_failed_skips(self):
        """全 Librarian が失敗した場合、Content を返す（スキップ）。"""
        ctx = MockCallbackContext(state={
            "selected_languages": ["en", "de"],
            "collected_documents_en": "NO_DOCUMENTS_FOUND: No English-language documents found.",
            "collected_documents_de": "NO_DOCUMENTS_FOUND: No German-language documents found.",
        })
        gate = make_scholar_gate()
        result = gate(ctx)
        # MagicMock 環境では types.Content() は MagicMock を返す
        # None でなければスキップされたことを意味する
        assert result is not None

    def test_one_librarian_succeeded_proceeds(self):
        """1言語でも有意なデータがあれば None を返す（実行継続）。"""
        ctx = MockCallbackContext(state={
            "selected_languages": ["en", "de"],
            "collected_documents_en": "Found 5 documents about Bell Witch...",
            "collected_documents_de": "NO_DOCUMENTS_FOUND: No German-language documents found.",
        })
        gate = make_scholar_gate()
        result = gate(ctx)
        assert result is None

    def test_docs_with_trailing_marker_proceeds(self):
        """Librarian がドキュメントを見つけたが末尾に NO_DOCUMENTS_FOUND がある場合。"""
        docs_with_trailing_marker = (
            "**Document 1**\n- **Title**: A history of Block Island\n\n---\n\n"
            "NO_DOCUMENTS_FOUND: No documents found for specific sub-query."
        )
        ctx = MockCallbackContext(state={
            "selected_languages": ["en", "de"],
            "collected_documents_en": docs_with_trailing_marker,
            "collected_documents_de": "NO_DOCUMENTS_FOUND: No German-language documents found.",
        })
        gate = make_scholar_gate()
        result = gate(ctx)
        assert result is None

    def test_no_selected_languages_defaults_to_all(self):
        """selected_languages がない場合、全言語をデフォルトにする。"""
        ctx = MockCallbackContext(state={
            "collected_documents_en": "Found documents...",
        })
        gate = make_scholar_gate()
        result = gate(ctx)
        assert result is None


class TestScholarGateFulltext:
    """ScholarGate の全文チェック関連テスト。"""

    def test_no_fulltext_terminates(self, caplog):
        """全文ドキュメントが 0 件で NO_FULLTEXT_AVAILABLE を返す。"""
        ctx = MockCallbackContext(state={
            "selected_languages": ["en"],
            "collected_documents_en": "# Collected Documents (English) — 3 documents...",
            "fulltext_metrics": {
                "total_documents": 3,
                "fulltext_documents": 0,
                "metadata_only_documents": 3,
                "by_language": {"en": {"total": 3, "fulltext": 0, "metadata_only": 3}},
            },
        })
        gate = make_scholar_gate()
        result = gate(ctx)
        assert result is not None
        assert "NO_FULLTEXT_AVAILABLE" in caplog.text

    def test_some_fulltext_passes(self):
        """全文ドキュメントが 1 件以上あれば通過する。"""
        ctx = MockCallbackContext(state={
            "selected_languages": ["en"],
            "collected_documents_en": "# Collected Documents (English) — 5 documents...",
            "fulltext_metrics": {
                "total_documents": 5,
                "fulltext_documents": 2,
                "metadata_only_documents": 3,
                "by_language": {"en": {"total": 5, "fulltext": 2, "metadata_only": 3}},
            },
        })
        gate = make_scholar_gate()
        result = gate(ctx)
        assert result is None

    def test_missing_metrics_passes(self):
        """fulltext_metrics が未設定でも通過する（後方互換）。"""
        ctx = MockCallbackContext(state={
            "selected_languages": ["en"],
            "collected_documents_en": "Found 5 documents about Bell Witch...",
        })
        gate = make_scholar_gate()
        result = gate(ctx)
        assert result is None

    def test_no_documents_takes_precedence(self, caplog):
        """ドキュメントなし + 全文なしの場合、INSUFFICIENT_DATA が先に発動する。"""
        ctx = MockCallbackContext(state={
            "selected_languages": ["en"],
            "collected_documents_en": "NO_DOCUMENTS_FOUND: No English-language documents.",
            "fulltext_metrics": {
                "total_documents": 0,
                "fulltext_documents": 0,
                "metadata_only_documents": 0,
                "by_language": {},
            },
        })
        gate = make_scholar_gate()
        result = gate(ctx)
        assert result is not None
        assert "INSUFFICIENT_DATA" in caplog.text
        assert "NO_FULLTEXT_AVAILABLE" not in caplog.text


class TestStorytellerGate:
    """make_storyteller_gate のテスト。"""

    def test_no_report_skips(self):
        ctx = MockCallbackContext(state={
            "mystery_report": "INSUFFICIENT_DATA: No mystery report available.",
        })
        gate = make_storyteller_gate()
        result = gate(ctx)
        assert result is not None

    def test_has_report_proceeds(self):
        ctx = MockCallbackContext(state={
            "mystery_report": "The Bell Witch mystery report...",
        })
        gate = make_storyteller_gate()
        result = gate(ctx)
        assert result is None

    def test_empty_report_skips(self):
        ctx = MockCallbackContext(state={
            "mystery_report": "",
        })
        gate = make_storyteller_gate()
        result = gate(ctx)
        assert result is not None


class TestPostStoryGate:
    """make_post_story_gate のテスト。"""

    def test_no_content_skips(self):
        ctx = MockCallbackContext(state={
            "creative_content": "NO_CONTENT: No story content available.",
        })
        gate = make_post_story_gate()
        result = gate(ctx)
        assert result is not None

    def test_has_content_proceeds(self):
        ctx = MockCallbackContext(state={
            "creative_content": "# The Bell Witch of Adams, Tennessee\n\nIn the autumn of 1817...",
        })
        gate = make_post_story_gate()
        result = gate(ctx)
        assert result is None

    def test_missing_key_skips(self):
        ctx = MockCallbackContext(state={})
        gate = make_post_story_gate()
        result = gate(ctx)
        assert result is not None
