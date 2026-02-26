"""エラー系カバレッジ強化テスト。

各ツール・ゲートの異常系パスを検証し、
エラー時の振る舞い（フォールバック・ログ出力・エラーJSON）が正しいことを確認する。
"""

import json
from unittest.mock import MagicMock, patch

from mystery_agents.agents.pipeline_gate import make_scholar_gate
from mystery_agents.tools.debate_tools import append_to_whiteboard
from mystery_agents.tools.prompt_safety import _rewrite_safe_prompt
from mystery_agents.tools.librarian_tools import search_archives
from mystery_agents.tools.publisher_tools import publish_mystery
from shared.http_retry import create_retry_session
from tests.fakes import make_tool_context


class TestPublishMysteryFirestoreTimeout:
    """publisher_tools: Firestore タイムアウト時のエラーハンドリング。"""

    @patch("mystery_agents.tools.publisher_tools.get_storage_bucket")
    @patch("mystery_agents.tools.publisher_tools.get_firestore_client")
    def test_firestore_timeout_returns_error_json(self, mock_get_db, mock_get_bucket):
        """Firestore タイムアウト時にエラー JSON を返す。"""
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        mock_get_bucket.return_value = MagicMock()

        # Firestore の set() がタイムアウト例外を投げる
        mock_db.collection.return_value.document.return_value.set.side_effect = (
            TimeoutError("Firestore request timed out")
        )

        mystery_json = json.dumps({
            "classification": "OCC",
            "country_code": "US",
            "region_code": "BOS",
            "title": "Test",
            "summary": "Test summary",
            "discrepancy_detected": "Test",
            "discrepancy_type": "event_outcome",
            "evidence_a": {"source_type": "newspaper", "source_language": "en",
                           "source_title": "T", "source_date": "1842-01-01",
                           "source_url": "https://example.com", "relevant_excerpt": "...",
                           "location_context": "Boston"},
            "evidence_b": {"source_type": "newspaper", "source_language": "es",
                           "source_title": "T", "source_date": "1842-02-01",
                           "source_url": "https://example.com/es", "relevant_excerpt": "...",
                           "location_context": "Havana"},
            "hypothesis": "Test",
            "alternative_hypotheses": [],
            "confidence_level": "medium",
            "historical_context": {"time_period": "19th", "geographic_scope": ["Boston"],
                                   "relevant_events": [], "key_figures": [],
                                   "political_climate": "Stable"},
            "research_questions": [],
            "story_hooks": [],
            "narrative_content": "# Test\nContent",
        })

        ctx = make_tool_context({})
        result = publish_mystery(mystery_json, "", ctx)
        result_data = json.loads(result)

        assert result_data["status"] == "error"
        assert "timed out" in result_data["error"].lower() or "timeout" in result_data["error"].lower()


class TestRewriteSafePromptEmptyResponse:
    """illustrator_tools: LLM 空レスポンスで sanitize_prompt フォールバック。"""

    @patch("mystery_agents.tools.illustrator_tools._get_client")
    def test_empty_llm_response_falls_back_to_sanitize(self, mock_get_client):
        """LLM が空レスポンスを返した場合 _sanitize_prompt にフォールバック。"""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        mock_response = MagicMock()
        mock_response.text = ""
        mock_client.models.generate_content.return_value = mock_response

        result = _rewrite_safe_prompt("A ghost ship sailing", "auto")

        # 空レスポンスなので _sanitize_prompt にフォールバック
        assert "ghost" not in result
        assert "ethereal figure" in result


class TestSearchArchivesAllSourcesFail:
    """librarian_tools: 全ソース例外時に空結果 + エラー情報。"""

    @patch("mystery_agents.tools.librarian_tools.validate_documents")
    @patch("mystery_agents.tools.librarian_tools.get_all_sources")
    def test_all_sources_fail_returns_empty_with_errors(self, mock_get_all, mock_validate):
        """全ソースが例外を投げた場合、空結果とエラー情報が返される。"""
        class FailSource:
            source_key = "fail1"
            source_name = "Fail Source 1"
            supports_language_filter = False
            supported_languages = {"en"}
            def search(self, **kwargs):
                raise ConnectionError("Connection refused")

        class FailSource2:
            source_key = "fail2"
            source_name = "Fail Source 2"
            supports_language_filter = False
            supported_languages = {"en"}
            def search(self, **kwargs):
                raise TimeoutError("Request timeout")

        mock_get_all.return_value = {
            "fail1": FailSource(),
            "fail2": FailSource2(),
        }
        mock_validate.return_value = type("Summary", (), {
            "total_checked": 0, "reachable": 0, "unreachable": 0,
            "removed_urls": [], "duration_ms": 0, "verified_documents": [],
        })()

        result_json = search_archives(
            keywords="ghost", sources="fail1,fail2", language="en"
        )
        result = json.loads(result_json)

        assert result["total_documents"] == 0
        assert result["errors"] is not None
        assert "fail1" in result["errors"]
        assert "fail2" in result["errors"]


class TestPipelineGateNoStateKeys:
    """pipeline_gate: 状態キー未設定でスキップが正常動作する。"""

    def test_scholar_gate_skips_when_no_state_keys(self):
        """selected_languages も collected_documents_* もない場合、スキップ Content を返す。"""
        gate = make_scholar_gate()

        mock_ctx = MagicMock()
        mock_ctx.state = {}  # 状態キー一切なし

        # log_pipeline_failure をモック化（Firestore 不要）
        with patch("mystery_agents.agents.pipeline_gate.log_pipeline_failure", create=True):
            result = gate(mock_ctx)

        # None でない → スキップが発生
        assert result is not None


class TestAppendToWhiteboardMissingKey:
    """debate_tools: whiteboard キー未設定でデフォルト空文字列処理。"""

    def test_missing_whiteboard_key_initializes_empty(self):
        """debate_whiteboard キーが未設定でも正常動作する。"""
        ctx = MagicMock()
        ctx.state = {}  # debate_whiteboard キーなし

        result = append_to_whiteboard("English", 1, "First contribution", ctx)

        assert "### [Round 1] English Perspective" in ctx.state["debate_whiteboard"]
        assert "First contribution" in ctx.state["debate_whiteboard"]
        assert "English" in result


class TestDefaultRetriesCount:
    """http_retry: デフォルトリトライ回数=3 の検証。"""

    def test_default_retries_count(self):
        """create_retry_session のデフォルトリトライ回数は 3。"""
        session = create_retry_session()

        # HTTPAdapter から Retry 設定を取得
        adapter = session.get_adapter("https://")
        assert adapter.max_retries.total == 3

    def test_custom_retries_count(self):
        """カスタムリトライ回数が正しく設定される。"""
        session = create_retry_session(retries=5)

        adapter = session.get_adapter("https://")
        assert adapter.max_retries.total == 5
