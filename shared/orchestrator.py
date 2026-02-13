"""Pipeline Orchestrator - ADK パイプラインの実行制御

Runner セットアップ、イベントループ処理、進捗追跡、セッション管理を一元化する。
CLI と Cloud Run Service の両方から呼ばれるビジネスロジック層。

並列実行エージェント（ParallelAgent）のインターリーブイベントに対応:
- エージェントごとに独立したテキスト蓄積とログインデックスを管理
- 同一エージェントの複数イベントを1エントリに集約（2重エントリ防止）
- スキップされたエージェント（空テキスト + 短時間）のログを除去
"""

import asyncio
import json
import logging
from dataclasses import dataclass, field
from typing import Callable

from google.adk.agents.run_config import RunConfig
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

from mystery_agents.utils.pipeline_logger import PipelineLogger
from shared.pipeline_run import (
    create_pipeline_run,
    update_agent_started,
    update_agent_completed,
    complete_pipeline_run,
    error_pipeline_run,
)

logger = logging.getLogger(__name__)

# スキップされたエージェント判定の閾値（秒）
_SKIP_DURATION_THRESHOLD = 0.5

# イベントコールバック型
OnText = Callable[[str], None]


@dataclass
class PipelineResult:
    """パイプライン実行結果"""

    run_id: str | None
    mystery_id: str | None = None  # blog パイプラインのみ
    logs: list[dict] = field(default_factory=list)
    session_state: dict = field(default_factory=dict)


def _complete_agent(
    pipeline_logger: PipelineLogger,
    run_id: str | None,
    agent_name: str,
    texts: list[str],
    log_index: int | None,
) -> None:
    """エージェントを完了マークし、スキップ判定を行う。

    空テキスト + 短時間（< 0.5s）のエージェントはスキップとみなし、ログから除去する。
    """
    summary = " ".join(texts)[:200] or "(no text output)"
    pipeline_logger.complete_agent(agent_name, summary)

    # スキップ判定: 空テキスト + 短時間ならログから除去
    completed_log = None
    for log in reversed(pipeline_logger.get_logs()):
        if log["agent_name"] == agent_name and log["status"] == "completed":
            completed_log = log
            break

    if completed_log:
        duration = completed_log.get("duration_seconds") or 0
        is_skipped = (
            not texts
            and duration < _SKIP_DURATION_THRESHOLD
        )
        if is_skipped:
            pipeline_logger.remove_last_log(agent_name)
            return

    # Firestore に完了を通知
    completed_logs = pipeline_logger.get_logs()
    if completed_logs:
        update_agent_completed(run_id, log_index, completed_log)


