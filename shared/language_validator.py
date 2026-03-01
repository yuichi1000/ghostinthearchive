"""翻訳言語バリデーションモジュール。

Translator が出力した翻訳結果が正しい言語で書かれているかを検証する。
外部ライブラリ不要（Unicode 範囲 + 英語ストップワード密度で判定）。

検出戦略:
- 日本語（ja）: ひらがな/カタカナ/CJK 漢字の Unicode 範囲で判定 — 極めて高精度
- ラテン文字言語（es/de/fr/nl/pt）: 英語ストップワード密度で判定
  英語テキスト（密度 0.20〜0.30）vs 非英語（密度 0.02〜0.08）、閾値 0.15
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Optional

# 英語で非常に高頻度だが他のラテン文字言語では低頻度のストップワード
_ENGLISH_STOP_WORDS: frozenset[str] = frozenset({
    "the", "a", "an", "is", "are", "was", "were", "been", "be",
    "have", "has", "had", "do", "does", "did", "will", "would",
    "could", "should", "may", "might", "shall", "can",
    "not", "no", "but", "or", "and", "if", "then", "than",
    "that", "this", "these", "those", "it", "its",
    "of", "in", "to", "for", "with", "on", "at", "by", "from",
    "as", "into", "through", "during", "before", "after",
    "he", "she", "they", "we", "you", "his", "her", "their", "our",
    "which", "what", "where", "when", "who", "how",
    "there", "here", "also", "very", "just", "about",
})


@dataclass
class ValidationResult:
    """言語バリデーション結果。"""

    is_valid: bool
    lang: str
    reason: str
    english_density: Optional[float] = None


def _has_japanese_characters(text: str) -> bool:
    """テキストにひらがな・カタカナ・CJK 漢字が含まれるか判定する。"""
    # ひらがな: U+3040-U+309F, カタカナ: U+30A0-U+30FF, CJK 漢字: U+4E00-U+9FFF
    return bool(re.search(r"[\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FFF]", text))


def _english_stop_word_density(text: str) -> float:
    """テキスト中の英語ストップワード密度（0.0〜1.0）を計算する。

    Args:
        text: 判定対象テキスト

    Returns:
        ストップワードの割合。単語数が 0 なら 0.0 を返す。
    """
    words = re.findall(r"[a-zA-Z]+", text.lower())
    if not words:
        return 0.0
    stop_count = sum(1 for w in words if w in _ENGLISH_STOP_WORDS)
    return stop_count / len(words)


def validate_translation_language(
    lang: str,
    translation: dict,
) -> ValidationResult:
    """翻訳結果が指定言語で書かれているかを検証する。

    narrative_content（最長フィールド）を使って判定し、なければ summary にフォールバック。
    20語未満は判定不能のため安全側で通す。

    Args:
        lang: 期待する言語コード（ja, es, de, fr, nl, pt）
        translation: 翻訳結果の dict（title, summary, narrative_content 等）

    Returns:
        ValidationResult: バリデーション結果
    """
    # 判定対象テキストの取得（narrative_content > summary の優先順）
    text = translation.get("narrative_content", "") or translation.get("summary", "")
    if not text or not isinstance(text, str):
        return ValidationResult(
            is_valid=True, lang=lang,
            reason="判定対象テキストなし（安全側で通過）",
        )

    # 単語数チェック（20語未満は判定不能 → 安全側で通す）
    word_count = len(re.findall(r"\S+", text))
    if word_count < 20:
        return ValidationResult(
            is_valid=True, lang=lang,
            reason=f"テキストが短すぎる（{word_count}語）— 判定不能のため通過",
        )

    # 日本語判定（Unicode 範囲）
    if lang == "ja":
        if _has_japanese_characters(text):
            return ValidationResult(is_valid=True, lang=lang, reason="日本語文字を検出")
        # 日本語文字が含まれない → 英語のまま出力された可能性が高い
        density = _english_stop_word_density(text)
        return ValidationResult(
            is_valid=False, lang=lang,
            reason=f"日本語文字なし（英語ストップワード密度: {density:.2f}）",
            english_density=density,
        )

    # ラテン文字言語（es/de/fr/nl/pt）の判定（英語ストップワード密度）
    density = _english_stop_word_density(text)
    if density >= 0.15:
        return ValidationResult(
            is_valid=False, lang=lang,
            reason=f"英語ストップワード密度が閾値超過（{density:.2f} >= 0.15）",
            english_density=density,
        )

    return ValidationResult(
        is_valid=True, lang=lang,
        reason=f"英語ストップワード密度正常（{density:.2f} < 0.15）",
        english_density=density,
    )
