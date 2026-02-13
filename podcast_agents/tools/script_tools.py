"""Podcast 脚本ツール

Scriptwriter Agent が構造化脚本データをセッション状態に保存するためのツール。
mystery_agents/tools/scholar_tools.py の save_structured_report パターンを踏襲。
"""

import json
import logging

from google.adk.tools.tool_context import ToolContext

logger = logging.getLogger(__name__)


def save_podcast_script(
    script_json: str,
    tool_context: ToolContext,
) -> str:
    """構造化脚本データをセッション状態に保存する。

    Scriptwriter Agent がこのツールを呼び出し、TTS 音声生成に適した
    構造化 JSON をセッション状態に保存する。

    Args:
        script_json: JSON 文字列。必須フィールド:
            - episode_title: エピソードタイトル
            - estimated_duration_minutes: 想定再生時間（分）
            - segments: セグメント配列
              各セグメント: type ("intro"/"body"/"outro"), label, text
              オプション: notes (SFX/BGM 指示)
        tool_context: ADK ToolContext（セッション状態アクセス用）

    Returns:
        保存結果の JSON 文字列
    """
    try:
        data = json.loads(script_json)
    except json.JSONDecodeError as e:
        return json.dumps(
            {"status": "error", "error": f"Invalid JSON: {e}"},
            ensure_ascii=False,
        )

    # バリデーション
    warnings: list[str] = []

    if not data.get("episode_title"):
        warnings.append("episode_title is missing or empty")

    segments = data.get("segments")
    if not segments or not isinstance(segments, list):
        return json.dumps(
            {"status": "error", "error": "segments array is required and must not be empty"},
            ensure_ascii=False,
        )

    valid_types = {"intro", "body", "outro"}
    for i, seg in enumerate(segments):
        if not isinstance(seg, dict):
            warnings.append(f"segments[{i}]: not a dict, skipping")
            continue
        seg_type = seg.get("type", "")
        if seg_type not in valid_types:
            warnings.append(f"segments[{i}]: invalid type '{seg_type}', expected one of {valid_types}")
        if not seg.get("text", "").strip():
            warnings.append(f"segments[{i}]: text is empty")

    # セッション状態に保存
    tool_context.state["structured_script"] = data

    logger.info(
        "Podcast script saved: %s (%d segments, ~%d min)",
        data.get("episode_title", "Untitled"),
        len(segments),
        data.get("estimated_duration_minutes", 0),
    )

    return json.dumps(
        {
            "status": "success",
            "message": "Structured podcast script saved to session state",
            "episode_title": data.get("episode_title", ""),
            "segment_count": len(segments),
            "estimated_duration_minutes": data.get("estimated_duration_minutes", 0),
            "warnings": warnings,
        },
        ensure_ascii=False,
    )
