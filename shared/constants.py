"""パイプライン全体で使用される定数の一元管理。

Python ロジック（言語選択、翻訳収集、ステータス設定等）で使用する定数を
集約し、typo やコピペ不一致を防止する。

注意: エージェント instruction（LLM プロンプト）内の失敗マーカーリテラル
（例: "Output INSUFFICIENT_DATA if ..."）はここでは管理しない。
プロンプト内のリテラルは LLM が直接読むものであり、Python 定数に置換できない。
"""

# ---------------------------------------------------------------------------
# 言語設定
# ---------------------------------------------------------------------------
# ThemeAnalyzer が選択可能な調査言語（英語は常に含まれる）
ALLOWED_LANGUAGES: set[str] = {"en", "de", "es", "fr", "ja", "nl", "pt"}

# 同時に選択できる最大言語数（コスト・時間制御）
MAX_LANGUAGES = 4

# selected_languages 未設定時のデフォルト
DEFAULT_SELECTED_LANGUAGES: list[str] = ["en"]

# Translator が翻訳する対象言語（英語から各言語へ）
TRANSLATION_LANGUAGES: list[str] = ["ja", "es", "de", "fr", "nl", "pt"]

# ---------------------------------------------------------------------------
# ステータス / スキーマ
# ---------------------------------------------------------------------------
STATUS_PENDING = "pending"
STATUS_PUBLISHED = "published"

# Firestore ドキュメント構造のバージョン
SCHEMA_VERSION = 2
