"""Unit tests for ThemeAnalyzer tools."""

import json
from unittest.mock import MagicMock

from mystery_agents.tools.theme_analyzer_tools import (
    ALLOWED_LANGUAGES,
    MAX_LANGUAGES,
    save_language_selection,
)
from tests.fakes import make_tool_context


class TestSaveLanguageSelection:
    """Tests for save_language_selection function."""

    def test_valid_selection(self):
        """正常な言語リストがセッション状態に保存される。"""
        ctx = make_tool_context()
        result_json = save_language_selection('["en", "de", "es"]', ctx)
        result = json.loads(result_json)

        assert result["status"] == "success"
        assert result["selected"] == ["en", "de", "es"]
        assert ctx.state["selected_languages"] == ["en", "de", "es"]

    def test_en_always_included(self):
        """英語を含まない選択でも en が自動追加される。"""
        ctx = make_tool_context()
        save_language_selection('["de", "fr"]', ctx)

        assert ctx.state["selected_languages"][0] == "en"
        assert "de" in ctx.state["selected_languages"]
        assert "fr" in ctx.state["selected_languages"]

    def test_max_languages_enforced(self):
        """MAX_LANGUAGES を超える選択はカットされる。"""
        ctx = make_tool_context()
        all_langs = list(ALLOWED_LANGUAGES)
        save_language_selection(json.dumps(all_langs), ctx)

        assert len(ctx.state["selected_languages"]) <= MAX_LANGUAGES

    def test_invalid_language_filtered(self):
        """許可リストにない言語コードは除外される。"""
        ctx = make_tool_context()
        save_language_selection('["en", "zh", "ko", "de"]', ctx)

        selected = ctx.state["selected_languages"]
        assert "zh" not in selected
        assert "ko" not in selected
        assert "en" in selected
        assert "de" in selected

    def test_invalid_json_fallback(self):
        """無効な JSON ではフォールバックして en のみ。"""
        ctx = make_tool_context()
        result_json = save_language_selection("not valid json", ctx)
        result = json.loads(result_json)

        assert result["status"] == "fallback"
        assert ctx.state["selected_languages"] == ["en"]

    def test_non_list_input_fallback(self):
        """配列以外の入力ではフォールバック。"""
        ctx = make_tool_context()
        save_language_selection('"just a string"', ctx)

        assert ctx.state["selected_languages"] == ["en"]

    def test_empty_list_adds_en(self):
        """空リストでも en が追加される。"""
        ctx = make_tool_context()
        save_language_selection('[]', ctx)

        assert ctx.state["selected_languages"] == ["en"]

    def test_duplicate_en_not_added(self):
        """en が既にリストにある場合、重複追加しない。"""
        ctx = make_tool_context()
        save_language_selection('["en", "de"]', ctx)

        assert ctx.state["selected_languages"].count("en") == 1

    def test_non_string_elements_filtered(self):
        """文字列以外の要素は除外される。"""
        ctx = make_tool_context()
        save_language_selection('[123, "de", null, "fr"]', ctx)

        selected = ctx.state["selected_languages"]
        assert all(isinstance(lang, str) for lang in selected)
        assert "en" in selected
        assert "de" in selected
        assert "fr" in selected


    def test_debate_whiteboard_initialized(self):
        """debate_whiteboard が空文字列で初期化される。"""
        ctx = make_tool_context()
        save_language_selection('["en", "de"]', ctx)

        assert ctx.state["debate_whiteboard"] == ""

    def test_structured_report_initialized(self):
        """structured_report が空 dict で初期化される。"""
        ctx = make_tool_context()
        save_language_selection('["en", "de"]', ctx)

        assert ctx.state["structured_report"] == {}

    def test_structured_report_not_initialized_on_fallback(self):
        """フォールバック時には structured_report は初期化されない（早期リターン）。"""
        ctx = make_tool_context()
        save_language_selection("not valid json", ctx)

        assert "structured_report" not in ctx.state

    def test_debate_whiteboard_initialized_on_fallback(self):
        """フォールバック時にも debate_whiteboard が初期化されない（フォールバックは早期リターン）。"""
        ctx = make_tool_context()
        save_language_selection("not valid json", ctx)

        # フォールバック時は debate_whiteboard は設定されない（早期リターン）
        assert "debate_whiteboard" not in ctx.state

    def test_unselected_languages_get_default_state(self):
        """未選択言語の collected_documents_* と scholar_analysis_* にデフォルト値が設定される。"""
        ctx = make_tool_context()
        save_language_selection('["en", "es"]', ctx)

        # 選択された言語にはデフォルト値が設定されない
        assert "collected_documents_en" not in ctx.state
        assert "collected_documents_es" not in ctx.state
        assert "scholar_analysis_en" not in ctx.state
        assert "scholar_analysis_es" not in ctx.state

        # 未選択言語にはデフォルト値が設定される
        for lang in ("de", "fr", "nl", "pt"):
            assert f"collected_documents_{lang}" in ctx.state
            assert f"scholar_analysis_{lang}" in ctx.state
            assert "Not available" in ctx.state[f"collected_documents_{lang}"]
            assert "Not available" in ctx.state[f"scholar_analysis_{lang}"]

    def test_all_languages_selected_no_defaults(self):
        """全言語選択時（MAX_LANGUAGES制限後）、制限外のみデフォルト値が設定される。"""
        ctx = make_tool_context()
        save_language_selection('["en", "de", "es", "fr", "nl", "pt"]', ctx)

        selected = ctx.state["selected_languages"]
        unselected = ALLOWED_LANGUAGES - set(selected)
        for lang in unselected:
            assert f"scholar_analysis_{lang}" in ctx.state

    def test_all_allowed_languages_accepted(self):
        """許可リスト内の全言語が受け入れられる（上限まで）。"""
        ctx = make_tool_context()
        save_language_selection('["en", "de", "es", "fr"]', ctx)

        selected = ctx.state["selected_languages"]
        assert len(selected) == 4
        for lang in selected:
            assert lang in ALLOWED_LANGUAGES

    def test_only_invalid_languages_fallback_to_en(self):
        """全て無効な言語コードの場合、en のみにフォールバック。"""
        ctx = make_tool_context()
        save_language_selection('["xx", "yy", "zz"]', ctx)

        assert ctx.state["selected_languages"] == ["en"]

    def test_order_preserved(self):
        """入力順序が保持される（en が先頭に挿入される場合を除く）。"""
        ctx = make_tool_context()
        save_language_selection('["de", "fr", "es"]', ctx)

        selected = ctx.state["selected_languages"]
        # en が先頭に挿入される
        assert selected[0] == "en"
        # 残りの順序は保持
        assert selected[1] == "de"
        assert selected[2] == "fr"
        assert selected[3] == "es"

    def test_result_json_total_languages(self):
        """戻り値の JSON に total_languages キーが正しく含まれる。"""
        ctx = make_tool_context()
        result_json = save_language_selection('["en", "de"]', ctx)
        result = json.loads(result_json)

        assert "total_languages" in result
        assert result["total_languages"] == 2

    def test_concurrent_safe_state_write(self):
        """セッション状態への書き込みが冪等的（最後の呼び出し結果が残る）。"""
        ctx = make_tool_context()

        # 2回呼び出しても最後の結果が残る
        save_language_selection('["en", "de"]', ctx)
        save_language_selection('["en", "fr", "nl"]', ctx)

        assert ctx.state["selected_languages"] == ["en", "fr", "nl"]


class TestAllowedLanguages:
    """Tests for language configuration constants."""

    def test_allowed_languages_set(self):
        """許可言語セットが正しい。"""
        assert ALLOWED_LANGUAGES == {"en", "de", "es", "fr", "ja", "nl", "pt"}

    def test_max_languages_is_4(self):
        """最大言語数が 4。"""
        assert MAX_LANGUAGES == 4
