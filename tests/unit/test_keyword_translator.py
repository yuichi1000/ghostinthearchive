"""Tests for shared/keyword_translator.py。

Translation API ラッパーの翻訳成功/失敗/キャッシュ/固有名詞除外を検証。
"""

from unittest.mock import MagicMock, patch

import pytest

import shared.keyword_translator as kt


@pytest.fixture(autouse=True)
def reset_client():
    """各テスト前にクライアントとキャッシュをリセット。"""
    kt._client = None
    kt._client_initialized = False
    kt._translate_single.cache_clear()
    yield
    kt._client = None
    kt._client_initialized = False
    kt._translate_single.cache_clear()


class TestTranslateKeywords:
    """translate_keywords のテスト。"""

    @patch("shared.keyword_translator._get_client")
    def test_successful_translation(self, mock_get_client):
        """正常に翻訳される場合。"""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.translate.side_effect = lambda text, **kw: {
            "translatedText": {"ghost": "Geist", "haunting": "Spuk"}.get(text, text)
        }

        result = kt.translate_keywords(["ghost", "haunting"], "en", ["de"])

        assert "de" in result
        assert "Geist" in result["de"]
        assert "Spuk" in result["de"]

    @patch("shared.keyword_translator._get_client")
    def test_proper_noun_excluded(self, mock_get_client):
        """固有名詞（翻訳結果が元テキストと同一）は除外される。"""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        # "Boston" → "Boston"（固有名詞なので翻訳結果が同一）
        mock_client.translate.return_value = {"translatedText": "Boston"}

        result = kt.translate_keywords(["Boston"], "en", ["de"])

        # "Boston" は除外されるので de キーが含まれない
        assert "de" not in result

    @patch("shared.keyword_translator._get_client")
    def test_case_insensitive_exclusion(self, mock_get_client):
        """大文字小文字を無視して固有名詞を除外する。"""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.translate.return_value = {"translatedText": "boston"}

        result = kt.translate_keywords(["Boston"], "en", ["fr"])
        assert "fr" not in result

    @patch("shared.keyword_translator._get_client")
    def test_api_error_returns_empty(self, mock_get_client):
        """API エラー時は空辞書を返す。"""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.translate.side_effect = Exception("API error")

        result = kt.translate_keywords(["ghost"], "en", ["de"])
        assert result == {}

    def test_no_client_returns_empty(self):
        """クライアント初期化失敗時は空辞書を返す。"""
        kt._client = None
        kt._client_initialized = True  # 初期化済みだが None

        result = kt.translate_keywords(["ghost"], "en", ["de"])
        assert result == {}

    def test_empty_keywords_returns_empty(self):
        """空のキーワードリストでは空辞書を返す。"""
        result = kt.translate_keywords([], "en", ["de"])
        assert result == {}

    def test_empty_target_langs_returns_empty(self):
        """空のターゲット言語リストでは空辞書を返す。"""
        result = kt.translate_keywords(["ghost"], "en", [])
        assert result == {}

    @patch("shared.keyword_translator._get_client")
    def test_same_source_and_target_excluded(self, mock_get_client):
        """ソース言語とターゲット言語が同一の場合はスキップされる。"""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        result = kt.translate_keywords(["ghost"], "en", ["en"])
        assert result == {}
        mock_client.translate.assert_not_called()

    @patch("shared.keyword_translator._get_client")
    def test_multiple_target_languages(self, mock_get_client):
        """複数のターゲット言語に翻訳される。"""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.translate.side_effect = lambda text, source_language, target_language: {
            "translatedText": f"{text}_{target_language}"
        }

        result = kt.translate_keywords(["ghost"], "en", ["de", "fr", "es"])
        assert len(result) == 3
        assert "de" in result
        assert "fr" in result
        assert "es" in result

    @patch("shared.keyword_translator._get_client")
    def test_cache_prevents_duplicate_calls(self, mock_get_client):
        """LRU キャッシュにより同一キーワードの再翻訳が防止される。"""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.translate.return_value = {"translatedText": "Geist"}

        # 同じキーワードで2回呼び出し
        kt.translate_keywords(["ghost"], "en", ["de"])
        kt.translate_keywords(["ghost"], "en", ["de"])

        # translate は1回しか呼ばれない（キャッシュヒット）
        assert mock_client.translate.call_count == 1
