"""Merch Design Pipeline - ADK Agent Definition

デザイン企画パイプライン: Alchemist (デザイン提案生成)
レンダリングパイプライン: AlchemistRenderer (Imagen 3 画像生成)

Podcast パイプラインと同じ独立パッケージ・2フェーズパターン。
"""

from google.adk.agents import SequentialAgent

from .agents.alchemist import alchemist_agent
from .agents.alchemist_renderer import alchemist_renderer_agent

# デザイン企画パイプライン（Phase 1: Alchemist のみ）
alchemist_commander = SequentialAgent(
    name="alchemist_commander",
    description=(
        "プロダクトデザイン企画パイプライン。"
        "Alchemist がブログ記事を分析し、T-シャツ・マグカップのデザイン提案を生成する。"
    ),
    sub_agents=[alchemist_agent],
)

# レンダリングパイプライン（Phase 2: AlchemistRenderer のみ）
alchemist_render_commander = SequentialAgent(
    name="alchemist_render_commander",
    description=(
        "プロダクトデザインレンダリングパイプライン。"
        "AlchemistRenderer がデザイン提案に基づき Imagen 3 でアセット画像を生成する。"
    ),
    sub_agents=[alchemist_renderer_agent],
)

root_agent = alchemist_commander

# ログ対象外のエージェント名（ルート SequentialAgent 自体は進捗表示不要）
SKIP_AUTHORS = {"alchemist_commander", "alchemist_render_commander"}
