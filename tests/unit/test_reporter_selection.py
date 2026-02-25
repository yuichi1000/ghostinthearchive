"""ストーリーテラー選択機能のユニットテスト。

create_storyteller_model() / create_storyteller() / build_pipeline() が
正しいモデルアダプタとパイプライン構造を生成することを検証する。
"""

import pytest

from shared.model_config import (
    DEFAULT_STORYTELLER,
    STORYTELLER_MODELS,
    create_storyteller_model,
)


class TestStorytellerModelsRegistry:
    """STORYTELLER_MODELS レジストリの構造検証。"""

    def test_default_storyteller_exists(self):
        """DEFAULT_STORYTELLER がレジストリに存在すること。"""
        assert DEFAULT_STORYTELLER in STORYTELLER_MODELS

    def test_all_storytellers_have_required_keys(self):
        """全ストーリーテラーが model_id, provider, display_name を持つこと。"""
        for name, config in STORYTELLER_MODELS.items():
            assert "model_id" in config, f"{name} に model_id がない"
            assert "provider" in config, f"{name} に provider がない"
            assert "display_name" in config, f"{name} に display_name がない"

    def test_six_storytellers_registered(self):
        """6種のストーリーテラーが登録されていること。"""
        assert len(STORYTELLER_MODELS) == 6
        expected = {"claude", "gemini", "gpt", "llama", "deepseek", "mistral"}
        assert set(STORYTELLER_MODELS.keys()) == expected

    def test_openrouter_models_have_provider_order(self):
        """OpenRouter 経由の全ストーリーテラーに openrouter_provider_order が設定されていること。"""
        for name, config in STORYTELLER_MODELS.items():
            if config["provider"] == "litellm":
                assert "openrouter_provider_order" in config, (
                    f"{name} に openrouter_provider_order がない"
                )
                order = config["openrouter_provider_order"]
                assert isinstance(order, list) and len(order) > 0, (
                    f"{name} の openrouter_provider_order が空"
                )


