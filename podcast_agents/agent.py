"""Podcast Pipeline - ADK Agent Definition

脚本生成パイプライン: ScriptPlanner → Scriptwriter → Podcast Translator（JA）
ScriptPlanner がアウトラインを設計し、Scriptwriter がセグメント単位で逐次執筆する。
音声生成は ADK 外の Python 関数で実行（tts.py）。
"""

from google.adk.agents import SequentialAgent

from .agents.script_planner import script_planner_agent
from .agents.scriptwriter import scriptwriter_agent
from .agents.podcast_translator import podcast_translator_ja

# 脚本生成パイプライン（ScriptPlanner → Scriptwriter → 日本語翻訳）
podcast_script_commander = SequentialAgent(
    name="podcast_script_commander",
    description=(
        "Podcast 脚本生成パイプライン。"
        "ScriptPlanner → Scriptwriter → Podcast Translator (JA) の順で実行し、"
        "ブログ記事からアウトライン設計・構造化脚本・日本語訳を生成する。"
    ),
    sub_agents=[script_planner_agent, scriptwriter_agent, podcast_translator_ja],
)

root_agent = podcast_script_commander
