"""Podcast Pipeline - ADK Agent Definition

脚本生成パイプライン: Scriptwriter → Podcast Translator（JA）
音声生成は ADK 外の Python 関数で実行（tts.py）。
"""

from google.adk.agents import SequentialAgent

from .agents.scriptwriter import scriptwriter_agent
from .agents.podcast_translator import podcast_translator_ja

# 脚本生成パイプライン（Scriptwriter → 日本語翻訳）
podcast_script_commander = SequentialAgent(
    name="podcast_script_commander",
    description=(
        "Podcast 脚本生成パイプライン。"
        "Scriptwriter → Podcast Translator (JA) の順で実行し、"
        "ブログ記事から構造化脚本と日本語訳を生成する。"
    ),
    sub_agents=[scriptwriter_agent, podcast_translator_ja],
)

root_agent = podcast_script_commander
