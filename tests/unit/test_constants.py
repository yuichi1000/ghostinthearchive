"""Tests for shared/constants.py の整合性検証。"""

from shared.constants import (
    ALLOWED_LANGUAGES,
    DEFAULT_SELECTED_LANGUAGES,
    FAILURE_MARKERS,
    TRANSLATION_LANGUAGES,
    is_meaningful,
)


class TestLanguageConstants:
    """言語定数の整合性テスト。"""

    def test_translation_languages_excludes_en(self):
        """翻訳対象言語に英語は含まれない（英語はソース言語）。"""
        assert "en" not in TRANSLATION_LANGUAGES

    def test_default_selected_languages_is_all(self):
        """DEFAULT_SELECTED_LANGUAGES は全言語を含む。"""
        assert set(DEFAULT_SELECTED_LANGUAGES) == ALLOWED_LANGUAGES

    def test_default_selected_languages_is_sorted(self):
        """DEFAULT_SELECTED_LANGUAGES はソート済み。"""
        assert DEFAULT_SELECTED_LANGUAGES == sorted(DEFAULT_SELECTED_LANGUAGES)


class TestIsMeaningful:
    """is_meaningful() の仕様テスト。"""

    def test_empty_string_is_not_meaningful(self):
        assert is_meaningful("") is False

    def test_none_is_not_meaningful(self):
        assert is_meaningful(None) is False

    def test_failure_markers_at_start_are_not_meaningful(self):
        """全失敗マーカーが先頭にある場合、無意味と判定する。"""
        for marker in FAILURE_MARKERS:
            assert is_meaningful(f"{marker}: details here") is False

    def test_real_content_is_meaningful(self):
        assert is_meaningful("The Bell Witch haunting of Adams, Tennessee...") is True

    def test_trailing_failure_marker_is_still_meaningful(self):
        """本文末尾に失敗マーカーがあっても、先頭が有意なら有意と判定する。"""
        text = (
            "**Document 1**\n"
            "- **Title**: A history of Block Island\n"
            "\n---\n\n"
            "NO_DOCUMENTS_FOUND: No documents found."
        )
        assert is_meaningful(text) is True

    def test_whitespace_before_failure_marker_is_not_meaningful(self):
        """先頭に空白があっても失敗マーカーで始まれば無意味と判定する。"""
        assert is_meaningful("  NO_DOCUMENTS_FOUND: nothing.") is False
