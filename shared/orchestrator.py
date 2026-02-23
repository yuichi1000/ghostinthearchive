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
import time
from dataclasses import dataclass, field
from typing import Callable

from google.adk.agents.run_config import RunConfig
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

from mystery_agents.agents.pipeline_gate import _is_meaningful
from mystery_agents.utils.pipeline_logger import PipelineLogger
from shared.logging_config import PipelineContext, set_pipeline_context
from shared.pipeline_run import (
    create_pipeline_run,
    update_agent_started,
    update_agent_completed,
    complete_pipeline_run,
    error_pipeline_run,
)

logger = logging.getLogger(__name__)


def _format_exception_group(exc: BaseException) -> str:
    """ExceptionGroup からサブ例外を再帰的に抽出し、可読文字列に整形する。"""
    if not isinstance(exc, ExceptionGroup):
        return str(exc)
    parts = []
    for sub in exc.exceptions:
        if isinstance(sub, ExceptionGroup):
            parts.append(_format_exception_group(sub))
        else:
            parts.append(f"{type(sub).__name__}: {sub}")
    return " | ".join(parts)


def _is_rate_limit_error(exc: BaseException) -> bool:
    """429 レート制限エラーか判定する。ExceptionGroup も再帰的にチェック。"""
    if isinstance(exc, ExceptionGroup):
        return any(_is_rate_limit_error(sub) for sub in exc.exceptions)
    error_str = str(exc)
    return "429" in error_str or "RESOURCE_EXHAUSTED" in error_str


# 一時的接続エラーの判定マーカー（httpx を import せず文字列ベースで判定）
_TRANSIENT_ERROR_MARKERS = (
    "RemoteProtocolError",
    "Server disconnected",
    "NetworkError",
    "ConnectError",
    "ReadError",
    "WriteError",
    "ReadTimeout",
    "ConnectTimeout",
    "PoolTimeout",
    "ConnectionReset",
    "ConnectionRefused",
)


def _is_transient_connection_error(exc: BaseException) -> bool:
    """一時的な接続エラーか判定する。ExceptionGroup も再帰的にチェック。"""
    if isinstance(exc, ExceptionGroup):
        return any(_is_transient_connection_error(sub) for sub in exc.exceptions)
    exc_info = f"{type(exc).__name__} {exc}"
    return any(marker in exc_info for marker in _TRANSIENT_ERROR_MARKERS)


# === 日本語訳 ===
# リトライ設定
# SDK のリトライで解決しない長時間レート制限に対応するため、
# オーケストレーターレベルで 1分待ってパイプラインを再実行する（最大1回リトライ）。
# 接続エラーはより短い間隔（15秒）でリトライする。
# === End 日本語訳 ===
_RATE_LIMIT_RETRY_DELAY = 60   # 1分
_RATE_LIMIT_MAX_RETRIES = 1    # 最大1回リトライ（計2回試行）
_CONNECTION_ERROR_RETRY_DELAY = 15  # 接続エラー: 15秒

# スキップされたエージェント判定の閾値（秒）
_SKIP_DURATION_THRESHOLD = 0.5

# イベントコールバック型
OnText = Callable[[str], None]


def _build_state_summary(session_state: dict) -> dict:
    """デバッグ用にセッション状態キーの存在と長さをサマリ化する。"""
    keys = [
        "mystery_report", "creative_content", "structured_report",
        "image_metadata", "published_mystery_id", "published_episode",
    ]
    summary = {}
    for k in keys:
        v = session_state.get(k)
        if v is None:
            summary[k] = "missing"
        elif isinstance(v, str):
            summary[k] = f"present ({len(v)} chars)"
        elif isinstance(v, dict):
            summary[k] = f"present (dict, {len(v)} keys)"
        else:
            summary[k] = f"present ({type(v).__name__})"
    return {"session_state_summary": summary}


