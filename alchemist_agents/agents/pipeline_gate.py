"""Alchemist パイプラインゲートコールバック。

前段エージェントの出力を確認し、有意なデータがない場合に
後続エージェントをスキップしてトークン消費を防ぐ。

shared/constants.py の is_meaningful() を使用して判定ロジックを統一する。
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Optional

from google.genai import types

from shared.constants import is_meaningful

if TYPE_CHECKING:
    from google.adk.agents.callback_context import CallbackContext

logger = logging.getLogger(__name__)


def make_design_gate():
    """creative_content が空 or 失敗マーカーなら Alchemist をスキップ。"""

    def gate(callback_context: CallbackContext) -> Optional[types.Content]:
        content = callback_context.state.get("creative_content", "")
        if is_meaningful(content):
            logger.info(
                "Pipeline gate [design]: 通過",
                extra={"gate_name": "design", "decision": "pass"},
            )
            return None

        message = "NO_DESIGN: No blog article available. Skipping design generation."
        logger.warning(
            "Pipeline gate [design]: %s", message,
            extra={"gate_name": "design", "decision": "skip", "reason": message},
        )
        return types.Content(
            parts=[types.Part(text=message)],
            role="model",
        )

    return gate


def make_render_gate():
    """structured_design_proposal が空/未設定なら Renderer をスキップ。"""

    def gate(callback_context: CallbackContext) -> Optional[types.Content]:
        proposal = callback_context.state.get("structured_design_proposal")
        if isinstance(proposal, dict) and proposal.get("products"):
            logger.info(
                "Pipeline gate [render]: 通過",
                extra={"gate_name": "render", "decision": "pass"},
            )
            return None

        message = "NO_RENDER: No design proposal available. Skipping asset rendering."
        logger.warning(
            "Pipeline gate [render]: %s", message,
            extra={"gate_name": "render", "decision": "skip", "reason": message},
        )
        return types.Content(
            parts=[types.Part(text=message)],
            role="model",
        )

    return gate
