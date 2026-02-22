"""Tests for shared/constants.py の整合性検証。"""

from shared.constants import (
    ALLOWED_LANGUAGES,
    MAX_LANGUAGES,
    TRANSLATION_LANGUAGES,
)


class TestLanguageConstants:
    """言語定数の整合性テスト。"""

    def test_translation_languages_excludes_en(self):
        """翻訳対象言語に英語は含まれない（英語はソース言語）。"""
        assert "en" not in TRANSLATION_LANGUAGES


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
