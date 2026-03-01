"""Tests for alchemist pipeline gate callbacks.

Alchemist パイプラインゲートが前段の出力を判定し、
有意なデータがない場合に後続エージェントをスキップすることを検証する。
"""

from alchemist_agents.agents.pipeline_gate import (
    make_design_gate,
    make_render_gate,
)


class MockCallbackContext:
    """CallbackContext の軽量モック。"""

    def __init__(self, state: dict):
        self.state = state


class TestDesignGate:
    """make_design_gate のテスト。"""

    def test_no_content_skips(self):
        """creative_content が NO_CONTENT なら Content を返す（スキップ）。"""
        ctx = MockCallbackContext(state={
            "creative_content": "NO_CONTENT: No story content available.",
        })
        gate = make_design_gate()
        result = gate(ctx)
        assert result is not None

    def test_empty_content_skips(self):
        """creative_content が空ならスキップ。"""
        ctx = MockCallbackContext(state={
            "creative_content": "",
        })
        gate = make_design_gate()
        result = gate(ctx)
        assert result is not None

    def test_missing_key_skips(self):
        """creative_content キーが存在しないならスキップ。"""
        ctx = MockCallbackContext(state={})
        gate = make_design_gate()
        result = gate(ctx)
        assert result is not None

    def test_has_content_proceeds(self):
        """有意なブログ記事があれば None を返す（実行継続）。"""
        ctx = MockCallbackContext(state={
            "creative_content": "# The Bell Witch of Adams, Tennessee\n\nIn the autumn of 1817...",
        })
        gate = make_design_gate()
        result = gate(ctx)
        assert result is None

    def test_not_available_skips(self):
        """Not available マーカーでもスキップ。"""
        ctx = MockCallbackContext(state={
            "creative_content": "Not available",
        })
        gate = make_design_gate()
        result = gate(ctx)
        assert result is not None


class TestRenderGate:
    """make_render_gate のテスト。"""

    def test_no_proposal_skips(self):
        """structured_design_proposal が未設定ならスキップ。"""
        ctx = MockCallbackContext(state={})
        gate = make_render_gate()
        result = gate(ctx)
        assert result is not None

    def test_empty_proposal_skips(self):
        """structured_design_proposal が空 dict ならスキップ。"""
        ctx = MockCallbackContext(state={
            "structured_design_proposal": {},
        })
        gate = make_render_gate()
        result = gate(ctx)
        assert result is not None

    def test_none_proposal_skips(self):
        """structured_design_proposal が None ならスキップ。"""
        ctx = MockCallbackContext(state={
            "structured_design_proposal": None,
        })
        gate = make_render_gate()
        result = gate(ctx)
        assert result is not None

    def test_proposal_without_products_skips(self):
        """structured_design_proposal に products キーがないならスキップ。"""
        ctx = MockCallbackContext(state={
            "structured_design_proposal": {"metadata": "something"},
        })
        gate = make_render_gate()
        result = gate(ctx)
        assert result is not None

    def test_proposal_with_empty_products_skips(self):
        """products が空配列ならスキップ。"""
        ctx = MockCallbackContext(state={
            "structured_design_proposal": {"products": []},
        })
        gate = make_render_gate()
        result = gate(ctx)
        assert result is not None

    def test_valid_proposal_proceeds(self):
        """有効なデザイン提案があれば None を返す（実行継続）。"""
        ctx = MockCallbackContext(state={
            "structured_design_proposal": {
                "products": [
                    {"product_type": "tshirt", "imagen_prompts": {"background": "..."}}
                ]
            },
        })
        gate = make_render_gate()
        result = gate(ctx)
        assert result is None
