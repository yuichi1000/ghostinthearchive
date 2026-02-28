"""Unit tests for Storyteller agent instruction, callbacks, and context window fix."""

import logging
from unittest.mock import MagicMock

from mystery_agents.agents.storyteller import (
    STORYTELLER_INSTRUCTION,
    _estimate_tokens,
    _has_function_parts,
    _is_leaked_content,
    _storyteller_after_model,
    _storyteller_before_model,
)
from shared.state_keys import STORYTELLER_LLM_METADATA


def _make_llm_response(
    *,
    text: str | None = None,
    finish_reason=None,
    error_code: str | None = None,
    error_message: str | None = None,
    prompt_tokens: int | None = None,
    output_tokens: int | None = None,
):
    """テスト用の LlmResponse モックを生成する。"""
    response = MagicMock()
    response.error_code = error_code
    response.error_message = error_message
    response.finish_reason = finish_reason

    if text:
        part = MagicMock()
        part.text = text
        response.content = MagicMock()
        response.content.parts = [part]
    else:
        response.content = None

    if prompt_tokens is not None or output_tokens is not None:
        response.usage_metadata = MagicMock()
        response.usage_metadata.prompt_token_count = prompt_tokens
        response.usage_metadata.candidates_token_count = output_tokens
    else:
        response.usage_metadata = None

    return response


def _make_callback_context():
    """テスト用の CallbackContext モックを生成する。"""
    ctx = MagicMock()
    ctx.state = {}
    return ctx


class TestStorytellerAfterModel:
    """_storyteller_after_model のテスト"""

    def test_normal_response_passes_through(self):
        """正常応答（テキストあり + エラーなし）は None を返し、メタデータを記録する。"""
        ctx = _make_callback_context()
        response = _make_llm_response(text="A compelling narrative...")

        result = _storyteller_after_model(ctx, response)

        assert result is None
        metadata = ctx.state[STORYTELLER_LLM_METADATA]
        assert "storyteller" in metadata
        assert "display_name" in metadata

    def test_actual_model_recorded_from_response(self):
        """actual_model が llm_response.model_version から記録される。"""
        ctx = _make_callback_context()
        response = _make_llm_response(text="A compelling narrative...")
        response.model_version = "claude-sonnet-4-5-20250929"

        _storyteller_after_model(ctx, response)

        metadata = ctx.state[STORYTELLER_LLM_METADATA]
        assert metadata["actual_model"] == "claude-sonnet-4-5-20250929"

    def test_actual_model_none_when_not_available(self):
        """model_version が None の場合、actual_model も None。"""
        ctx = _make_callback_context()
        response = _make_llm_response(text="A compelling narrative...")
        response.model_version = None

        _storyteller_after_model(ctx, response)

        metadata = ctx.state[STORYTELLER_LLM_METADATA]
        assert metadata["actual_model"] is None

    def test_actual_model_in_error_metadata(self):
        """異常応答でも actual_model が記録される。"""
        ctx = _make_callback_context()
        response = _make_llm_response(
            error_code="SAFETY_FILTER",
            prompt_tokens=3000,
        )
        response.model_version = "deepseek/deepseek-r1"

        _storyteller_after_model(ctx, response)

        metadata = ctx.state[STORYTELLER_LLM_METADATA]
        assert metadata["actual_model"] == "deepseek/deepseek-r1"

    def test_empty_response_records_metadata(self, caplog):
        """空レスポンスでメタデータがセッション状態に記録される。"""
        ctx = _make_callback_context()
        response = _make_llm_response(
            finish_reason="STOP",
            prompt_tokens=5000,
            output_tokens=0,
        )

        with caplog.at_level(logging.ERROR, logger="mystery_agents.agents.storyteller"):
            result = _storyteller_after_model(ctx, response)

        assert result is None
        metadata = ctx.state[STORYTELLER_LLM_METADATA]
        assert metadata["has_content"] is False
        assert metadata["prompt_tokens"] == 5000
        assert metadata["output_tokens"] == 0
        assert metadata["error_code"] is None

        # ERROR レベルでログ出力される
        error_records = [
            r for r in caplog.records if r.levelno == logging.ERROR
        ]
        assert len(error_records) == 1
        assert "Storyteller 異常応答" in error_records[0].message

    def test_safety_filter_records_metadata(self, caplog):
        """安全フィルタ応答でメタデータが記録される。"""
        ctx = _make_callback_context()
        response = _make_llm_response(
            text="I cannot generate this content",
            finish_reason="SAFETY",
            error_code="SAFETY_FILTER",
            error_message="Content blocked by safety filter",
            prompt_tokens=3000,
            output_tokens=10,
        )

        with caplog.at_level(logging.ERROR, logger="mystery_agents.agents.storyteller"):
            result = _storyteller_after_model(ctx, response)

        assert result is None
        metadata = ctx.state[STORYTELLER_LLM_METADATA]
        assert metadata["error_code"] == "SAFETY_FILTER"
        assert metadata["error_message"] == "Content blocked by safety filter"
        assert metadata["finish_reason"] == "SAFETY"
        assert metadata["prompt_tokens"] == 3000

    def test_no_usage_metadata_handled(self):
        """usage_metadata なしでもエラーにならない。"""
        ctx = _make_callback_context()
        response = _make_llm_response(error_code="UNKNOWN_ERROR")

        result = _storyteller_after_model(ctx, response)

        assert result is None
        metadata = ctx.state[STORYTELLER_LLM_METADATA]
        assert metadata["prompt_tokens"] is None
        assert metadata["output_tokens"] is None


