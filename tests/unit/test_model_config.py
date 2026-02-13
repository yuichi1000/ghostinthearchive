"""shared/model_config のユニットテスト。

Gemini モデルアダプタのリトライ設定ファクトリ関数が
正常に呼び出せることを検証する。
"""

from shared.model_config import (
    create_flash_model,
    create_pro_model,
)


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
