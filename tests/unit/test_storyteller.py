"""Unit tests for Storyteller agent instruction and after_model_callback."""

import logging
from unittest.mock import MagicMock

from mystery_agents.agents.storyteller import (
    STORYTELLER_INSTRUCTION,
    _storyteller_after_model,
)


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
        """正常応答（テキストあり + エラーなし）は None を返し、メタデータを記録しない。"""
        ctx = _make_callback_context()
        response = _make_llm_response(text="A compelling narrative...")

        result = _storyteller_after_model(ctx, response)

        assert result is None
        assert "storyteller_llm_metadata" not in ctx.state

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
        metadata = ctx.state["storyteller_llm_metadata"]
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
        metadata = ctx.state["storyteller_llm_metadata"]
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
        metadata = ctx.state["storyteller_llm_metadata"]
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
