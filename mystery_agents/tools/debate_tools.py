"""討論ホワイトボードツール。

LoopAgent ベースの逐次討論で使用する共有ホワイトボードへの書き込みツール。
各 Scholar（討論モード）が自分の発言を追記し、次のラウンドで全員が読めるようにする。
収束判定ツール（check_debate_convergence）により新規論点の枯渇を検出し、
LoopAgent を早期終了させる。
"""

import logging
import re

from google.adk.tools.tool_context import ToolContext

logger = logging.getLogger(__name__)


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


# --- 収束判定 ---

# 新語比率の閾値: この値未満なら収束とみなす
_CONVERGENCE_THRESHOLD = 0.20


def _extract_rounds(whiteboard: str) -> dict[int, str]:
    """ホワイトボードのテキストをラウンドごとに分割する。

    Returns:
        {ラウンド番号: そのラウンドの全テキスト} の辞書
    """
    rounds: dict[int, str] = {}
    # "### [Round N]" マーカーで分割
    segments = re.split(r"### \[Round (\d+)\]", whiteboard)
    # segments[0] はマーカー前のテキスト（通常は空）
    # segments[1], segments[2] = ラウンド番号, テキスト, ...
    for i in range(1, len(segments) - 1, 2):
        round_num = int(segments[i])
        text = segments[i + 1]
        if round_num in rounds:
            rounds[round_num] += " " + text
        else:
            rounds[round_num] = text
    return rounds


def _extract_words(text: str) -> set[str]:
    """テキストから単語集合を抽出する（小文字正規化、3文字以上）。"""
    words = re.findall(r"[a-zA-Z]{3,}", text.lower())
    return set(words)


def check_debate_convergence(tool_context: ToolContext) -> str:
    """討論の収束を判定する。

    ホワイトボードの最新ラウンドと前ラウンドの単語集合を比較し、
    新語比率が閾値未満なら escalate して LoopAgent を早期終了させる。

    - ラウンド1のみ → 常に継続（比較対象がないため）
    - ラウンド2+ → 新語比率 < 20% で収束と判定

    Args:
        tool_context: ADK tool context for session state access.

    Returns:
        収束判定結果のメッセージ。
    """
    whiteboard = tool_context.state.get("debate_whiteboard", "")
    if not whiteboard:
        return "No whiteboard content found. Debate should continue."

    rounds = _extract_rounds(whiteboard)

    if len(rounds) < 2:
        return "Only one round completed. Debate should continue for more perspectives."

    # 最新2ラウンドを比較
    sorted_round_nums = sorted(rounds.keys())
    prev_text = rounds[sorted_round_nums[-2]]
    curr_text = rounds[sorted_round_nums[-1]]

    prev_words = _extract_words(prev_text)
    curr_words = _extract_words(curr_text)

    if not curr_words:
        return "Current round had no content. Debate should continue."

    new_words = curr_words - prev_words
    new_word_ratio = len(new_words) / len(curr_words)

    logger.info(
        "Convergence check: round %d→%d, prev_words=%d, curr_words=%d, "
        "new_words=%d, ratio=%.1f%%",
        sorted_round_nums[-2],
        sorted_round_nums[-1],
        len(prev_words),
        len(curr_words),
        len(new_words),
        new_word_ratio * 100,
    )

    if new_word_ratio < _CONVERGENCE_THRESHOLD:
        tool_context.actions.escalate = True
        return (
            f"Debate has CONVERGED. New word ratio: {new_word_ratio:.1%} "
            f"(threshold: {_CONVERGENCE_THRESHOLD:.0%}). "
            f"No significant new arguments. Escalating to end debate loop."
        )

    return (
        f"Debate has NOT converged. New word ratio: {new_word_ratio:.1%} "
        f"(threshold: {_CONVERGENCE_THRESHOLD:.0%}). "
        f"New arguments are still being introduced."
    )
