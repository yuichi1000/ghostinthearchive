"""全エージェント横断トークン使用量追跡。

各 LlmAgent の after_model_callback で呼び出し、セッション状態にトークン使用量を蓄積する。
パイプライン完了後に orchestrator が集約して pipeline_runs に永続化する。

既存の search_metrics パターン（セッション状態 → 抽出 → Firestore）を踏襲する。
"""

import logging
from datetime import datetime, timezone

from shared.state_keys import AGENT_TOKEN_LOG

logger = logging.getLogger(__name__)


def track_tokens(agent_name: str, callback_context, llm_response) -> None:
    """トークン使用量をセッション状態に追記する。

    after_model_callback 内から呼び出す低レベル関数。
    usage_metadata がない場合は 0 でフォールバックする。

    Args:
        agent_name: エージェント識別名（例: "librarian_us_archives", "scholar_en"）
        callback_context: ADK CallbackContext（state アクセス用）
        llm_response: ADK LlmResponse（usage_metadata アクセス用）
    """
    usage = llm_response.usage_metadata if llm_response else None
    prompt_tokens = getattr(usage, "prompt_token_count", 0) or 0
    output_tokens = getattr(usage, "candidates_token_count", 0) or 0

    entry = {
        "agent": agent_name,
        "prompt_tokens": prompt_tokens,
        "output_tokens": output_tokens,
    }

    log = callback_context.state.get(AGENT_TOKEN_LOG)
    if not isinstance(log, list):
        log = []
    log.append(entry)
    callback_context.state[AGENT_TOKEN_LOG] = log


def create_token_tracking_callback(agent_name: str):
    """after_model_callback ファクトリ。agent_name をクロージャでバインドする。

    Args:
        agent_name: エージェント識別名

    Returns:
        after_model_callback 関数（None を返す = レスポンスを変更しない）
    """
    def _callback(callback_context, llm_response):
        track_tokens(agent_name, callback_context, llm_response)
        return None
    return _callback


def extract_token_metrics(session_state: dict) -> dict | None:
    """_agent_token_log を集約して by_agent + totals を返す。

    Args:
        session_state: セッション状態辞書

    Returns:
        集約結果 dict、またはログがない場合は None
    """
    log = session_state.get(AGENT_TOKEN_LOG)
    if not log or not isinstance(log, list):
        return None

    by_agent: dict[str, dict] = {}
    for entry in log:
        if not isinstance(entry, dict):
            continue
        agent = entry.get("agent", "unknown")
        prompt = entry.get("prompt_tokens", 0)
        output = entry.get("output_tokens", 0)

        if agent not in by_agent:
            by_agent[agent] = {"calls": 0, "prompt_tokens": 0, "output_tokens": 0}
        by_agent[agent]["calls"] += 1
        by_agent[agent]["prompt_tokens"] += prompt
        by_agent[agent]["output_tokens"] += output

    if not by_agent:
        return None

    totals = {
        "calls": sum(a["calls"] for a in by_agent.values()),
        "prompt_tokens": sum(a["prompt_tokens"] for a in by_agent.values()),
        "output_tokens": sum(a["output_tokens"] for a in by_agent.values()),
    }

    return {"by_agent": by_agent, "totals": totals}


def save_token_metrics(run_id: str | None, metrics: dict | None) -> None:
    """token_metrics を pipeline_runs ドキュメントに保存する（非ブロッキング）。

    Args:
        run_id: パイプライン実行ドキュメントの ID
        metrics: extract_token_metrics() の戻り値。None なら何もしない。
    """
    if not run_id or metrics is None:
        return
    try:
        from shared.firestore import get_firestore_client

        db = get_firestore_client()
        db.collection("pipeline_runs").document(run_id).update({
            "token_metrics": metrics,
            "updated_at": datetime.now(timezone.utc),
        })
        logger.info(
            "トークンメトリクス保存: %s (エージェント数=%d, 総呼出=%d, 総入力=%d, 総出力=%d)",
            run_id,
            len(metrics.get("by_agent", {})),
            metrics["totals"]["calls"],
            metrics["totals"]["prompt_tokens"],
            metrics["totals"]["output_tokens"],
        )
    except Exception:
        # メトリクス保存失敗はパイプラインをブロックしない
        logger.warning("Failed to save token metrics to Firestore", exc_info=True)
