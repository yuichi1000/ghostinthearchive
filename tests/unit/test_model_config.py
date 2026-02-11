"""shared/model_config のユニットテスト。

Gemini モデルアダプタのリトライ設定ファクトリ関数が
正常に呼び出せること、モデル名定数が正しいことを検証する。
"""

from shared.model_config import (
    MODEL_FLASH,
    MODEL_PRO,
    create_flash_model,
    create_pro_model,
)


class TestModelConstants:
    """モデル名定数のテスト。"""

    def test_model_pro_name(self):
        assert MODEL_PRO == "gemini-3-pro-preview"

    def test_model_flash_name(self):
        assert MODEL_FLASH == "gemini-2.5-flash"


class TestCreateProModel:
    """create_pro_model() のテスト。"""

    def test_returns_non_none(self):
        model = create_pro_model()
        assert model is not None

class TestCreateFlashModel:
    """create_flash_model() のテスト。"""

    def test_returns_non_none(self):
        model = create_flash_model()
        assert model is not None
