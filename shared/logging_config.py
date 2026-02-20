"""構造化ログ設定 — Cloud Run JSON ログ + ローカル プレーンテキスト自動切替。

Cloud Run では stdout に JSON を出力すると Cloud Logging が自動パースする。
ローカルでは従来の "%(asctime)s %(name)s [%(levelname)s] %(message)s" を維持する。

コンテキスト伝搬:
    contextvars を使い、run_id / pipeline_type / mystery_id を
    全 LogRecord に自動付与する（logging.Filter 経由）。
    asyncio.create_task() でコンテキストが自動コピーされるため、
    既存の logger.info() 呼び出しを変更する必要がない。
"""

import json
import logging
import os
import sys
from contextvars import ContextVar
from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class PipelineContext:
    """パイプライン実行コンテキスト。"""

    run_id: str = ""
    pipeline_type: str = ""  # "blog", "podcast", "curator"
    mystery_id: str = ""


_pipeline_context: ContextVar[PipelineContext] = ContextVar(
    "pipeline_context", default=PipelineContext()
)


def set_pipeline_context(ctx: PipelineContext) -> None:
    """現在の asyncio タスクにパイプラインコンテキストを設定する。"""
    _pipeline_context.set(ctx)


def get_pipeline_context() -> PipelineContext:
    """現在のパイプラインコンテキストを取得する。"""
    return _pipeline_context.get()


# logging.LogRecord の標準属性（CloudJsonFormatter で除外対象）
_STANDARD_LOG_ATTRS = frozenset({
    "name", "msg", "args", "created", "relativeCreated", "exc_info",
    "exc_text", "stack_info", "lineno", "funcName", "levelno", "levelname",
    "pathname", "filename", "module", "thread", "threadName", "process",
    "processName", "msecs", "message", "taskName",
    # StructuredLogFilter が付与するフィールド（JSON では別途処理）
    "run_id", "pipeline_type", "mystery_id",
})


class StructuredLogFilter(logging.Filter):
    """全 LogRecord にパイプラインコンテキストを自動付与する Filter。"""

    def filter(self, record: logging.LogRecord) -> bool:
        ctx = _pipeline_context.get()
        record.run_id = ctx.run_id
        record.pipeline_type = ctx.pipeline_type
        record.mystery_id = ctx.mystery_id
        return True


class CloudJsonFormatter(logging.Formatter):
    """Cloud Logging 互換 JSON フォーマッタ。

    severity キーで Cloud Logging の重大度が自動認識される。
    record.__dict__ から標準属性以外を自動抽出して JSON に含める
    （extra={} で渡した任意フィールドを構造化出力）。
    """

    # Python → Cloud Logging severity マッピング
    _SEVERITY_MAP: dict[str, str] = {
        "DEBUG": "DEBUG",
        "INFO": "INFO",
        "WARNING": "WARNING",
        "ERROR": "ERROR",
        "CRITICAL": "CRITICAL",
    }

    def format(self, record: logging.LogRecord) -> str:
        # メッセージ組み立て（% フォーマット適用）
        record.message = record.getMessage()

        payload: dict[str, Any] = {
            "severity": self._SEVERITY_MAP.get(record.levelname, "DEFAULT"),
            "message": record.message,
            "logger": record.name,
            "timestamp": self.formatTime(record, self.datefmt),
        }

        # コンテキストフィールド（空文字は除外）
        for key in ("run_id", "pipeline_type", "mystery_id"):
            value = getattr(record, key, "")
            if value:
                payload[key] = value

        # extra フィールド自動展開
        for key, value in record.__dict__.items():
            if key not in _STANDARD_LOG_ATTRS and key not in payload:
                payload[key] = value

        # 例外情報
        if record.exc_info and not record.exc_text:
            record.exc_text = self.formatException(record.exc_info)
        if record.exc_text:
            payload["exception"] = record.exc_text

        return json.dumps(payload, ensure_ascii=False, default=str)


class PlainTextFormatter(logging.Formatter):
    """ローカル用プレーンテキストフォーマッタ（既存互換）。

    コンテキストフィールド（run_id 等）がある場合は末尾に付与する。
    """

    def __init__(self) -> None:
        super().__init__("%(asctime)s %(name)s [%(levelname)s] %(message)s")

    def format(self, record: logging.LogRecord) -> str:
        base = super().format(record)

        # コンテキスト情報を末尾に付与
        ctx_parts = []
        for key in ("run_id", "pipeline_type", "mystery_id"):
            value = getattr(record, key, "")
            if value:
                ctx_parts.append(f"{key}={value}")
        if ctx_parts:
            return f"{base} [{', '.join(ctx_parts)}]"
        return base


def _is_cloud_run() -> bool:
    """Cloud Run 環境かどうかを判定する。"""
    return bool(os.environ.get("K_SERVICE"))


def setup_logging(*, force: bool = False) -> None:
    """root logger を初期化する。

    Cloud Run（K_SERVICE 環境変数あり）では JSON フォーマッタ、
    ローカルではプレーンテキストフォーマッタを使用する。

    Args:
        force: True の場合、既存ハンドラを削除して再初期化する。
    """
    root = logging.getLogger()

    # 既に初期化済みの場合はスキップ（force=True でない限り）
    if root.handlers and not force:
        return

    # 既存ハンドラを削除
    for handler in root.handlers[:]:
        root.removeHandler(handler)

    # ハンドラ設定
    handler = logging.StreamHandler(sys.stdout)

    if _is_cloud_run():
        handler.setFormatter(CloudJsonFormatter())
    else:
        handler.setFormatter(PlainTextFormatter())

    # 全 LogRecord にコンテキストを付与する Filter
    handler.addFilter(StructuredLogFilter())

    root.addHandler(handler)
    root.setLevel(logging.INFO)
