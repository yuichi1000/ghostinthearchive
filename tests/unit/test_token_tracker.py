"""Unit tests for shared/token_tracker.py — 全エージェント横断トークン使用量追跡。"""

from unittest.mock import MagicMock, patch

from shared.state_keys import AGENT_TOKEN_LOG
from shared.token_tracker import (
    create_token_tracking_callback,
    extract_token_metrics,
    save_token_metrics,
    track_tokens,
)


# ---------------------------------------------------------------------------
# ヘルパー
# ---------------------------------------------------------------------------

def _make_callback_context(state: dict | None = None):
    """テスト用 CallbackContext モック。"""
    ctx = MagicMock()
    ctx.state = state if state is not None else {}
    return ctx


def _make_llm_response(*, prompt_tokens: int | None = None, output_tokens: int | None = None):
    """テスト用 LlmResponse モック。"""
    resp = MagicMock()
    if prompt_tokens is not None or output_tokens is not None:
        resp.usage_metadata = MagicMock()
        resp.usage_metadata.prompt_token_count = prompt_tokens
        resp.usage_metadata.candidates_token_count = output_tokens
    else:
        resp.usage_metadata = None
    return resp


# ---------------------------------------------------------------------------
# track_tokens
# ---------------------------------------------------------------------------

class TestTrackTokens:
    """track_tokens() のテスト。"""

    def test_appends_entry_to_empty_state(self):
        """空のセッション状態に最初のエントリを追記する。"""
        ctx = _make_callback_context()
        resp = _make_llm_response(prompt_tokens=100, output_tokens=50)

        track_tokens("scholar_en", ctx, resp)

        log = ctx.state[AGENT_TOKEN_LOG]
        assert len(log) == 1
        assert log[0] == {
            "agent": "scholar_en",
            "prompt_tokens": 100,
            "output_tokens": 50,
        }

    def test_appends_to_existing_log(self):
        """既存のログリストに追記する。"""
        existing = [{"agent": "librarian_us", "prompt_tokens": 200, "output_tokens": 100}]
        ctx = _make_callback_context({AGENT_TOKEN_LOG: existing})
        resp = _make_llm_response(prompt_tokens=300, output_tokens=150)

        track_tokens("scholar_de", ctx, resp)

        log = ctx.state[AGENT_TOKEN_LOG]
        assert len(log) == 2
        assert log[1]["agent"] == "scholar_de"

    def test_no_usage_metadata_falls_back_to_zero(self):
        """usage_metadata が None の場合、トークン数は 0 にフォールバックする。"""
        ctx = _make_callback_context()
        resp = _make_llm_response()  # usage_metadata = None

        track_tokens("illustrator", ctx, resp)

        entry = ctx.state[AGENT_TOKEN_LOG][0]
        assert entry["prompt_tokens"] == 0
        assert entry["output_tokens"] == 0

    def test_none_llm_response_falls_back_to_zero(self):
        """llm_response 自体が None の場合も安全に処理する。"""
        ctx = _make_callback_context()

        track_tokens("translator_ja", ctx, None)

        entry = ctx.state[AGENT_TOKEN_LOG][0]
        assert entry["prompt_tokens"] == 0
        assert entry["output_tokens"] == 0

    def test_non_list_state_reinitializes(self):
        """state に list でない値が入っている場合、新しいリストで上書きする。"""
        ctx = _make_callback_context({AGENT_TOKEN_LOG: "corrupted"})
        resp = _make_llm_response(prompt_tokens=50, output_tokens=25)

        track_tokens("storyteller", ctx, resp)

        log = ctx.state[AGENT_TOKEN_LOG]
        assert isinstance(log, list)
        assert len(log) == 1


# ---------------------------------------------------------------------------
# create_token_tracking_callback
# ---------------------------------------------------------------------------

class TestCreateTokenTrackingCallback:
    """create_token_tracking_callback() のテスト。"""

    def test_binds_agent_name_and_returns_none(self):
        """agent_name をクロージャでバインドし、None を返す。"""
        callback = create_token_tracking_callback("librarian_europeana")
        ctx = _make_callback_context()
        resp = _make_llm_response(prompt_tokens=500, output_tokens=250)

        result = callback(ctx, resp)

        assert result is None
        assert ctx.state[AGENT_TOKEN_LOG][0]["agent"] == "librarian_europeana"

    def test_different_agent_names_produce_independent_callbacks(self):
        """異なる agent_name のコールバックは独立して動作する。"""
        cb1 = create_token_tracking_callback("scholar_en")
        cb2 = create_token_tracking_callback("scholar_de")
        ctx = _make_callback_context()

        cb1(ctx, _make_llm_response(prompt_tokens=100, output_tokens=50))
        cb2(ctx, _make_llm_response(prompt_tokens=200, output_tokens=100))

        agents = [e["agent"] for e in ctx.state[AGENT_TOKEN_LOG]]
        assert agents == ["scholar_en", "scholar_de"]


