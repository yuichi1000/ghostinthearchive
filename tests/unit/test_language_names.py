"""shared/language_names.py のユニットテスト。"""

from shared.language_names import get_language_name


class TestGetLanguageName:
    """get_language_name() のテスト。"""

    def test_known_english(self):
        """英語コードが正しい名前を返す。"""
        assert get_language_name("en") == "English"

    def test_known_german(self):
        assert get_language_name("de") == "German"

    def test_known_japanese(self):
        assert get_language_name("ja") == "Japanese"

    def test_known_italian(self):
        assert get_language_name("it") == "Italian"

    def test_known_dutch(self):
        assert get_language_name("nl") == "Dutch"

    def test_known_polish(self):
        assert get_language_name("pl") == "Polish"

    def test_unknown_code_returns_uppercase(self):
        """未知コードは大文字にフォールバック。"""
        assert get_language_name("xx") == "XX"

    def test_case_insensitive(self):
        """大文字コードも正しく処理される。"""
        assert get_language_name("EN") == "English"
        assert get_language_name("De") == "German"

    def test_empty_string(self):
        """空文字列はフォールバック。"""
        assert get_language_name("") == ""
