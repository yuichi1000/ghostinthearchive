"""Podcast パイプラインゲートコールバック。

creative_content の存在を確認し、有意なデータがない場合に
後続エージェントをスキップしてトークン消費を防ぐ。

shared/constants.py の is_meaningful() を使用して判定ロジックを統一する。
cli.py で事前バリデーション済みのため防御的ゲート（defense-in-depth）。
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Optional

from google.genai import types

from shared.constants import is_meaningful

if TYPE_CHECKING:
    from google.adk.agents.callback_context import CallbackContext

logger = logging.getLogger(__name__)


def make_script_gate():
    """creative_content が空 or 失敗マーカーなら全パイプラインをスキップ。"""

    def gate(callback_context: CallbackContext) -> Optional[types.Content]:
        content = callback_context.state.get("creative_content", "")
        if is_meaningful(content):
            logger.info(
                "Pipeline gate [script]: 通過",
                extra={"gate_name": "script", "decision": "pass"},
            )
            return None

        message = "NO_SCRIPT: No blog article available. Skipping podcast script generation."
        logger.warning(
            "Pipeline gate [script]: %s", message,
            extra={"gate_name": "script", "decision": "skip", "reason": message},
        )
        return types.Content(
            parts=[types.Part(text=message)],
            role="model",
        )

    return gate
