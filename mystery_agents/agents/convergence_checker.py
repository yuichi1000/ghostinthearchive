"""討論収束判定エージェント。

LoopAgent 内で各討論ラウンド終了後に実行され、
ホワイトボードの内容を分析して新規論点が枯渇したか判定する。
収束した場合は escalate で LoopAgent を早期終了させる。

Flash モデルを使用し、コストを最小限に抑える。
"""

from google.adk.agents import LlmAgent

from shared.model_config import create_flash_model

from ..tools.debate_tools import check_debate_convergence

# === 日本語訳 ===
# あなたは討論収束判定エージェントです。
# あなたの唯一の仕事は check_debate_convergence ツールを呼び出して、
# 討論が収束したかどうかを判定することです。
# ツールの結果をそのまま返してください。
# === End 日本語訳 ===
_CONVERGENCE_CHECKER_INSTRUCTION = """
You are a convergence checker agent. Your only job is to call the
`check_debate_convergence` tool to determine if the debate has converged.
Return the tool's result as your response.
"""

convergence_checker_agent = LlmAgent(
    name="convergence_checker",
    model=create_flash_model(),
    description=(
        "Checks if the debate has converged by analyzing the whiteboard. "
        "Calls check_debate_convergence tool and escalates to end the "
        "debate loop if no significant new arguments are being introduced."
    ),
    instruction=_CONVERGENCE_CHECKER_INSTRUCTION,
    tools=[check_debate_convergence],
)
