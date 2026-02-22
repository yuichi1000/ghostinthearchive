"""LLM モデル設定ユーティリティ。

全エージェントで使用する Gemini / Claude モデルアダプタを一元管理する。
HTTP 429 (RESOURCE_EXHAUSTED) エラーに対する指数バックオフ付きリトライを設定し、
並列エージェント実行時のレート制限エラーを自動的に回復する。

ADK はデフォルトで retry_options=None（リトライ0回）のため、
明示的に HttpRetryOptions を設定しないと 429 で即クラッシュする。
参照: https://google.github.io/adk-docs/agents/models/google-gemini/
"""

import logging

from google.adk.models.google_llm import Gemini
from google.genai.types import HttpRetryOptions

logger = logging.getLogger(__name__)

# === 日本語訳 ===
# Claude (Vertex AI) のリトライ回数上限。
# Anthropic SDK のデフォルトは 2回だが、Vertex AI の 429 レート制限に対応するため
# 10回に引き上げる。指数バックオフは SDK が自動適用する。
# === End 日本語訳 ===
_CLAUDE_MAX_RETRIES = 10

# _ClaudeWithRetry クラスの参照（try ブロック外に sentinel 定義）
# anthropic パッケージが未インストールの場合は None のまま
_claude_with_retry_cls = None

# Claude モデルの LLMRegistry 登録（Vertex AI 経由）
# anthropic パッケージが未インストールの場合はスキップ（テスト環境等）
try:
    import os
    from functools import cached_property

    from anthropic import AsyncAnthropicVertex
    from google.adk.models.anthropic_llm import Claude
    from google.adk.models.registry import LLMRegistry

    class _ClaudeWithRetry(Claude):
        """Vertex AI 429 レート制限に対応するリトライ強化版 Claude。

        ADK の Claude クラスは AsyncAnthropicVertex に max_retries を渡さないため、
        Anthropic SDK のデフォルト（2回）しかリトライされない。
        このサブクラスで max_retries=_CLAUDE_MAX_RETRIES を明示的に設定する。
        """

        @cached_property
        def _anthropic_client(self) -> AsyncAnthropicVertex:
            if (
                "GOOGLE_CLOUD_PROJECT" not in os.environ
                or "GOOGLE_CLOUD_LOCATION" not in os.environ
            ):
                raise ValueError(
                    "GOOGLE_CLOUD_PROJECT and GOOGLE_CLOUD_LOCATION "
                    "environment variables must be set."
                )
            try:
                from google.adk.utils._google_client_headers import (
                    get_tracking_headers,
                )

                headers = get_tracking_headers()
            except ImportError:
                headers = {}
            logger.info(
                "AsyncAnthropicVertex 初期化: max_retries=%d",
                _CLAUDE_MAX_RETRIES,
            )
            return AsyncAnthropicVertex(
                project_id=os.environ["GOOGLE_CLOUD_PROJECT"],
                region=os.environ["GOOGLE_CLOUD_LOCATION"],
                default_headers=headers,
                max_retries=_CLAUDE_MAX_RETRIES,
            )

    _claude_with_retry_cls = _ClaudeWithRetry
    LLMRegistry.register(_ClaudeWithRetry)
    # ADK が自動登録した Claude の LRU キャッシュを無効化し、
    # _ClaudeWithRetry が resolve() で返されるようにする
    LLMRegistry.resolve.cache_clear()
except ImportError:
    pass

# モデル名定数
MODEL_PRO = "gemini-3-pro-preview"
MODEL_FLASH = "gemini-2.5-flash"
MODEL_CLAUDE_SONNET = "claude-sonnet-4-5@20250929"

# === 日本語訳 ===
# Pro モデル用リトライ設定（レート制限が厳しい）
# - 最大7回（初回 + リトライ6回）
# - 初回リトライまで2秒（並列実行の波が収まるまで待つ）
# - 最大120秒（並列実行の長い競合に対応）
# - 指数バックオフ: 2s → 4s → 8s → 16s → 32s → 64s
# - ジッター1.0で並列リクエストの衝突を分散
# === End 日本語訳 ===
_PRO_RETRY_OPTIONS = HttpRetryOptions(
    attempts=7,
    initial_delay=2.0,
    max_delay=120.0,
    exp_base=2.0,
    jitter=1.0,
)

# === 日本語訳 ===
# Flash モデル用リトライ設定（レート制限が緩やか）
# - 最大5回（初回 + リトライ4回）
# - 初回リトライまで1秒
# - 最大60秒
# - 指数バックオフ: 1s → 2s → 4s → 8s
# - ジッター1.0で並列リクエストの衝突を分散
# === End 日本語訳 ===
_FLASH_RETRY_OPTIONS = HttpRetryOptions(
    attempts=5,
    initial_delay=1.0,
    max_delay=60.0,
    exp_base=2.0,
    jitter=1.0,
)


def create_pro_model() -> Gemini:
    """gemini-3-pro-preview のリトライ付きモデルアダプタを生成する。"""
    return Gemini(model=MODEL_PRO, retry_options=_PRO_RETRY_OPTIONS)


def create_flash_model() -> Gemini:
    """gemini-2.5-flash のリトライ付きモデルアダプタを生成する。"""
    return Gemini(model=MODEL_FLASH, retry_options=_FLASH_RETRY_OPTIONS)


def create_claude_sonnet_model():
    """Claude Sonnet 4.5 (Vertex AI) のモデルを返す。

    _ClaudeWithRetry が利用可能な場合はインスタンスを直接返す。
    LlmAgent(model=BaseLlm_instance) は LLMRegistry.resolve() を完全にバイパスするため、
    ADK 自動登録 Claude の LRU キャッシュ問題を根本解決する。
    利用不可能な場合はモデル文字列にフォールバック。
    """
    if _claude_with_retry_cls is not None:
        return _claude_with_retry_cls(model=MODEL_CLAUDE_SONNET)
    return MODEL_CLAUDE_SONNET
