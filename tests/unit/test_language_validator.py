"""Unit tests for shared/language_validator.py."""

from shared.language_validator import (
    ValidationResult,
    _english_stop_word_density,
    _has_japanese_characters,
    validate_translation_language,
)


class TestHasJapaneseCharacters:
    """ひらがな/カタカナ/漢字の Unicode 範囲検出テスト。"""

    def test_detects_hiragana(self):
        assert _has_japanese_characters("これはテストです") is True

    def test_detects_katakana(self):
        assert _has_japanese_characters("カタカナテスト") is True

    def test_detects_kanji(self):
        assert _has_japanese_characters("漢字検出") is True

    def test_rejects_english(self):
        assert _has_japanese_characters("This is an English sentence") is False

    def test_rejects_french(self):
        assert _has_japanese_characters("Ceci est une phrase en français") is False

    def test_empty_string(self):
        assert _has_japanese_characters("") is False


class TestEnglishStopWordDensity:
    """英語ストップワード密度計算テスト。"""

    def test_english_text_high_density(self):
        text = (
            "The mysterious disappearance of the ship was reported in the newspaper. "
            "It is said that the crew had been warned about the storm, but they chose "
            "to sail anyway. The investigation was conducted by the authorities."
        )
        density = _english_stop_word_density(text)
        assert density >= 0.20, f"英語テキストの密度が低すぎる: {density}"

    def test_french_text_low_density(self):
        text = (
            "La disparition mystérieuse du navire a été signalée dans le journal. "
            "On raconte que l'équipage avait été prévenu de la tempête, mais ils ont "
            "choisi de naviguer quand même. L'enquête a été menée par les autorités."
        )
        density = _english_stop_word_density(text)
        assert density < 0.15, f"フランス語テキストの密度が高すぎる: {density}"

    def test_spanish_text_low_density(self):
        text = (
            "La misteriosa desaparición del barco fue reportada en el periódico. "
            "Se dice que la tripulación había sido advertida sobre la tormenta, pero "
            "eligieron navegar de todos modos. La investigación fue realizada."
        )
        density = _english_stop_word_density(text)
        assert density < 0.15, f"スペイン語テキストの密度が高すぎる: {density}"

    def test_german_text_low_density(self):
        text = (
            "Das mysteriöse Verschwinden des Schiffes wurde in der Zeitung gemeldet. "
            "Es heißt, dass die Besatzung vor dem Sturm gewarnt worden war, aber sie "
            "beschlossen trotzdem zu segeln. Die Untersuchung wurde durchgeführt."
        )
        density = _english_stop_word_density(text)
        assert density < 0.15, f"ドイツ語テキストの密度が高すぎる: {density}"

    def test_short_text_returns_zero(self):
        assert _english_stop_word_density("") == 0.0

    def test_no_latin_words_returns_zero(self):
        assert _english_stop_word_density("これは日本語テスト") == 0.0


class TestValidateTranslationLanguage:
    """validate_translation_language の統合テスト。"""

    def test_valid_japanese_translation(self):
        """正常な日本語翻訳を通過させること。"""
        translation = {
            "title": "ボストン港の幽霊船",
            "summary": "1842年に消えた船の謎",
            "narrative_content": (
                "ボストン港に停泊していた貨物船が一夜にして姿を消した。"
                "乗組員は全員行方不明となり、船体は二度と発見されなかった。"
                "地元の漁師たちは霧の夜に幽霊船を目撃したと証言しているが、"
                "当局はその証言を公式記録には残さなかった。この事件は現在も未解決である。"
            ),
        }
        result = validate_translation_language("ja", translation)
        assert result.is_valid is True

    def test_rejects_english_as_japanese(self):
        """英語テキストを日本語翻訳として拒否すること。"""
        translation = {
            "title": "The Ghost Ship of Boston Harbor",
            "summary": "The mystery of a ship that vanished in 1842",
            "narrative_content": (
                "A cargo ship docked at Boston Harbor vanished overnight. "
                "All crew members went missing, and the hull was never found again. "
                "Local fishermen claimed to have witnessed a ghost ship on foggy nights, "
                "but the authorities did not include their testimony in official records."
            ),
        }
        result = validate_translation_language("ja", translation)
        assert result.is_valid is False

    def test_rejects_english_as_french(self):
        """英語テキストをフランス語翻訳として拒否すること。"""
        translation = {
            "title": "The Ghost Ship of Boston Harbor",
            "summary": "The mystery of a ship that vanished in 1842",
            "narrative_content": (
                "A cargo ship docked at Boston Harbor vanished overnight. "
                "All crew members went missing, and the hull was never found again. "
                "Local fishermen claimed to have witnessed a ghost ship on foggy nights, "
                "but the authorities did not include their testimony in official records. "
                "The investigation was conducted by the maritime authorities of the time."
            ),
        }
        result = validate_translation_language("fr", translation)
        assert result.is_valid is False
        assert result.english_density is not None
        assert result.english_density >= 0.15

    def test_valid_french_translation(self):
        """正常なフランス語翻訳を通過させること。"""
        translation = {
            "title": "Le navire fantôme du port de Boston",
            "summary": "Le mystère d'un navire disparu en 1842",
            "narrative_content": (
                "Un cargo amarré au port de Boston a disparu du jour au lendemain. "
                "Tous les membres d'équipage ont disparu et la coque n'a jamais été retrouvée. "
                "Des pêcheurs locaux affirment avoir aperçu un navire fantôme les nuits de brouillard, "
                "mais les autorités n'ont pas inclus leur témoignage dans les registres officiels."
            ),
        }
        result = validate_translation_language("fr", translation)
        assert result.is_valid is True

    def test_short_text_passes_safely(self):
        """短いテキスト（20語未満）は安全側で通すこと。"""
        translation = {
            "title": "Short title",
            "summary": "Brief summary here",
        }
        result = validate_translation_language("fr", translation)
        assert result.is_valid is True

    def test_empty_translation_passes(self):
        """空の翻訳は安全側で通すこと。"""
        result = validate_translation_language("ja", {})
        assert result.is_valid is True

    def test_uses_summary_as_fallback(self):
        """narrative_content がなければ summary にフォールバックすること。"""
        translation = {
            "title": "テスト",
            "summary": (
                "ボストン港に停泊していた貨物船が一夜にして姿を消した。"
                "乗組員は全員行方不明となり、船体は二度と発見されなかった。"
                "地元の漁師たちは霧の夜に幽霊船を目撃したと証言しているが、"
                "当局はその証言を公式記録には残さなかった。"
            ),
        }
        result = validate_translation_language("ja", translation)
        assert result.is_valid is True
