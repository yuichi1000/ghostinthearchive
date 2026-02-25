"""Tests for shared/constants.py の整合性検証。"""

from shared.constants import (
    ALLOWED_LANGUAGES,
    DEFAULT_SELECTED_LANGUAGES,
    TRANSLATION_LANGUAGES,
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
