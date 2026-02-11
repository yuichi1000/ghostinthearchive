"""Tests for pipeline gate callbacks.

パイプラインゲートが前段エージェントの出力を判定し、
有意なデータがない場合に後続をスキップすることを検証する。
"""

from mystery_agents.agents.pipeline_gate import (
    _FAILURE_MARKERS,
    _is_meaningful,
    make_polymath_gate,
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

    def test_no_selected_languages_defaults_to_en(self):
        """selected_languages がない場合 ['en'] をデフォルトにする。"""
        ctx = MockCallbackContext(state={
            "collected_documents_en": "Found documents...",
        })
        gate = make_scholar_gate()
        result = gate(ctx)
        assert result is None


class TestPolymathGate:
    """make_polymath_gate のテスト。"""

    def test_all_scholars_failed_skips(self):
        ctx = MockCallbackContext(state={
            "selected_languages": ["en", "es"],
            "scholar_analysis_en": "INSUFFICIENT_DATA: Not enough material for analysis.",
            "scholar_analysis_es": "INSUFFICIENT_DATA: No sources available.",
        })
        gate = make_polymath_gate()
        result = gate(ctx)
        assert result is not None

    def test_one_scholar_succeeded_proceeds(self):
        ctx = MockCallbackContext(state={
            "selected_languages": ["en", "es"],
            "scholar_analysis_en": "Analysis of Bell Witch phenomenon...",
            "scholar_analysis_es": "INSUFFICIENT_DATA: No sources.",
        })
        gate = make_polymath_gate()
        result = gate(ctx)
        assert result is None


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
