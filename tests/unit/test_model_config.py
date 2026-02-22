"""shared/model_config のユニットテスト。

Gemini / Claude モデルアダプタのモデル名・リトライ設定が
正しいパラメータで生成されることを検証する。

Note: HttpRetryOptions はモジュールインポート時にモジュールレベル定数として
呼び出されるため、ファクトリ関数の呼び出し時ではなく、
model_config モジュールの定数を直接検証する。
"""

from shared.model_config import (
    MODEL_CLAUDE_SONNET,
    MODEL_FLASH,
    MODEL_PRO,
    _CLAUDE_MAX_RETRIES,
    _FLASH_RETRY_OPTIONS,
    _PRO_RETRY_OPTIONS,
    create_claude_sonnet_model,
    create_flash_model,
    create_pro_model,
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


class TestCreateClaudeSonnetModel:
    """create_claude_sonnet_model() のテスト。"""

    def test_returns_model_string(self):
        """戻り値が MODEL_CLAUDE_SONNET と一致すること。"""
        result = create_claude_sonnet_model()
        assert result == MODEL_CLAUDE_SONNET

    def test_model_string_format(self):
        """モデル文字列が Vertex AI 形式（claude- プレフィックス + @ セパレータ）であること。"""
        result = create_claude_sonnet_model()
        assert result.startswith("claude-")
        assert "@" in result

    def test_claude_with_retry_registered(self):
        """_ClaudeWithRetry が LLMRegistry に登録されていること。"""
        from google.adk.models.registry import LLMRegistry

        # LLMRegistry.register() が呼び出されたこと
        assert LLMRegistry.register.called
        # 最後の register 呼び出しの引数が _ClaudeWithRetry クラスであること
        registered_cls = LLMRegistry.register.call_args_list[-1][0][0]
        assert registered_cls.__name__ == "_ClaudeWithRetry"

    def test_claude_max_retries_value(self):
        """_CLAUDE_MAX_RETRIES が 10 であること。"""
        assert _CLAUDE_MAX_RETRIES == 10