class TestCreateStorytellerModel:
    """create_storyteller_model() のテスト。"""

    def test_gemini_returns_native_model(self):
        """gemini ストーリーテラーは Gemini（native）モデルを返すこと。"""
        from google.adk.models.google_llm import Gemini

        result = create_storyteller_model("gemini")
        # Gemini は MagicMock なので呼び出しを検証
        last_call = Gemini.call_args
        assert last_call is not None

    def test_claude_returns_litellm(self):
        """claude ストーリーテラーは LiteLlm アダプタを返すこと。"""
        from google.adk.models.lite_llm import LiteLlm

        create_storyteller_model("claude")
        last_call = LiteLlm.call_args
        assert last_call is not None
        assert last_call.kwargs.get("model") == "openrouter/anthropic/claude-sonnet-4.5"

    def test_gpt_returns_litellm(self):
        """gpt ストーリーテラーは LiteLlm アダプタを返すこと。"""
        from google.adk.models.lite_llm import LiteLlm

        LiteLlm.reset_mock()
        create_storyteller_model("gpt")
        last_call = LiteLlm.call_args
        assert last_call is not None
        assert last_call.kwargs.get("model") == "openrouter/openai/gpt-4o"

    def test_llama_returns_litellm(self):
        """llama ストーリーテラーは LiteLlm アダプタを返すこと。"""
        from google.adk.models.lite_llm import LiteLlm

        LiteLlm.reset_mock()
        create_storyteller_model("llama")
        last_call = LiteLlm.call_args
        assert last_call is not None
        assert last_call.kwargs.get("model") == "openrouter/meta-llama/llama-4-maverick"

    def test_deepseek_returns_litellm(self):
        """deepseek ストーリーテラーは LiteLlm アダプタを返すこと。"""
        from google.adk.models.lite_llm import LiteLlm

        LiteLlm.reset_mock()
        create_storyteller_model("deepseek")
        last_call = LiteLlm.call_args
        assert last_call is not None
        assert last_call.kwargs.get("model") == "openrouter/deepseek/deepseek-chat"

    def test_mistral_returns_litellm(self):
        """mistral ストーリーテラーは LiteLlm アダプタを返すこと。"""
        from google.adk.models.lite_llm import LiteLlm

        LiteLlm.reset_mock()
        create_storyteller_model("mistral")
        last_call = LiteLlm.call_args
        assert last_call is not None
        assert last_call.kwargs.get("model") == "openrouter/mistralai/mistral-large-2512"

    def test_openrouter_models_pass_provider_routing(self):
        """OpenRouter 経由モデルが extra_body にプロバイダルーティング設定を渡すこと。"""
        from google.adk.models.lite_llm import LiteLlm

        for name, config in STORYTELLER_MODELS.items():
            if config["provider"] != "litellm":
                continue
            LiteLlm.reset_mock()
            create_storyteller_model(name)
            last_call = LiteLlm.call_args
            assert last_call is not None, f"{name} の LiteLlm 呼び出しがない"
            extra_body = last_call.kwargs.get("extra_body")
            assert extra_body is not None, f"{name} に extra_body がない"
            provider = extra_body.get("provider")
            assert provider is not None, f"{name} の extra_body に provider がない"
            assert "order" in provider, f"{name} の provider に order がない"
            assert provider["order"] == config["openrouter_provider_order"]
            assert provider["allow_fallbacks"] is False

    def test_gemini_does_not_pass_extra_body(self):
        """Gemini（native）モデルは extra_body を渡さないこと。"""
        from google.adk.models.google_llm import Gemini

        Gemini.reset_mock()
        create_storyteller_model("gemini")
        last_call = Gemini.call_args
        assert last_call is not None
        assert "extra_body" not in last_call.kwargs

    def test_unknown_storyteller_raises_value_error(self):
        """不正なストーリーテラー名で ValueError が発生すること。"""
        with pytest.raises(ValueError, match="Unknown storyteller 'unknown'"):
            create_storyteller_model("unknown")

    def test_default_storyteller_is_claude(self):
        """デフォルトストーリーテラーが claude であること。"""
        assert DEFAULT_STORYTELLER == "claude"


class TestCreateStoryteller:
    """create_storyteller() ファクトリのテスト。"""

    def test_returns_agent(self):
        """create_storyteller() が LlmAgent を返すこと。"""
        from mystery_agents.agents.storyteller import create_storyteller

        result = create_storyteller()
        # LlmAgent は MagicMock なので、呼び出しが行われたことを確認
        assert result is not None

    def test_custom_storyteller(self):
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

    def test_custom_storyteller_pipeline(self):
        """build_pipeline("gemini") がカスタムストーリーテラーでパイプラインを構築すること。"""
        from mystery_agents.agent import build_pipeline

        result = build_pipeline("gemini")
        assert result is not None

    def test_invalid_storyteller_raises(self):
        """build_pipeline() に不正なストーリーテラー名を渡すと ValueError が発生すること。"""
        from mystery_agents.agent import build_pipeline

        with pytest.raises(ValueError, match="Unknown storyteller"):
            build_pipeline("nonexistent")

    def test_multiple_build_pipeline_no_parent_conflict(self):
        """build_pipeline() を複数回呼び出しても ADK 親重複エラーが発生しないこと。

        回帰テスト: 旧実装ではモジュールレベルのシングルトンを再利用していたため、
        2回目の呼び出しで「Agent already has a parent agent」エラーが発生していた。
        """
        from mystery_agents.agent import build_pipeline

        pipeline1 = build_pipeline()
        pipeline2 = build_pipeline("gemini")
        # 両方とも正常に構築され、異なるインスタンスであること
        assert pipeline1 is not pipeline2

    def test_build_pipeline_returns_independent_instances(self):
        """build_pipeline() が毎回独立したエージェントインスタンスを返すこと。"""
        from mystery_agents.agent import build_pipeline

        pipeline1 = build_pipeline()
        pipeline2 = build_pipeline()
        # sub_agents が異なるインスタンスであること
        assert pipeline1.sub_agents[0] is not pipeline2.sub_agents[0]
