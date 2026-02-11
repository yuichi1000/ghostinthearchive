"""Unit tests for language selection guard mechanisms.

各 Librarian のツール呼び出し制限や、言語選択のバリデーションを検証する。
"""

import json
from unittest.mock import MagicMock

from mystery_agents.tools.theme_analyzer_tools import (
    ALLOWED_LANGUAGES,
    MAX_LANGUAGES,
    save_language_selection,
)


class TestLanguageSelectionGuard:
    """言語選択のガード機構テスト。"""

    def _make_tool_context(self):
        ctx = MagicMock()
        ctx.state = {}
        return ctx

    def test_all_allowed_languages_accepted(self):
        """許可リスト内の全言語が受け入れられる（上限まで）。"""
        ctx = self._make_tool_context()
        save_language_selection('["en", "de", "es", "fr"]', ctx)

        selected = ctx.state["selected_languages"]
        assert len(selected) == 4
        for lang in selected:
            assert lang in ALLOWED_LANGUAGES

    def test_exceeding_max_languages_truncated(self):
        """MAX_LANGUAGES を超える場合は切り捨て。"""
        ctx = self._make_tool_context()
        save_language_selection('["en", "de", "es", "fr", "nl", "pt"]', ctx)

        assert len(ctx.state["selected_languages"]) == MAX_LANGUAGES

    def test_mixed_valid_invalid_languages(self):
        """有効・無効混在のリストから有効なもののみ抽出。"""
        ctx = self._make_tool_context()
        save_language_selection('["en", "xx", "de", "yy", "fr"]', ctx)

        selected = ctx.state["selected_languages"]
        assert "xx" not in selected
        assert "yy" not in selected
        assert "en" in selected
        assert "de" in selected
        assert "fr" in selected

    def test_only_invalid_languages_fallback_to_en(self):
        """全て無効な言語コードの場合、en のみにフォールバック。"""
        ctx = self._make_tool_context()
        save_language_selection('["xx", "yy", "zz"]', ctx)

        assert ctx.state["selected_languages"] == ["en"]

    def test_order_preserved(self):
        """入力順序が保持される（en が先頭に挿入される場合を除く）。"""
        ctx = self._make_tool_context()
        save_language_selection('["de", "fr", "es"]', ctx)

        selected = ctx.state["selected_languages"]
        # en が先頭に挿入される
        assert selected[0] == "en"
        # 残りの順序は保持
        assert selected[1] == "de"
        assert selected[2] == "fr"
        assert selected[3] == "es"

    def test_result_json_format(self):
        """戻り値の JSON フォーマットが正しい。"""
        ctx = self._make_tool_context()
        result_json = save_language_selection('["en", "de"]', ctx)
        result = json.loads(result_json)

        assert "status" in result
        assert "selected" in result
        assert "total_languages" in result
        assert result["total_languages"] == 2

    def test_concurrent_safe_state_write(self):
        """セッション状態への書き込みが確定的。"""
        ctx = self._make_tool_context()

        # 2回呼び出しても最後の結果が残る
        save_language_selection('["en", "de"]', ctx)
        save_language_selection('["en", "fr", "nl"]', ctx)

        assert ctx.state["selected_languages"] == ["en", "fr", "nl"]
