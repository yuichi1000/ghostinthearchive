"""Tests for shared/constants.py の整合性検証。"""

from shared.constants import (
    ALLOWED_LANGUAGES,
    DEFAULT_SELECTED_LANGUAGES,
    MAX_LANGUAGES,
    TRANSLATION_LANGUAGES,
)


class TestLanguageConstants:
    """言語定数の整合性テスト。"""

    def test_translation_languages_excludes_en(self):
        """翻訳対象言語に英語は含まれない（英語はソース言語）。"""
        assert "en" not in TRANSLATION_LANGUAGES

    def test_translation_languages_includes_ja(self):
        """翻訳対象言語に日本語が含まれる。"""
        assert "ja" in TRANSLATION_LANGUAGES

    def test_translation_languages_overlap_with_allowed(self):
        """翻訳対象言語のうち ja 以外は全て ALLOWED_LANGUAGES に含まれる。"""
        non_ja = {lang for lang in TRANSLATION_LANGUAGES if lang != "ja"}
        assert non_ja <= ALLOWED_LANGUAGES

    def test_default_language_in_allowed(self):
        """デフォルト言語は ALLOWED_LANGUAGES に含まれる。"""
        for lang in DEFAULT_SELECTED_LANGUAGES:
            assert lang in ALLOWED_LANGUAGES


class TestReexportConsistency:
    """theme_analyzer_tools 経由の再エクスポートが shared.constants と一致するか。"""

    def test_allowed_languages_matches(self):
        from mystery_agents.tools.theme_analyzer_tools import (
            ALLOWED_LANGUAGES as TAT_ALLOWED,
        )
        from mystery_agents.tools.theme_analyzer_tools import (
            MAX_LANGUAGES as TAT_MAX,
        )

        assert TAT_ALLOWED is ALLOWED_LANGUAGES
        assert TAT_MAX is MAX_LANGUAGES
