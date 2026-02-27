"""Armchair Polymath Agent - 言語横断統合分析

全言語 Scholar の分析結果と討論ホワイトボードを読み、
言語横断の矛盾・相関を特定し、English Master Report を作成する。

CrossReferenceScholar の後継。output_key は既存と同じ "mystery_report" を使用し、
下流エージェントとの互換性を維持。save_structured_report を必ず呼び出す。
"""

import logging

from google.adk.agents import LlmAgent
from google.genai import types

from shared.model_config import create_pro_model

from ..tools.document_inventory import get_document_inventory
from ..tools.openalex import search_academic_papers
from ..tools.scholar_tools import save_structured_report
from ..tools.search_metadata import get_search_metadata
from ..tools.word_count import count_words
from .polymath_instructions import (
    ARMCHAIR_POLYMATH_INSTRUCTION,
    INSTRUCTION_BODY,  # noqa: F401 — re-export for dynamic_polymath_block
    INSTRUCTION_PREAMBLE,  # noqa: F401 — re-export for dynamic_polymath_block
    STATIC_ANALYSES_SECTION as _STATIC_ANALYSES_SECTION,  # noqa: F401 — re-export for dynamic_polymath_block
)

logger = logging.getLogger(__name__)

# Polymath ツール一覧（DynamicPolymathBlock でも共有）
POLYMATH_TOOLS = [
    save_structured_report,
    get_search_metadata,
    search_academic_papers,
    get_document_inventory,
    count_words,
]

# モデル暴走時の安全弁（通常は EOS で自然停止するため速度に影響なし）
POLYMATH_MAX_OUTPUT_TOKENS = 32768

# ツール呼び出しカウンター用ステートキー
_TOOL_CALL_COUNT_KEY = "polymath_tool_call_count"

# ログに出力する args 値の最大文字数
_TRUNCATE_THRESHOLD = 200


def log_polymath_tool_call(tool, args, tool_context):
    """Polymath のツール呼び出しをログに記録する。

    カウンターをインクリメントし、ツール名と引数をログ出力する。
    長文フィールド（200字超）はトランケートする。
    常に None を返し、ツール実行をブロックしない。
    """
    count = tool_context.state.get(_TOOL_CALL_COUNT_KEY, 0) + 1
    tool_context.state[_TOOL_CALL_COUNT_KEY] = count

    # args の長文フィールドをトランケート
    truncated_args = {}
    for key, value in args.items():
        if isinstance(value, str) and len(value) > _TRUNCATE_THRESHOLD:
            truncated_args[key] = value[:_TRUNCATE_THRESHOLD] + "..."
        else:
            truncated_args[key] = value

    logger.info(
        "Polymath tool call #%d: %s (args: %s)",
        count,
        tool.name,
        truncated_args,
    )
    return None


# Polymath 説明文（DynamicPolymathBlock でも共有）
POLYMATH_DESCRIPTION = (
    "The Armchair Polymath: a sardonic, encyclopaedically learned synthesizer "
    "who integrates analysis results from multiple language-specific Scholars "
    "and their debate records. Identifies cross-language discrepancies, cultural "
    "biases, and produces a unified Mystery Report drawing on Fact, Folklore, "
    "and Anthropology perspectives from all available language sources."
)


def create_armchair_polymath() -> LlmAgent:
    """Armchair Polymath エージェントを新規生成する。"""
    return LlmAgent(
        name="armchair_polymath",
        model=create_pro_model(),
        description=POLYMATH_DESCRIPTION,
        instruction=ARMCHAIR_POLYMATH_INSTRUCTION,
        tools=POLYMATH_TOOLS,
        output_key="mystery_report",  # 既存と同じキー → 下流互換性維持
        generate_content_config=types.GenerateContentConfig(
            max_output_tokens=POLYMATH_MAX_OUTPUT_TOKENS,
        ),
        before_tool_callback=log_polymath_tool_call,
    )


# 後方互換: デフォルトシングルトン
armchair_polymath_agent = create_armchair_polymath()
