"""語数カウント・検証ツール。

エージェントが自身の出力テキストの語数を確認し、
指定範囲内に収まっているかチェックするためのセルフチェックツール。
プロンプト指示だけでは語数制約が守られない場合の安全策として機能する。
"""

from __future__ import annotations

import json


def count_words(text: str, min_words: int = 0, max_words: int = 0) -> str:
    """テキストの語数をカウントし、指定範囲との比較結果を返す。

    Args:
        text: 語数をカウントするテキスト
        min_words: 最小語数（0 の場合はチェックしない）
        max_words: 最大語数（0 の場合はチェックしない）

    Returns:
        JSON 文字列: word_count, within_range, message
    """
    words = text.split()
    count = len(words)
    result: dict = {"word_count": count}

    if min_words > 0 and max_words > 0:
        result["min_words"] = min_words
        result["max_words"] = max_words
        result["within_range"] = min_words <= count <= max_words
        if count < min_words:
            result["message"] = (
                f"Too short by {min_words - count} words. "
                f"Current: {count}, minimum: {min_words}. "
                "Expand your analysis with more detail, evidence, and citations."
            )
        elif count > max_words:
            result["message"] = (
                f"Too long by {count - max_words} words. "
                f"Current: {count}, maximum: {max_words}. "
                "Tighten your prose — remove redundancy, not substance."
            )
        else:
            result["message"] = (
                f"Word count ({count}) is within the expected range "
                f"({min_words}–{max_words})."
            )
    else:
        result["message"] = f"Word count: {count}. No range specified for validation."

    return json.dumps(result, ensure_ascii=False)
