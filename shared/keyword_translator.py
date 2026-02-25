"""Google Cloud Translation API v2 を使ったキーワード翻訳ラッパー。

多言語アーカイブ検索時に、元言語のキーワードを他言語に自動翻訳する。
翻訳失敗時はパイプラインをブロックせず空辞書を返す（graceful degradation）。
"""

from __future__ import annotations

import logging
from functools import lru_cache
from typing import Optional

logger = logging.getLogger(__name__)

# モジュールレベルでシングルトン管理
_client: Optional[object] = None
_client_initialized = False


def _get_client():
    """Translation API クライアントをシングルトンで取得する。"""
    global _client, _client_initialized
    if _client_initialized:
        return _client
    _client_initialized = True
    try:
        from google.cloud import translate_v2 as translate

        _client = translate.Client()
    except Exception:
        logger.debug("Translation API クライアント初期化失敗", exc_info=True)
        _client = None
    return _client


@lru_cache(maxsize=512)
def _translate_single(text: str, source_lang: str, target_lang: str) -> Optional[str]:
    """単一テキストを翻訳する（キャッシュ付き）。

    翻訳結果が元テキストと同一（大文字小文字無視）なら None を返す。
    これにより固有名詞（"Boston" → "Boston"）の重複を防ぐ。
    """
    client = _get_client()
    if client is None:
        return None
    try:
        result = client.translate(
            text,
            source_language=source_lang,
            target_language=target_lang,
        )
        translated = result["translatedText"]
        # 固有名詞除外: 翻訳結果が元テキストと同一なら除外
        if translated.lower() == text.lower():
            return None
        return translated
    except Exception:
        logger.debug(
            "翻訳失敗: %s (%s→%s)", text, source_lang, target_lang,
            exc_info=True,
        )
        return None


def translate_keywords(
    keywords: list[str],
    source_lang: str,
    target_langs: list[str],
) -> dict[str, list[str]]:
    """キーワードを複数言語に翻訳する。

    Args:
        keywords: 翻訳対象のキーワードリスト
        source_lang: 元言語の ISO 639-1 コード
        target_langs: 翻訳先言語の ISO 639-1 コードリスト

    Returns:
        {lang: [translated_keywords]} の辞書。
        翻訳先に有効な翻訳がない言語はキーから除外される。
        API エラー時は空辞書を返す。
    """
    if not keywords or not target_langs:
        return {}

    client = _get_client()
    if client is None:
        return {}

    result: dict[str, list[str]] = {}
    for lang in target_langs:
        if lang == source_lang:
            continue
        translated = []
        for kw in keywords:
            t = _translate_single(kw, source_lang, lang)
            if t is not None:
                translated.append(t)
        if translated:
            result[lang] = translated

    return result
