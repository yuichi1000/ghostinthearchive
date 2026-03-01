"""パイプライン全体で使用される定数の一元管理。

Python ロジック（言語選択、翻訳収集、ステータス設定、失敗判定等）で
使用する定数を集約し、typo やコピペ不一致を防止する。

注意: エージェント instruction（LLM プロンプト）内の失敗マーカーリテラル
（例: "Output INSUFFICIENT_DATA if ..."）はここでは管理しない。
プロンプト内のリテラルは LLM が直接読むものであり、Python 定数に置換できない。
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# 言語設定
# ---------------------------------------------------------------------------
# 調査対象言語（全7言語を常時実行）
ALLOWED_LANGUAGES: set[str] = {"en", "de", "es", "fr", "ja", "nl", "pt"}

# selected_languages 未設定時のデフォルト（全言語）
DEFAULT_SELECTED_LANGUAGES: list[str] = sorted(ALLOWED_LANGUAGES)

# Translator が翻訳する対象言語（英語から各言語へ）
TRANSLATION_LANGUAGES: list[str] = ["ja", "es", "de"]

# ラテン文字系言語（ASCII ヒューリスティックで英語と区別不能）
LATIN_SCRIPT_LANGUAGES: frozenset[str] = frozenset({
    "de", "es", "fr", "nl", "pt", "en",
})

# ---------------------------------------------------------------------------
# ステータス / スキーマ
# ---------------------------------------------------------------------------
STATUS_PENDING = "pending"
STATUS_PUBLISHED = "published"

# Firestore ドキュメント構造のバージョン
SCHEMA_VERSION = 2

# ---------------------------------------------------------------------------
# 失敗マーカー
# ---------------------------------------------------------------------------
# エージェントが出力する失敗マーカー文字列。
# セッション状態の値がこれらで始まる場合、有意なデータなしと判定する。
FAILURE_MARKERS: frozenset[str] = frozenset({
    "NO_DOCUMENTS_FOUND",
    "NO_FULLTEXT_AVAILABLE",
    "INSUFFICIENT_DATA",
    "NO_CONTENT",
    "Not available",
})


def is_meaningful(value: str | None) -> bool:
    """セッション状態の値が有意なデータを含むか判定する。

    テキストの先頭が失敗マーカーで始まる場合のみ「無意味」と判定する。
    ドキュメント本文の途中や末尾に部分的な失敗マーカーが含まれていても、
    先頭に有意なデータがあれば有意とみなす。
    """
    if not value:
        return False
    text = str(value).strip()
    return not any(text.startswith(marker) for marker in FAILURE_MARKERS)
