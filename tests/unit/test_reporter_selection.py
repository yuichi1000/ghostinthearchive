"""レポーター選択機能のユニットテスト。

create_storyteller_model() / create_storyteller() / build_pipeline() が
正しいモデルアダプタとパイプライン構造を生成することを検証する。
"""

import pytest

from shared.model_config import (
    DEFAULT_REPORTER,
    REPORTER_MODELS,
    create_storyteller_model,
)


class TestReporterModelsRegistry:
    """REPORTER_MODELS レジストリの構造検証。"""

    def test_default_reporter_exists(self):
        """DEFAULT_REPORTER がレジストリに存在すること。"""
        assert DEFAULT_REPORTER in REPORTER_MODELS

    def test_all_reporters_have_required_keys(self):
        """全レポーターが model_id, provider, display_name を持つこと。"""
        for name, config in REPORTER_MODELS.items():
            assert "model_id" in config, f"{name} に model_id がない"
            assert "provider" in config, f"{name} に provider がない"
            assert "display_name" in config, f"{name} に display_name がない"

    def test_six_reporters_registered(self):
        """6種のレポーターが登録されていること。"""
        assert len(REPORTER_MODELS) == 6
        expected = {"claude", "gemini", "gpt", "llama", "deepseek", "mistral"}
        assert set(REPORTER_MODELS.keys()) == expected


class TestCreateStorytellerModel:
    """create_storyteller_model() のテスト。"""

    def test_gemini_returns_native_model(self):
        """gemini レポーターは Gemini（native）モデルを返すこと。"""
        from google.adk.models.google_llm import Gemini

        result = create_storyteller_model("gemini")
        # Gemini は MagicMock なので呼び出しを検証
        last_call = Gemini.call_args
        assert last_call is not None

    def test_claude_returns_litellm(self):
        """claude レポーターは LiteLlm アダプタを返すこと。"""
        from google.adk.models.lite_llm import LiteLlm

        create_storyteller_model("claude")
        last_call = LiteLlm.call_args
        assert last_call is not None
        assert last_call.kwargs.get("model") == "openrouter/anthropic/claude-sonnet-4.5"

    def test_gpt_returns_litellm(self):
        """gpt レポーターは LiteLlm アダプタを返すこと。"""
        from google.adk.models.lite_llm import LiteLlm

        LiteLlm.reset_mock()
        create_storyteller_model("gpt")
        last_call = LiteLlm.call_args
        assert last_call is not None
        assert last_call.kwargs.get("model") == "openrouter/openai/gpt-4o"

    def test_llama_returns_litellm(self):
        """llama レポーターは LiteLlm アダプタを返すこと。"""
        from google.adk.models.lite_llm import LiteLlm

        LiteLlm.reset_mock()
        create_storyteller_model("llama")
        last_call = LiteLlm.call_args
        assert last_call is not None
        assert last_call.kwargs.get("model") == "openrouter/meta-llama/llama-4-maverick"

    def test_deepseek_returns_litellm(self):
        """deepseek レポーターは LiteLlm アダプタを返すこと。"""
        from google.adk.models.lite_llm import LiteLlm

        LiteLlm.reset_mock()
        create_storyteller_model("deepseek")
        last_call = LiteLlm.call_args
        assert last_call is not None
        assert last_call.kwargs.get("model") == "openrouter/deepseek/deepseek-chat"

    def test_mistral_returns_litellm(self):
        """mistral レポーターは LiteLlm アダプタを返すこと。"""
        from google.adk.models.lite_llm import LiteLlm

        LiteLlm.reset_mock()
        create_storyteller_model("mistral")
        last_call = LiteLlm.call_args
        assert last_call is not None
        assert last_call.kwargs.get("model") == "openrouter/mistralai/mistral-large-2512"

    def test_unknown_reporter_raises_value_error(self):
        """不正なレポーター名で ValueError が発生すること。"""
        with pytest.raises(ValueError, match="Unknown reporter 'unknown'"):
            create_storyteller_model("unknown")

    def test_default_reporter_is_claude(self):
        """デフォルトレポーターが claude であること。"""
        assert DEFAULT_REPORTER == "claude"


class TestCreateStoryteller:
    """create_storyteller() ファクトリのテスト。"""

    def test_returns_agent(self):
        """create_storyteller() が LlmAgent を返すこと。"""
        from mystery_agents.agents.storyteller import create_storyteller

        result = create_storyteller()
        # LlmAgent は MagicMock なので、呼び出しが行われたことを確認
        assert result is not None

    def test_custom_reporter(self):
        """create_storyteller("gemini") がエラーなく動作すること。"""
        from mystery_agents.agents.storyteller import create_storyteller

        result = create_storyteller("gemini")
        assert result is not None


class TestBuildPipeline:
    """build_pipeline() のテスト。"""

    def test_default_pipeline(self):
        """build_pipeline() がデフォルトでパイプラインを構築すること。"""
        from mystery_agents.agent import build_pipeline

        result = build_pipeline()
        assert result is not None

    def test_custom_reporter_pipeline(self):
        """build_pipeline("gemini") がカスタムレポーターでパイプラインを構築すること。"""
        from mystery_agents.agent import build_pipeline

        result = build_pipeline("gemini")
        assert result is not None

    def test_invalid_reporter_raises(self):
        """build_pipeline() に不正なレポーター名を渡すと ValueError が発生すること。"""
        from mystery_agents.agent import build_pipeline

        with pytest.raises(ValueError, match="Unknown reporter"):
            build_pipeline("nonexistent")