# ---------------------------------------------------------------------------
# extract_token_metrics
# ---------------------------------------------------------------------------

class TestExtractTokenMetrics:
    """extract_token_metrics() のテスト。"""

    def test_empty_state_returns_none(self):
        """ログがない場合は None を返す。"""
        assert extract_token_metrics({}) is None

    def test_empty_list_returns_none(self):
        """空リストの場合は None を返す。"""
        assert extract_token_metrics({AGENT_TOKEN_LOG: []}) is None

    def test_single_agent_single_call(self):
        """単一エージェント・単一呼出の集約。"""
        state = {
            AGENT_TOKEN_LOG: [
                {"agent": "storyteller", "prompt_tokens": 1000, "output_tokens": 500},
            ]
        }
        metrics = extract_token_metrics(state)

        assert metrics["by_agent"]["storyteller"] == {
            "calls": 1,
            "prompt_tokens": 1000,
            "output_tokens": 500,
        }
        assert metrics["totals"] == {
            "calls": 1,
            "prompt_tokens": 1000,
            "output_tokens": 500,
        }

    def test_multiple_agents(self):
        """複数エージェントの集約。"""
        state = {
            AGENT_TOKEN_LOG: [
                {"agent": "scholar_en", "prompt_tokens": 500, "output_tokens": 300},
                {"agent": "scholar_de", "prompt_tokens": 600, "output_tokens": 400},
            ]
        }
        metrics = extract_token_metrics(state)

        assert len(metrics["by_agent"]) == 2
        assert metrics["totals"]["calls"] == 2
        assert metrics["totals"]["prompt_tokens"] == 1100
        assert metrics["totals"]["output_tokens"] == 700

    def test_same_agent_multiple_calls_aggregated(self):
        """同一エージェントの複数呼出が集約される。"""
        state = {
            AGENT_TOKEN_LOG: [
                {"agent": "armchair_polymath", "prompt_tokens": 1000, "output_tokens": 500},
                {"agent": "armchair_polymath", "prompt_tokens": 2000, "output_tokens": 1000},
                {"agent": "armchair_polymath", "prompt_tokens": 3000, "output_tokens": 1500},
            ]
        }
        metrics = extract_token_metrics(state)

        polymath = metrics["by_agent"]["armchair_polymath"]
        assert polymath["calls"] == 3
        assert polymath["prompt_tokens"] == 6000
        assert polymath["output_tokens"] == 3000

    def test_non_dict_entries_skipped(self):
        """dict でないエントリは無視される。"""
        state = {
            AGENT_TOKEN_LOG: [
                "invalid",
                {"agent": "storyteller", "prompt_tokens": 100, "output_tokens": 50},
                42,
            ]
        }
        metrics = extract_token_metrics(state)

        assert metrics["totals"]["calls"] == 1

    def test_non_list_log_returns_none(self):
        """ログが list でない場合は None を返す。"""
        assert extract_token_metrics({AGENT_TOKEN_LOG: "not a list"}) is None


# ---------------------------------------------------------------------------
# save_token_metrics
# ---------------------------------------------------------------------------

class TestSaveTokenMetrics:
    """save_token_metrics() のテスト。"""

    @patch("shared.firestore.get_firestore_client")
    def test_saves_to_firestore(self, mock_get_client):
        """Firestore に token_metrics を保存する。"""
        mock_db = MagicMock()
        mock_get_client.return_value = mock_db

        metrics = {
            "by_agent": {"storyteller": {"calls": 1, "prompt_tokens": 100, "output_tokens": 50}},
            "totals": {"calls": 1, "prompt_tokens": 100, "output_tokens": 50},
        }

        save_token_metrics("run_123", metrics)

        mock_db.collection.assert_called_once_with("pipeline_runs")
        mock_db.collection().document.assert_called_once_with("run_123")
        update_call = mock_db.collection().document().update
        update_call.assert_called_once()
        saved_data = update_call.call_args[0][0]
        assert saved_data["token_metrics"] == metrics
        assert "updated_at" in saved_data

    def test_none_run_id_skips(self):
        """run_id が None の場合は何もしない。"""
        # Firestore import がないことを確認（例外が出ない）
        save_token_metrics(None, {"totals": {}})

    def test_none_metrics_skips(self):
        """metrics が None の場合は何もしない。"""
        save_token_metrics("run_123", None)

    @patch("shared.firestore.get_firestore_client", side_effect=Exception("connection error"))
    def test_firestore_error_does_not_block(self, mock_get_client):
        """Firestore エラーはパイプラインをブロックしない。"""
        metrics = {
            "by_agent": {},
            "totals": {"calls": 0, "prompt_tokens": 0, "output_tokens": 0},
        }
        # 例外が伝播しないことを確認
        save_token_metrics("run_456", metrics)
