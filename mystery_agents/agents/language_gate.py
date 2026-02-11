"""言語ゲートコールバック。

ADK の before_agent_callback パターンを使用して、
テーマに基づいて選択されていない言語のエージェントをスキップする。
MultilingualOrchestrator (カスタム BaseAgent) の代替として機能する。
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from google.genai import types

if TYPE_CHECKING:
    from google.adk.agents.callback_context import CallbackContext


def make_language_gate(lang_code: str):
    """before_agent_callback: 選択されていない言語のエージェントをスキップ。

    selected_languages に含まれない言語の場合、空の Content を返してスキップする。
    selected_languages が未設定の場合は ["en"] をデフォルトとする。
    """

    def gate(callback_context: CallbackContext) -> Optional[types.Content]:
        selected = callback_context.state.get("selected_languages", ["en"])
        if not isinstance(selected, list):
            selected = ["en"]
        if lang_code not in selected:
            return types.Content(
                parts=[types.Part(text="")], role="model"
            )
        return None

    return gate


def make_debate_gate(lang_code: str):
    """before_agent_callback: 未選択 or 1言語のみの場合スキップ。

    討論は2言語以上の分析が存在する場合にのみ意味があるため、
    言語が未選択、または選択言語が1つだけの場合はスキップする。
    """

    def gate(callback_context: CallbackContext) -> Optional[types.Content]:
        selected = callback_context.state.get("selected_languages", ["en"])
        if not isinstance(selected, list):
            selected = ["en"]
        if lang_code not in selected or len(selected) < 2:
            return types.Content(
                parts=[types.Part(text="")], role="model"
            )
        return None

    return gate