class TestStorytellerInstruction:
    def test_no_sources_in_output_template(self):
        """Storyteller should not include 'Sources: [引用元リスト]' in the output template."""
        assert "Sources: [引用元リスト]" not in STORYTELLER_INSTRUCTION

    def test_explicit_no_sources_directive(self):
        """Storyteller should have an explicit directive to not include Sources."""
        assert "Do NOT include a Sources (citation list) in the output" in STORYTELLER_INSTRUCTION

    def test_has_epistemic_honesty_guidelines(self):
        assert "Epistemic Honesty" in STORYTELLER_INSTRUCTION

    def test_not_found_not_equals_not_exist(self):
        assert "Does not exist" in STORYTELLER_INSTRUCTION

    def test_api_absence_not_historical_absence(self):
        assert "API absence" in STORYTELLER_INSTRUCTION

    def test_has_hook_technique(self):
        """Introduction にフック技法（provocative question）の指示がある。"""
        assert "provocative question" in STORYTELLER_INSTRUCTION.lower()
        assert "Do NOT open with a dry academic lead-in" in STORYTELLER_INSTRUCTION

    def test_has_sensory_writing_guidelines(self):
        """Sensory Writing セクションが存在し、blockquote 除外ルールを含む。"""
        assert "## Sensory Writing" in STORYTELLER_INSTRUCTION
        assert "regular paragraphs only" in STORYTELLER_INSTRUCTION

    def test_has_rhetoric_of_absence(self):
        """Rhetoric of Absence セクションが存在する。"""
        assert "## Rhetoric of Absence" in STORYTELLER_INSTRUCTION
        assert "gaps, silences, and omissions" in STORYTELLER_INSTRUCTION

    def test_has_abstract_concrete_alternation(self):
        """抽象⇄具体の交互配置指示が Sensory Writing 内にある。"""
        assert "abstract analysis" in STORYTELLER_INSTRUCTION
        assert "concrete sensory details" in STORYTELLER_INSTRUCTION
        assert "rhythm and contrast" in STORYTELLER_INSTRUCTION

    def test_instruction_has_single_mystery_report_placeholder(self):
        """{mystery_report} プレースホルダーが instruction 内に1回のみ出現する。"""
        count = STORYTELLER_INSTRUCTION.count("{mystery_report}")
        assert count == 1, f"{{mystery_report}} が {count} 回出現（期待: 1回）"


# --- テスト用ヘルパー（conftest で google.genai.types がモック済みのため SimpleNamespace を使用） ---

from types import SimpleNamespace


def _make_part(*, text=None, function_call=None, function_response=None):
    """テスト用の Part 相当オブジェクトを生成する。"""
    return SimpleNamespace(
        text=text,
        function_call=function_call,
        function_response=function_response,
    )


def _make_content(role="user", parts=None):
    """テスト用の Content 相当オブジェクトを生成する。"""
    return SimpleNamespace(role=role, parts=parts)


def _make_leaked_content(text_parts: list[str]):
    """ADK _present_other_agent_message 形式のリークコンテンツを生成する。"""
    return _make_content(
        role="user",
        parts=[_make_part(text=t) for t in text_parts],
    )


def _make_tool_content():
    """function_call を含むコンテンツを生成する。"""
    return _make_content(
        role="model",
        parts=[_make_part(
            function_call=SimpleNamespace(
                name="count_words",
                args={"text": "hello world", "min_words": 2000, "max_words": 3500},
            ),
        )],
    )


def _make_tool_response_content():
    """function_response を含むコンテンツを生成する。"""
    return _make_content(
        role="user",
        parts=[_make_part(
            function_response=SimpleNamespace(
                name="count_words",
                response={"word_count": 2500, "within_range": True},
            ),
        )],
    )


def _make_llm_request(contents, system_instruction: str = ""):
    """テスト用の LlmRequest モックを生成する。"""
    request = MagicMock()
    request.contents = contents
    if system_instruction:
        si_part = _make_part(text=system_instruction)
        si = SimpleNamespace(parts=[si_part])
        config = SimpleNamespace(system_instruction=si)
        request.config = config
    else:
        request.config = None
    return request


