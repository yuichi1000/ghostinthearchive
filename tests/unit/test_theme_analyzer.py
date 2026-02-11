"""Unit tests for ThemeAnalyzer tools."""

import json
from unittest.mock import MagicMock

from mystery_agents.tools.theme_analyzer_tools import (
    ALLOWED_LANGUAGES,
    MAX_LANGUAGES,
    save_language_selection,
)


class TestSaveLanguageSelection:
    """Tests for save_language_selection function."""

    def _make_tool_context(self):
        """ToolContext モックを作成する。"""
        ctx = MagicMock()
        ctx.state = {}
        return ctx

    def test_valid_selection(self):
        """正常な言語リストがセッション状態に保存される。"""
        ctx = self._make_tool_context()
        result_json = save_language_selection('["en", "de", "es"]', ctx)
        result = json.loads(result_json)

        assert result["status"] == "success"
        assert result["selected"] == ["en", "de", "es"]
        assert ctx.state["selected_languages"] == ["en", "de", "es"]

    def test_en_always_included(self):
        """英語を含まない選択でも en が自動追加される。"""
        ctx = self._make_tool_context()
        save_language_selection('["de", "fr"]', ctx)

        assert ctx.state["selected_languages"][0] == "en"
        assert "de" in ctx.state["selected_languages"]
        assert "fr" in ctx.state["selected_languages"]

    def test_max_languages_enforced(self):
        """MAX_LANGUAGES を超える選択はカットされる。"""
        ctx = self._make_tool_context()
        all_langs = list(ALLOWED_LANGUAGES)
        save_language_selection(json.dumps(all_langs), ctx)

        assert len(ctx.state["selected_languages"]) <= MAX_LANGUAGES

    def test_invalid_language_filtered(self):
        """許可リストにない言語コードは除外される。"""
        ctx = self._make_tool_context()
        save_language_selection('["en", "ja", "zh", "de"]', ctx)

        selected = ctx.state["selected_languages"]
        assert "ja" not in selected
        assert "zh" not in selected
        assert "en" in selected
        assert "de" in selected

    def test_invalid_json_fallback(self):
        """無効な JSON ではフォールバックして en のみ。"""
        ctx = self._make_tool_context()
        result_json = save_language_selection("not valid json", ctx)
        result = json.loads(result_json)

        assert result["status"] == "fallback"
        assert ctx.state["selected_languages"] == ["en"]

    def test_non_list_input_fallback(self):
        """配列以外の入力ではフォールバック。"""
        ctx = self._make_tool_context()
        save_language_selection('"just a string"', ctx)

        assert ctx.state["selected_languages"] == ["en"]

    def test_empty_list_adds_en(self):
        """空リストでも en が追加される。"""
        ctx = self._make_tool_context()
        save_language_selection('[]', ctx)

        assert ctx.state["selected_languages"] == ["en"]

    def test_duplicate_en_not_added(self):
        """en が既にリストにある場合、重複追加しない。"""
        ctx = self._make_tool_context()
        save_language_selection('["en", "de"]', ctx)

        assert ctx.state["selected_languages"].count("en") == 1

    def test_non_string_elements_filtered(self):
        """文字列以外の要素は除外される。"""
        ctx = self._make_tool_context()
        save_language_selection('[123, "de", null, "fr"]', ctx)

        selected = ctx.state["selected_languages"]
        assert all(isinstance(lang, str) for lang in selected)
        assert "en" in selected
        assert "de" in selected
        assert "fr" in selected


class TestAllowedLanguages:
    """Tests for language configuration constants."""

    def test_allowed_languages_set(self):
        """許可言語セットが正しい。"""
        assert ALLOWED_LANGUAGES == {"en", "de", "es", "fr", "nl", "pt"}

    def test_max_languages_is_4(self):
        """最大言語数が 4。"""
        assert MAX_LANGUAGES == 4
