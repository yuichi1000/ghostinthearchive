"""言語ゲートコールバック。

ADK の before_agent_callback パターンを使用して、
テーマに基づいて選択されていない言語のエージェントをスキップする。
MultilingualOrchestrator (カスタム BaseAgent) の代替として機能する。
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from google.genai import types

from shared.constants import DEFAULT_SELECTED_LANGUAGES

if TYPE_CHECKING:
    from google.adk.agents.callback_context import CallbackContext


def make_language_gate(lang_code: str):
    """before_agent_callback: 選択されていない言語のエージェントをスキップ。

    selected_languages に含まれない言語の場合、空の Content を返してスキップする。
    selected_languages が未設定の場合は ["en"] をデフォルトとする。
    """

    def gate(callback_context: CallbackContext) -> Optional[types.Content]:
        selected = callback_context.state.get("selected_languages", DEFAULT_SELECTED_LANGUAGES)
        if not isinstance(selected, list):
            selected = list(DEFAULT_SELECTED_LANGUAGES)
        if lang_code not in selected:
            return types.Content(
                parts=[types.Part(text="")], role="model"
            )
        return None

    return gate


def make_debate_gate(lang_code: str):
    """before_agent_callback: 未選択 or 1言語のみ or 分析が不十分な場合スキップ。

    討論は2言語以上の有意な分析が存在する場合にのみ意味があるため、
    言語が未選択、選択言語が1つだけ、または Scholar の分析結果が
    不十分な場合はスキップする。
    """

    def gate(callback_context: CallbackContext) -> Optional[types.Content]:
        selected = callback_context.state.get("selected_languages", DEFAULT_SELECTED_LANGUAGES)
        if not isinstance(selected, list):
            selected = list(DEFAULT_SELECTED_LANGUAGES)
        if lang_code not in selected or len(selected) < 2:
            return types.Content(
                parts=[types.Part(text="")], role="model"
            )
        # Scholar が有意な分析を出していない場合もスキップ
        analysis = callback_context.state.get(f"scholar_analysis_{lang_code}", "")
        if not analysis or "INSUFFICIENT_DATA" in str(analysis) or "Not available" in str(analysis):
            return types.Content(
                parts=[types.Part(text="")], role="model"
            )
        return None

    return gate


def make_debate_loop_gate():
    """before_agent_callback: 有意な分析が2言語未満なら討論全体をスキップ。

    LoopAgent 全体のゲート。Scholar が実際に有意な分析を出した言語数をカウントし、
    2言語未満なら討論は不要と判断してスキップする。
    """

    def gate(callback_context: CallbackContext) -> Optional[types.Content]:
        selected = callback_context.state.get("selected_languages", DEFAULT_SELECTED_LANGUAGES)
        if not isinstance(selected, list):
            selected = list(DEFAULT_SELECTED_LANGUAGES)

        # 有意な分析を出した Scholar の数をカウント
        meaningful = 0
        for lang in selected:
            analysis = callback_context.state.get(f"scholar_analysis_{lang}", "")
            if (
                analysis
                and "INSUFFICIENT_DATA" not in str(analysis)
                and "Not available" not in str(analysis)
            ):
                meaningful += 1

        if meaningful < 2:
            return types.Content(
                parts=[types.Part(text="")], role="model"
            )
        return None

    return gate