async def run_pipeline(
    agent,
    app_name: str,
    user_message: str,
    initial_state: dict,
    *,
    run_id: str | None = None,
    run_type: str = "blog",
    timeout_seconds: int = 1800,
    max_llm_calls: int = 120,
    skip_authors: set[str] | None = None,
    on_text: OnText | None = None,
) -> PipelineResult:
    """ADK パイプラインを実行する。

    責務:
    1. pipeline_run ドキュメント作成（run_id 未指定時）
    2. InMemorySessionService + Runner セットアップ
    3. イベントループ処理（エージェント遷移検出、進捗追跡、Firestore 同期）
    4. セッション状態からの結果抽出
    5. pipeline_run 完了/エラーマーク

    並列実行対応:
    - agent_texts: エージェントごとのテキスト蓄積
    - agent_log_indices: エージェントごとの Firestore ログインデックス
    - 新規 author 検出時にエントリ作成、既存 author は蓄積のみ

    Args:
        agent: ADK Agent（ghost_commander / podcast_commander）
        app_name: ADK アプリケーション名
        user_message: ユーザーメッセージ（パイプライン起動テキスト）
        initial_state: セッション初期状態
        run_id: パイプライン実行 ID（未指定時は自動生成）
        run_type: パイプライン種別 ("blog", "podcast")
        timeout_seconds: タイムアウト秒数
        max_llm_calls: LLM 呼び出し上限
        skip_authors: ログ対象外のエージェント名セット
        on_text: テキスト出力コールバック（CLI の print 等）

    Returns:
        PipelineResult: 実行結果
    """
    if skip_authors is None:
        skip_authors = set()

    # pipeline_run ドキュメント作成
    if run_id is None:
        create_kwargs = {"query": user_message} if run_type == "blog" else {}
        run_id = create_pipeline_run(run_type, **create_kwargs)

    # Runner + Session セットアップ
    session_service = InMemorySessionService()
    runner = Runner(
        agent=agent,
        app_name=app_name,
        session_service=session_service,
    )

    user_id = "pipeline_user"
    session_id = "pipeline_session"

    state = {
        "pipeline_log": [],
        "pipeline_run_id": run_id,
        **initial_state,
    }

    await session_service.create_session(
        app_name=app_name,
        user_id=user_id,
        session_id=session_id,
        state=state,
    )

    # 進捗追跡（並列対応: エージェントごとの dict で管理）
    pipeline_logger = PipelineLogger()
    agent_texts: dict[str, list[str]] = {}  # {agent_name: [text_chunks]}
    agent_log_indices: dict[str, int | None] = {}  # {agent_name: firestore_index}

    run_config = RunConfig(max_llm_calls=max_llm_calls)

    try:
        async with asyncio.timeout(timeout_seconds):
            async for event in runner.run_async(
                user_id=user_id,
                session_id=session_id,
                new_message=types.Content(
                    role="user",
                    parts=[types.Part(text=user_message)],
                ),
                run_config=run_config,
            ):
                # エージェント遷移検出
                author = getattr(event, "author", None)
                if not author or author in skip_authors:
                    # skip_authors のイベントはステージ境界として検出
                    # 前ステージの全 active エージェントを一括完了
                    if author and author in skip_authors and agent_texts:
                        for name in list(agent_texts.keys()):
                            _complete_agent(
                                pipeline_logger,
                                run_id,
                                name,
                                agent_texts.pop(name),
                                agent_log_indices.pop(name, None),
                            )
                    continue

                # 新規エージェントの場合のみエントリ作成
                if author not in agent_texts:
                    agent_texts[author] = []
                    pipeline_logger.start_agent(author)
                    agent_log_indices[author] = update_agent_started(
                        run_id, author, pipeline_logger.get_logs()[-1]
                    )

                # テキスト出力処理
                if event.content and event.content.parts:
                    for part in event.content.parts:
                        if hasattr(part, "text") and part.text:
                            if on_text:
                                on_text(part.text)
                            agent_texts[author].append(part.text[:100])

        # 残存エージェントを完了マーク
        for name in list(agent_texts.keys()):
            _complete_agent(
                pipeline_logger,
                run_id,
                name,
                agent_texts.pop(name),
                agent_log_indices.pop(name, None),
            )

        # セッション状態を取得
        session = await session_service.get_session(
            app_name=app_name,
            user_id=user_id,
            session_id=session_id,
        )
        session_state = dict(session.state) if session else {}

        # pipeline_log をセッション状態に保存
        if session:
            session.state["pipeline_log"] = pipeline_logger.get_logs()

        # mystery_id 抽出（blog パイプラインのみ）
        mystery_id = None
        if run_type == "blog" and session_state:
            published = session_state.get("published_episode", "")
            if isinstance(published, str) and published.startswith("{"):
                try:
                    published_data = json.loads(published)
                    mystery_id = published_data.get("mystery_id")
                except (json.JSONDecodeError, AttributeError):
                    pass
            elif isinstance(published, dict):
                mystery_id = published.get("mystery_id")

        complete_pipeline_run(run_id, mystery_id=mystery_id)

        return PipelineResult(
            run_id=run_id,
            mystery_id=mystery_id,
            logs=pipeline_logger.get_logs(),
            session_state=session_state,
        )

    except TimeoutError:
        error_pipeline_run(run_id, f"Pipeline timed out after {timeout_seconds}s")
        raise
    except Exception as e:
        error_pipeline_run(run_id, str(e))
        raise
