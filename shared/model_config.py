"""LLM モデル設定ユーティリティ。

全エージェントで使用する Gemini モデルアダプタを一元管理する。
HTTP 429 (RESOURCE_EXHAUSTED) エラーに対する指数バックオフ付きリトライを設定し、
並列エージェント実行時のレート制限エラーを自動的に回復する。

Storyteller 用のストーリーテラーモデルは STORYTELLER_MODELS レジストリで管理し、
Gemini 以外のモデル（Claude, GPT, Llama, DeepSeek, Mistral）は
OpenRouter 経由で LiteLLM アダプタを使用する。

ADK はデフォルトで retry_options=None（リトライ0回）のため、
明示的に HttpRetryOptions を設定しないと 429 で即クラッシュする。
参照: https://google.github.io/adk-docs/agents/models/google-gemini/
"""

import logging

from google.adk.models.google_llm import Gemini
from google.genai.types import HttpRetryOptions

logger = logging.getLogger(__name__)

# モデル名定数
MODEL_PRO = "gemini-3-pro-preview"
MODEL_FLASH = "gemini-2.5-flash"

# === 日本語訳 ===
# ストーリーテラーモデルレジストリ。
# Storyteller エージェントが使用する LLM を「語り部（ストーリーテラー）」として選択可能にする。
# - native_gemini: 既存の Gemini Pro（Vertex AI）を使用
# - litellm: OpenRouter 経由で各プロバイダーのモデルにアクセス（API キー: OPENROUTER_API_KEY 1つで一元管理）
# === End 日本語訳 ===
STORYTELLER_MODELS: dict[str, dict] = {
    "claude": {
        "model_id": "openrouter/anthropic/claude-sonnet-4.5",
        "provider": "litellm",
        "display_name": "Claude",
    },
    "gemini": {
        "model_id": MODEL_PRO,
        "provider": "native_gemini",
        "display_name": "Gemini",
    },
    "gpt": {
        "model_id": "openrouter/openai/gpt-4o",
        "provider": "litellm",
        "display_name": "GPT",
    },
    "llama": {
        "model_id": "openrouter/meta-llama/llama-4-maverick",
        "provider": "litellm",
        "display_name": "Llama",
    },
    "deepseek": {
        "model_id": "openrouter/deepseek/deepseek-chat",
        "provider": "litellm",
        "display_name": "DeepSeek",
    },
    "mistral": {
        "model_id": "openrouter/mistralai/mistral-large-2512",
        "provider": "litellm",
        "display_name": "Mistral",
    },
}

DEFAULT_STORYTELLER = "claude"

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


def create_storyteller_model(storyteller: str = DEFAULT_STORYTELLER):
    """ストーリーテラー名から Storyteller 用モデルアダプタを生成する。

    Args:
        storyteller: ストーリーテラー名（STORYTELLER_MODELS のキー）

    Returns:
        ADK モデルアダプタ（Gemini または LiteLlm インスタンス）

    Raises:
        ValueError: 不正なストーリーテラー名が指定された場合
    """
    if storyteller not in STORYTELLER_MODELS:
        valid = ", ".join(STORYTELLER_MODELS.keys())
        raise ValueError(f"Unknown storyteller '{storyteller}'. Valid storytellers: {valid}")

    config = STORYTELLER_MODELS[storyteller]
    provider = config["provider"]

    if provider == "native_gemini":
        return create_pro_model()

    # OpenRouter 経由（LiteLLM アダプタ）
    from google.adk.models.lite_llm import LiteLlm

    return LiteLlm(model=config["model_id"])