class TestIsLeakedContent:
    """_is_leaked_content のテスト"""

    def test_detects_for_context_pattern(self):
        """'For context:' 先頭パートを持つコンテンツをリークとして検出する。"""
        content = _make_leaked_content([
            "For context:",
            "[armchair_polymath] said: Long analysis report...",
        ])
        assert _is_leaked_content(content) is True

    def test_ignores_normal_user_message(self):
        """通常のユーザーメッセージはリークと判定しない。"""
        content = _make_content(
            role="user",
            parts=[_make_part(text="Write a blog article about this mystery.")],
        )
        assert _is_leaked_content(content) is False

    def test_ignores_empty_parts(self):
        """parts が空のコンテンツはリークと判定しない。"""
        content = _make_content(role="user", parts=[])
        assert _is_leaked_content(content) is False

    def test_ignores_none_parts(self):
        """parts が None のコンテンツはリークと判定しない。"""
        content = _make_content(role="user", parts=None)
        assert _is_leaked_content(content) is False

    def test_ignores_tool_contents(self):
        """function_call/response を含むコンテンツはリークと判定しない。"""
        assert _is_leaked_content(_make_tool_content()) is False
        assert _is_leaked_content(_make_tool_response_content()) is False


class TestHasFunctionParts:
    """_has_function_parts のテスト"""

    def test_detects_function_call(self):
        assert _has_function_parts(_make_tool_content()) is True

    def test_detects_function_response(self):
        assert _has_function_parts(_make_tool_response_content()) is True

    def test_text_only_returns_false(self):
        content = _make_content(
            role="user",
            parts=[_make_part(text="Just text")],
        )
        assert _has_function_parts(content) is False


class TestStorytellerBeforeModel:
    """_storyteller_before_model のテスト"""

    def test_purge_removes_leaked_preserves_tools(self):
        """パージでリークコンテンツが除去され、ツールコンテンツが保持される。"""
        leaked = _make_leaked_content([
            "For context:",
            "[scholar_en] said: Very long scholar analysis..." * 100,
        ])
        tool_call = _make_tool_content()
        tool_resp = _make_tool_response_content()

        request = _make_llm_request([leaked, tool_call, tool_resp])
        ctx = _make_callback_context()
        ctx.state["mystery_report"] = "Some report text"

        result = _storyteller_before_model(ctx, request)

        assert result is None
        # リークは除去、ツールは保持
        assert len(request.contents) == 2
        assert request.contents[0] is tool_call
        assert request.contents[1] is tool_resp

    def test_preserves_all_when_no_leak(self):
        """リークがない場合はすべてのコンテンツが保持される。"""
        normal = _make_content(
            role="user",
            parts=[_make_part(text="Write the article.")],
        )
        tool_call = _make_tool_content()

        request = _make_llm_request([normal, tool_call])
        ctx = _make_callback_context()
        ctx.state["mystery_report"] = "Report"

        _storyteller_before_model(ctx, request)

        assert len(request.contents) == 2

    def test_logs_mystery_report_tokens(self, caplog):
        """mystery_report のトークン数がログに記録される。"""
        report = "x" * 40_000  # 10,000 トークン相当
        ctx = _make_callback_context()
        ctx.state["mystery_report"] = report

        request = _make_llm_request([])

        with caplog.at_level(logging.INFO, logger="mystery_agents.agents.storyteller"):
            _storyteller_before_model(ctx, request)

        info_records = [
            r for r in caplog.records if r.levelno == logging.INFO
        ]
        assert any("10,000 tokens" in r.message for r in info_records)

    def test_logs_input_token_breakdown(self, caplog):
        """system_instruction と contents のトークン内訳がログに記録される。"""
        ctx = _make_callback_context()
        ctx.state["mystery_report"] = "report"

        si_text = "A" * 4_000  # 1,000 トークン相当
        request = _make_llm_request([], system_instruction=si_text)

        with caplog.at_level(logging.INFO, logger="mystery_agents.agents.storyteller"):
            _storyteller_before_model(ctx, request)

        log_text = " ".join(r.message for r in caplog.records)
        assert "system_instruction=" in log_text
        assert "contents=" in log_text
        assert "パージ除去=" in log_text

    def test_logs_purged_token_count(self, caplog):
        """パージで除去されたトークン数がログに記録される。"""
        leaked_text = "A" * 8_000  # 2,000 トークン相当
        leaked = _make_leaked_content(["For context:", leaked_text])

        request = _make_llm_request([leaked])
        ctx = _make_callback_context()
        ctx.state["mystery_report"] = ""

        with caplog.at_level(logging.INFO, logger="mystery_agents.agents.storyteller"):
            _storyteller_before_model(ctx, request)

        info_records = [
            r for r in caplog.records if r.levelno == logging.INFO
        ]
        # パージ除去が 0 でないことを確認
        assert any("パージ除去=" in r.message and "パージ除去=0" not in r.message
                    for r in info_records)


class TestEstimateTokens:
    """_estimate_tokens のテスト"""

    def test_empty_string(self):
        assert _estimate_tokens("") == 0

    def test_known_length(self):
        assert _estimate_tokens("A" * 400) == 100

    def test_none_like(self):
        assert _estimate_tokens("") == 0
