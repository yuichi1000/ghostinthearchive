"""Podcast 脚本ツール

多段階脚本生成のためのツール群:
- save_script_outline: ScriptPlanner がアウトラインを保存
- save_segment: Scriptwriter がセグメント単位で逐次保存
- finalize_script: 全セグメントを最終スクリプトに組み立て

mystery_agents/tools/scholar_tools.py の save_structured_report、
mystery_agents/tools/debate_tools.py の append_to_whiteboard パターンを踏襲。
"""

import json
import logging

from google.adk.tools.tool_context import ToolContext

logger = logging.getLogger(__name__)


def save_script_outline(
    outline_json: str,
    tool_context: ToolContext,
) -> str:
    """脚本アウトラインをセッション状態に保存する。

    ScriptPlanner Agent がこのツールを呼び出し、セグメント構成・
    キーポイント・語数配分を含むアウトラインを保存する。
    同時に segment_buffer を空リストで初期化する。

    Args:
        outline_json: JSON 文字列。必須フィールド:
            - episode_title: エピソードタイトル
            - segments: セグメント配列
              各セグメント: type, label, key_points[], word_target
        tool_context: ADK ToolContext

    Returns:
        保存結果の JSON 文字列
    """
    try:
        data = json.loads(outline_json)
    except json.JSONDecodeError as e:
        return json.dumps(
            {"status": "error", "error": f"Invalid JSON: {e}"},
            ensure_ascii=False,
        )

    # バリデーション
    warnings: list[str] = []

    segments = data.get("segments")
    if not segments or not isinstance(segments, list):
        return json.dumps(
            {"status": "error", "error": "segments array is required and must not be empty"},
            ensure_ascii=False,
        )

    for i, seg in enumerate(segments):
        if not isinstance(seg, dict):
            warnings.append(f"segments[{i}]: not a dict")
            continue
        if not seg.get("key_points"):
            warnings.append(f"segments[{i}] '{seg.get('label', '?')}': key_points is missing or empty")

    # セッション状態に保存
    tool_context.state["structured_outline"] = data
    tool_context.state["segment_buffer"] = []

    total_word_target = data.get("total_word_target", 0)
    if not total_word_target:
        total_word_target = sum(
            seg.get("word_target", 0)
            for seg in segments
            if isinstance(seg, dict)
        )

    logger.info(
        "Script outline saved: %s (%d segments, ~%d words target)",
        data.get("episode_title", "Untitled"),
        len(segments),
        total_word_target,
    )

    return json.dumps(
        {
            "status": "success",
            "message": "Script outline saved. segment_buffer initialized.",
            "segment_count": len(segments),
            "total_word_target": total_word_target,
            "warnings": warnings,
        },
        ensure_ascii=False,
    )


def save_segment(
    segment_json: str,
    tool_context: ToolContext,
) -> str:
    """脚本セグメントを buffer に追加する。

    Scriptwriter Agent がセグメント単位で逐次呼び出し、
    segment_buffer に累積保存する（上書きしない）。

    Args:
        segment_json: JSON 文字列。必須フィールド:
            - type: "overview" / "act_i" / "act_ii" / "act_iii" / "act_iiii"
            - label: セグメント名
            - text: ナレーションテキスト（空不可）
            オプション: notes (SFX/BGM 指示)
        tool_context: ADK ToolContext

    Returns:
        保存結果の JSON 文字列
    """
    try:
        data = json.loads(segment_json)
    except json.JSONDecodeError as e:
        return json.dumps(
            {"status": "error", "error": f"Invalid JSON: {e}"},
            ensure_ascii=False,
        )

    # バリデーション: text は必須かつ非空
    text = data.get("text", "")
    if not isinstance(text, str) or not text.strip():
        return json.dumps(
            {"status": "error", "error": "text is required and must not be empty"},
            ensure_ascii=False,
        )

    # segment_buffer を自動初期化（save_script_outline 経由でない場合のフォールバック）
    if "segment_buffer" not in tool_context.state:
        tool_context.state["segment_buffer"] = []

    buffer: list = tool_context.state["segment_buffer"]
    segment_index = len(buffer)
    buffer.append(data)

    word_count = len(text.split())
    cumulative_word_count = sum(
        len(seg.get("text", "").split())
        for seg in buffer
    )

    logger.info(
        "Segment saved: [%d] %s (%s) - %d words (cumulative: %d)",
        segment_index,
        data.get("label", "?"),
        data.get("type", "?"),
        word_count,
        cumulative_word_count,
    )

    return json.dumps(
        {
            "status": "success",
            "segment_index": segment_index,
            "label": data.get("label", ""),
            "type": data.get("type", ""),
            "word_count": word_count,
            "cumulative_word_count": cumulative_word_count,
        },
        ensure_ascii=False,
    )


def finalize_script(
    tool_context: ToolContext,
) -> str:
    """segment_buffer から最終スクリプトを組み立てる。

    全セグメントが save_segment で蓄積された後に呼び出し、
    state["structured_script"] に最終 PodcastScript JSON を保存する。
    cli.py が読み取る同一キーに書き込むため後方互換性を維持。

    Args:
        tool_context: ADK ToolContext

    Returns:
        組み立て結果の JSON 文字列
    """
    buffer = tool_context.state.get("segment_buffer")
    if not buffer or not isinstance(buffer, list) or len(buffer) == 0:
        return json.dumps(
            {"status": "error", "error": "segment_buffer is empty or missing. Call save_segment first."},
            ensure_ascii=False,
        )

    warnings: list[str] = []

    # overview 存在チェック
    types_present = {seg.get("type") for seg in buffer if isinstance(seg, dict)}
    if "overview" not in types_present:
        warnings.append("No overview segment found")

    # structured_outline からメタデータ取得
    outline = tool_context.state.get("structured_outline", {})
    episode_title = outline.get("episode_title", "Untitled Episode")
    estimated_duration = outline.get("estimated_duration_minutes", 20)

    # 最終スクリプト組み立て
    structured_script = {
        "episode_title": episode_title,
        "estimated_duration_minutes": estimated_duration,
        "segments": list(buffer),
    }

    tool_context.state["structured_script"] = structured_script

    total_word_count = sum(
        len(seg.get("text", "").split())
        for seg in buffer
        if isinstance(seg, dict)
    )

    logger.info(
        "Script finalized: %s (%d segments, %d words)",
        episode_title,
        len(buffer),
        total_word_count,
    )

    return json.dumps(
        {
            "status": "success",
            "message": "Script assembled and saved to structured_script",
            "episode_title": episode_title,
            "segment_count": len(buffer),
            "total_word_count": total_word_count,
            "warnings": warnings,
        },
        ensure_ascii=False,
    )
