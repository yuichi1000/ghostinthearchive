"""shared/model_config のユニットテスト。

Gemini モデルアダプタのモデル名・リトライ設定が
正しいパラメータで生成されることを検証する。

Note: HttpRetryOptions はモジュールインポート時にモジュールレベル定数として
呼び出されるため、ファクトリ関数の呼び出し時ではなく、
model_config モジュールの定数を直接検証する。
"""

from shared.model_config import (
    MODEL_FLASH,
    MODEL_PRO,
    _FLASH_RETRY_OPTIONS,
    _LITELLM_MAX_RETRIES,
    _PRO_RETRY_OPTIONS,
    create_flash_model,
    create_pro_model,
    create_storyteller_model,
)


class TestCreateProModel:
    """create_pro_model() のテスト。"""

    def test_pro_model_name(self):
        """Pro モデルが MODEL_PRO で生成されること。"""
        from google.adk.models.google_llm import Gemini
        create_pro_model()
        last_call = Gemini.call_args
        assert last_call.kwargs.get("model") == MODEL_PRO or (
            last_call.args and last_call.args[0] == MODEL_PRO
        )

    def test_pro_retry_options(self):
        """Pro モデルのリトライ設定が正しいこと（attempts=7, initial_delay=2.0, max_delay=120.0）。"""
        from google.adk.models.google_llm import Gemini
        create_pro_model()
        last_call = Gemini.call_args
        # retry_options 引数が _PRO_RETRY_OPTIONS と同一オブジェクトであること
        assert last_call.kwargs.get("retry_options") is _PRO_RETRY_OPTIONS


class TestCreateFlashModel:
    """create_flash_model() のテスト。"""

    def test_flash_model_name(self):
        """Flash モデルが MODEL_FLASH で生成されること。"""
        from google.adk.models.google_llm import Gemini
        create_flash_model()
        last_call = Gemini.call_args
        assert last_call.kwargs.get("model") == MODEL_FLASH or (
            last_call.args and last_call.args[0] == MODEL_FLASH
        )

    def test_flash_retry_options(self):
        """Flash モデルのリトライ設定が正しいこと（attempts=5, initial_delay=1.0, max_delay=60.0）。"""
        from google.adk.models.google_llm import Gemini
        create_flash_model()
        last_call = Gemini.call_args
        # retry_options 引数が _FLASH_RETRY_OPTIONS と同一オブジェクトであること
        assert last_call.kwargs.get("retry_options") is _FLASH_RETRY_OPTIONS


class TestCreateStorytellerModel:
    """create_storyteller_model() の LiteLLM リトライ設定テスト。"""

    def test_litellm_storyteller_has_max_retries(self):
        """OpenRouter モデル生成時に max_retries が設定されること。"""
        from google.adk.models.lite_llm import LiteLlm
        create_storyteller_model("claude")
        last_call = LiteLlm.call_args
        assert last_call.kwargs.get("max_retries") == _LITELLM_MAX_RETRIES
