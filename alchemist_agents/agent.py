"""Alchemist Design Pipeline - ADK Agent Definition

デザイン企画パイプライン: Alchemist (デザイン提案生成)
レンダリングパイプライン: AlchemistRenderer (Imagen 3 画像生成)

Podcast パイプラインと同じ独立パッケージ・2フェーズパターン。
"""

from google.adk.agents import SequentialAgent

from .agents.alchemist import create_alchemist
from .agents.alchemist_renderer import create_alchemist_renderer
from .agents.pipeline_gate import make_design_gate, make_render_gate


def build_design_pipeline() -> SequentialAgent:
    """デザイン企画パイプラインを構築する（Phase 1）。

    呼び出しごとにフレッシュなエージェントインスタンスを生成する。
    before_agent_callback で creative_content の存在を確認し、
    有意なデータがなければスキップする。
    """
    return SequentialAgent(
        name="alchemist_commander",
        description=(
            "プロダクトデザイン企画パイプライン。"
            "Alchemist がブログ記事を分析し、T-シャツ・マグカップのデザイン提案を生成する。"
        ),
        sub_agents=[create_alchemist()],
        before_agent_callback=make_design_gate(),
    )


def build_render_pipeline() -> SequentialAgent:
    """レンダリングパイプラインを構築する（Phase 2）。

    呼び出しごとにフレッシュなエージェントインスタンスを生成する。
    before_agent_callback で structured_design_proposal の存在を確認し、
    有意なデータがなければスキップする。
    """
    return SequentialAgent(
        name="alchemist_render_commander",
        description=(
            "プロダクトデザインレンダリングパイプライン。"
            "AlchemistRenderer がデザイン提案に基づき Imagen 3 でアセット画像を生成する。"
        ),
        sub_agents=[create_alchemist_renderer()],
        before_agent_callback=make_render_gate(),
    )


# ADK ローダーの発見規約
root_agent = build_design_pipeline()

# ログ対象外のエージェント名（ルート SequentialAgent 自体は進捗表示不要）
SKIP_AUTHORS = {"alchemist_commander", "alchemist_render_commander"}
