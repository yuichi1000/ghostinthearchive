"""討論ホワイトボードツール。

LoopAgent ベースの逐次討論で使用する共有ホワイトボードへの書き込みツール。
各 Scholar（討論モード）が自分の発言を追記し、次のラウンドで全員が読めるようにする。
"""

from google.adk.tools.tool_context import ToolContext


def append_to_whiteboard(
    speaker: str,
    round_number: int,
    contribution: str,
    tool_context: ToolContext,
) -> str:
    """Append a debate contribution to the shared whiteboard.

    Each Scholar in debate mode calls this tool to add their perspective
    to the shared whiteboard. Contributions are accumulated (not overwritten)
    so that all participants can see the full discussion history.

    Args:
        speaker: Name of the speaking Scholar's perspective (e.g. "English", "German").
        round_number: Current debate round number (1 or 2).
        contribution: The debate contribution text.
        tool_context: ADK tool context for session state access.

    Returns:
        Confirmation message.
    """
    current = tool_context.state.get("debate_whiteboard", "")

    entry = f"### [Round {round_number}] {speaker} Perspective\n\n{contribution}\n\n"
    tool_context.state["debate_whiteboard"] = current + entry

    return f"Contribution from {speaker} (Round {round_number}) appended to whiteboard."
