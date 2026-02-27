"""ADK 軽量実行ヘルパー — 単一エージェント1回実行のボイラープレートを一元化。

shared/orchestrator.py は blog/podcast パイプライン向けの重量級ランナー
（PipelineLogger, pipeline_run 等を含む）。Curator の「単一エージェント1回実行」
ユースケースとは目的が異なるため、curator_agents 内に軽量ヘルパーとして配置する。
"""

from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types


async def run_single_agent(
    agent,
    *,
    app_name: str,
    user_id: str,
    session_id: str,
    state: dict,
    user_message: str,
) -> str:
    """単一 ADK エージェントを1回実行し、テキスト出力を返す。

    InMemorySessionService でセッションを作成し、Runner.run_async で
    イベントを収集して結合テキストを返す。

    Args:
        agent: 実行する ADK エージェント（LlmAgent 等）
        app_name: ADK アプリケーション名
        user_id: セッションのユーザー ID
        session_id: セッション ID
        state: セッション初期状態の dict
        user_message: エージェントに送信するユーザーメッセージ

    Returns:
        エージェントの全テキスト出力を結合した文字列
    """
    session_service = InMemorySessionService()
    runner = Runner(
        agent=agent,
        app_name=app_name,
        session_service=session_service,
    )

    await session_service.create_session(
        app_name=app_name,
        user_id=user_id,
        session_id=session_id,
        state=state,
    )

    result_text = ""
    async for event in runner.run_async(
        user_id=user_id,
        session_id=session_id,
        new_message=types.Content(
            role="user",
            parts=[types.Part(text=user_message)],
        ),
    ):
        if event.content and event.content.parts:
            for part in event.content.parts:
                if hasattr(part, "text") and part.text:
                    result_text += part.text

    return result_text