def _detect_gate_failure(session_state: dict) -> tuple[str, dict]:
    """セッション状態からゲート失敗を検出し、エラーメッセージと詳細情報を返す。

    blog パイプラインで mystery_id が None の場合に呼ばれる。
    セッション状態の mystery_report → creative_content を順にチェックし、
    失敗マーカーを検出した段階で対応するメッセージと error_detail を返す。
    """
    detail = _build_state_summary(session_state)

    # LLM メタデータがあれば追加（安全フィルタ等の原因特定用）
    llm_meta = session_state.get("storyteller_llm_metadata")
    if llm_meta:
        detail["storyteller_llm_metadata"] = llm_meta

    mystery_report = session_state.get("mystery_report", "")
    if not _is_meaningful(mystery_report):
        return "十分な資料が見つからなかったため、記事を生成できませんでした", {
            "error_type": "gate_failure",
            "failed_stage": "scholar/polymath",
            **detail,
        }

    creative_content = session_state.get("creative_content", "")
    if not _is_meaningful(creative_content):
        return "記事の生成に失敗しました", {
            "error_type": "gate_failure",
            "failed_stage": "storyteller",
            **detail,
        }

    # mystery_id なし + 失敗マーカーなし → 公開処理で問題発生
    return "記事の公開処理で問題が発生しました", {
        "error_type": "publish_failed",
        "failed_stage": "publisher",
        **detail,
    }


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

    # 完了ログ出力
    if completed_log:
        duration = completed_log.get("duration_seconds") or 0
        logger.info(
            "エージェント完了: %s (%.1fs)", agent_name, duration,
            extra={"agent_name": agent_name, "status": "completed", "duration_seconds": duration},
        )

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
    sequential_agents: set[str] | None = None,
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

    直列実行対応（sequential_agents）:
    - SequentialAgent 内のサブエージェントは遷移イベントを発行しないため、
      新しいメンバーが開始されたとき、同セット内の既存 active エージェントを自動完了する

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
        sequential_agents: 直列実行エージェント名セット（新メンバー開始時に既存を自動完了）
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

    # 構造化ログコンテキスト設定
    set_pipeline_context(PipelineContext(run_id=run_id, pipeline_type=run_type))

    pipeline_start_time = time.monotonic()
    logger.info("パイプライン開始: %s", run_type, extra={"status": "started"})

    user_id = "pipeline_user"
    session_id = "pipeline_session"

    # リトライループ（レートリミット + 一時的接続エラー対応）
    # SDK の 10回リトライで解決しない長時間レート制限、および
    # トランスポート層の一時的接続エラー（RemoteProtocolError 等）に対応
    last_error: Exception | None = None
    last_error_is_rate_limit: bool = False
    for attempt in range(_RATE_LIMIT_MAX_RETRIES + 1):
        if attempt > 0:
            retry_delay = (
                _RATE_LIMIT_RETRY_DELAY if last_error_is_rate_limit
                else _CONNECTION_ERROR_RETRY_DELAY
            )
            error_label = "レートリミット" if last_error_is_rate_limit else "接続エラー"
            logger.warning(
                "%s: %d秒後にパイプラインをリトライ (試行 %d/%d)",
                error_label, retry_delay, attempt + 1, _RATE_LIMIT_MAX_RETRIES + 1,
                extra={"status": "retrying", "attempt": attempt + 1},
            )
            await asyncio.sleep(retry_delay)

        # 各試行で Session/Runner を再作成
        session_service = InMemorySessionService()
        runner = Runner(
            agent=agent,
            app_name=app_name,
            session_service=session_service,
        )

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

                    # 順次実行エージェントの直列完了:
                    # 同セット内の既存 active エージェントを自動完了する
                    if sequential_agents and author in sequential_agents:
                        for name in list(agent_texts.keys()):
                            if name in sequential_agents and name != author:
                                _complete_agent(
                                    pipeline_logger,
                                    run_id,
                                    name,
                                    agent_texts.pop(name),
                                    agent_log_indices.pop(name, None),
                                )

                    # 新規エージェントの場合のみエントリ作成
                    if author not in agent_texts:
                        agent_texts[author] = []
                        pipeline_logger.start_agent(author)
                        logger.info(
                            "エージェント開始: %s", author,
                            extra={"agent_name": author, "status": "started"},
                        )
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
                # 優先: ツールがセッション状態に直接書き込んだ mystery_id
                mystery_id = session_state.get("published_mystery_id")

                # フォールバック: published_episode テキストから抽出
                if not mystery_id:
                    published = session_state.get("published_episode", "")
                    if isinstance(published, str):
                        text = published.strip()
                        if text.startswith("{"):
                            try:
                                published_data = json.loads(text)
                                mystery_id = published_data.get("mystery_id")
                            except (json.JSONDecodeError, AttributeError):
                                pass
                    elif isinstance(published, dict):
                        mystery_id = published.get("mystery_id")

            # mystery_id をコンテキストに追加
            if mystery_id:
                set_pipeline_context(PipelineContext(
                    run_id=run_id, pipeline_type=run_type, mystery_id=mystery_id,
                ))

            # blog パイプラインで記事未生成の場合、ゲート失敗を検出してエラーマーク
            if run_type == "blog" and mystery_id is None:
                failure_reason, detail = _detect_gate_failure(session_state)
                logger.error(
                    "ゲート失敗: %s (stage=%s)",
                    failure_reason,
                    detail.get("failed_stage", "unknown"),
                    extra={"status": "error", **detail},
                )
                error_pipeline_run(run_id, failure_reason, error_detail=detail)
            else:
                # パイプライン正常完了サマリ
                completed_logs = pipeline_logger.get_logs()
                total_agents = len(completed_logs)
                total_duration = round(time.monotonic() - pipeline_start_time, 1)
                logger.info(
                    "パイプライン完了: %s (エージェント数=%d, 合計%.1fs)",
                    run_type, total_agents, total_duration,
                    extra={
                        "status": "completed",
                        "agent_count": total_agents,
                        "total_duration_seconds": total_duration,
                        "mystery_id": mystery_id or "",
                    },
                )
                complete_pipeline_run(run_id, mystery_id=mystery_id)

            return PipelineResult(
                run_id=run_id,
                mystery_id=mystery_id,
                logs=pipeline_logger.get_logs(),
                session_state=session_state,
            )

        except TimeoutError:
            error_pipeline_run(run_id, f"Pipeline timed out after {timeout_seconds}s", error_detail={
                "error_type": "timeout",
                "timeout_seconds": timeout_seconds,
            })
            raise
        except Exception as e:
            # 429 レートリミットエラーの場合はリトライ
            if _is_rate_limit_error(e) and attempt < _RATE_LIMIT_MAX_RETRIES:
                last_error = e
                last_error_is_rate_limit = True
                logger.warning(
                    "レートリミットエラー検出: %s", _format_exception_group(e),
                    extra={"status": "rate_limited", "attempt": attempt + 1},
                )
                continue

            # 一時的な接続エラーの場合はリトライ
            if _is_transient_connection_error(e) and attempt < _RATE_LIMIT_MAX_RETRIES:
                last_error = e
                last_error_is_rate_limit = False
                logger.warning(
                    "一時的な接続エラー検出: %s", _format_exception_group(e),
                    extra={"status": "connection_error", "attempt": attempt + 1},
                )
                continue

            error_message = _format_exception_group(e)
            logger.error(
                "Pipeline failed: %s", error_message, exc_info=True,
                extra={"status": "error", "exception_class": type(e).__name__},
            )
            error_pipeline_run(run_id, error_message, error_detail={
                "error_type": "exception",
                "exception_class": type(e).__name__,
            })
            raise

    # リトライ上限到達（通常ここには到達しない — 最後の try で raise されるため）
    assert last_error is not None
    error_message = _format_exception_group(last_error)
    error_type = "rate_limit_exhausted" if last_error_is_rate_limit else "connection_error_exhausted"
    error_pipeline_run(run_id, error_message, error_detail={
        "error_type": error_type,
        "exception_class": type(last_error).__name__,
        "retry_attempts": _RATE_LIMIT_MAX_RETRIES + 1,
    })
    raise last_error
