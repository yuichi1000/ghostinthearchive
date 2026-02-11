"""ThemeAnalyzer 用ツール。

テーマ分析結果（関連言語リスト）をセッション状態に保存する。
"""

import json

from google.adk.tools.tool_context import ToolContext

# 許可される言語コード
ALLOWED_LANGUAGES = {"en", "de", "es", "fr", "nl", "pt"}
# 同時に選択できる最大言語数（コスト・時間制御）
MAX_LANGUAGES = 4


def save_language_selection(
    languages_json: str,
    tool_context: ToolContext,
) -> str:
    """Save the selected languages for multilingual investigation to session state.

    The ThemeAnalyzer calls this tool to store which languages are relevant
    for the current investigation theme. Downstream agents (Librarians, Scholars)
    will be dynamically selected based on this list.

    Args:
        languages_json: JSON array of ISO 639-1 language codes.
            Example: '["en", "de", "nl"]'
        tool_context: ADK tool context for session state access.

    Returns:
        JSON string with save status and validated language list.
    """
    try:
        languages = json.loads(languages_json)
    except json.JSONDecodeError as e:
        # パースエラー時は英語のみにフォールバック
        tool_context.state["selected_languages"] = ["en"]
        return json.dumps(
            {
                "status": "fallback",
                "error": f"Invalid JSON: {e}",
                "selected": ["en"],
            },
            ensure_ascii=False,
        )

    if not isinstance(languages, list):
        languages = ["en"]

    # バリデーション: 許可リスト以外を除外
    valid = [lang for lang in languages if isinstance(lang, str) and lang in ALLOWED_LANGUAGES]

    # 英語は必ず含める（フォールバック保証）
    if "en" not in valid:
        valid.insert(0, "en")

    # 上限制限
    valid = valid[:MAX_LANGUAGES]

    tool_context.state["selected_languages"] = valid

    # 討論ホワイトボードを初期化（LoopAgent の累積書き込み用）
    tool_context.state["debate_whiteboard"] = ""

    # 未選択言語のセッション変数にデフォルト値を設定
    # Scholar の instruction が全言語の {scholar_analysis_*} を参照するため、
    # 未設定だと ADK の template 展開で KeyError になる
    unselected = ALLOWED_LANGUAGES - set(valid)
    for lang in unselected:
        tool_context.state[f"collected_documents_{lang}"] = (
            f"Not available: {lang} was not selected for this investigation."
        )
        tool_context.state[f"scholar_analysis_{lang}"] = (
            f"Not available: {lang} was not selected for this investigation."
        )

    return json.dumps(
        {
            "status": "success",
            "selected": valid,
            "total_languages": len(valid),
        },
        ensure_ascii=False,
    )
