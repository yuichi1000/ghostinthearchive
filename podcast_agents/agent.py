"""Podcast Pipeline - ADK Agent Definition

脚本生成パイプライン: ScriptPlanner → Scriptwriter → Podcast Translator（JA）
ScriptPlanner がアウトラインを設計し、Scriptwriter がセグメント単位で逐次執筆する。
音声生成は ADK 外の Python 関数で実行（tts.py）。
"""

from google.adk.agents import SequentialAgent

from .agents.pipeline_gate import make_script_gate
from .agents.podcast_translator import create_podcast_translator
from .agents.script_planner import create_script_planner
from .agents.scriptwriter import create_scriptwriter


def build_pipeline() -> SequentialAgent:
    """脚本生成パイプラインを構築する。

    呼び出しごとにフレッシュなエージェントインスタンスを生成する。
    before_agent_callback で creative_content の存在を確認し、
    有意なデータがなければスキップする。
    """
    return SequentialAgent(
        name="podcast_script_commander",
        description=(
            "Podcast 脚本生成パイプライン。"
            "ScriptPlanner → Scriptwriter → Podcast Translator (JA) の順で実行し、"
            "ブログ記事からアウトライン設計・構造化脚本・日本語訳を生成する。"
        ),
        sub_agents=[
            create_script_planner(),
            create_scriptwriter(),
            create_podcast_translator(),
        ],
        before_agent_callback=make_script_gate(),
    )


# ADK ローダーの発見規約
podcast_script_commander = build_pipeline()
root_agent = podcast_script_commander

# ログ対象外のエージェント名（ルート SequentialAgent 自体は進捗表示不要）
SKIP_AUTHORS = {"podcast_script_commander"}
