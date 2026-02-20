"""Publisher Agent - Custom Agent による決定的公開処理

LLM を介さず、セッション状態から直接 Firestore に公開する Custom Agent。
本番パイプラインで LlmAgent が publish_mystery ツールを呼び出さずに終了した
障害を受け、BaseAgent 継承の決定的実行に置き換えた。

Input: All assets (mystery_report, creative_content, visual_assets, 6-lang translations)
Output: Firestore documents with pending status (EN base + translations map)
"""

import json
import logging
from collections.abc import AsyncGenerator
from pathlib import Path

from dotenv import load_dotenv
from google.adk.agents import BaseAgent
from google.adk.agents.invocation_context import InvocationContext
from google.adk.events.event import Event, EventActions
from google.genai import types

from ..tools.publisher_tools import _PublishContext, publish_mystery

load_dotenv(Path(__file__).parent.parent / ".env")  # mystery_agents/.env

logger = logging.getLogger(__name__)


class PublisherAgent(BaseAgent):
    """Custom Agent: LLM を介さず直接 Firestore に公開する。"""

    async def _run_async_impl(
        self, ctx: InvocationContext
    ) -> AsyncGenerator[Event, None]:
        state = ctx.session.state

        # structured_report から ID 生成用データを取得
        sr = state.get("structured_report", {})
        if not isinstance(sr, dict):
            sr = {}
        minimal_json = json.dumps(
            {
                "classification": sr.get("classification", ""),
                "state_code": sr.get("state_code", ""),
                "area_code": sr.get("area_code", ""),
            }
        )

        # セッション状態のコピーを渡して publish_mystery を実行
        state_copy = dict(state)
        publish_ctx = _PublishContext(state=state_copy)
        result_json = publish_mystery(minimal_json, "", publish_ctx)

        # state_delta: published_mystery_id + published_episode をセッションに反映
        state_delta: dict[str, object] = {"published_episode": result_json}
        mystery_id = state_copy.get("published_mystery_id")
        if mystery_id:
            state_delta["published_mystery_id"] = mystery_id

        yield Event(
            invocation_id=ctx.invocation_id,
            author=self.name,
            branch=ctx.branch,
            content=types.Content(
                role="model", parts=[types.Part(text=result_json)]
            ),
            actions=EventActions(state_delta=state_delta),
        )


publisher_agent = PublisherAgent(
    name="publisher",
    description=(
        "Content manager agent that saves all assets to Firestore. "
        "Deterministic execution without LLM — reads session state directly."
    ),
)
