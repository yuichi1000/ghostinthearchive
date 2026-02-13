"""Curator スキーマ定義 — カテゴリ一元管理 + LLM 出力検証。

ClassificationCode enum を唯一の信頼源（Single Source of Truth）として使用し、
カテゴリ定義の重複を排除する。
"""

from __future__ import annotations

import logging
from typing import Literal

from pydantic import BaseModel, ValidationError

from mystery_agents.schemas.mystery_id import (
    CLASSIFICATION_DESCRIPTIONS_EN,
    ClassificationCode,
)

logger = logging.getLogger(__name__)

# ClassificationCode enum から導出した全カテゴリコードのリスト
ALL_CATEGORIES: list[str] = [code.value for code in ClassificationCode]

# Literal 型（Pydantic 検証用）
CategoryCode = Literal["HIS", "FLK", "ANT", "OCC", "URB", "CRM", "REL", "LOC"]


class ThemeSuggestion(BaseModel):
    """Curator エージェントが出力する1件のテーマ提案。"""

    theme: str
    description: str
    category: CategoryCode


def validate_suggestions(raw: list) -> list[dict]:
    """LLM が出力した提案リストを検証し、不正エントリを除外して返す。

    Args:
        raw: JSON パース済みのリスト（各要素は dict 想定）

    Returns:
        検証を通過したエントリの dict リスト
    """
    valid = []
    for i, item in enumerate(raw):
        try:
            suggestion = ThemeSuggestion.model_validate(item)
            valid.append(suggestion.model_dump())
        except (ValidationError, Exception) as e:
            logger.warning("テーマ提案 #%d を除外: %s (データ: %s)", i, e, item)
    return valid


def build_category_prompt_section() -> str:
    """プロンプト用カテゴリ定義テキストを動的生成する。

    CLASSIFICATION_DESCRIPTIONS_EN から各カテゴリの説明を組み立てる。
    """
    lines = []
    for code in ClassificationCode:
        desc = CLASSIFICATION_DESCRIPTIONS_EN[code]
        lines.append(f"- {code.value} ({code.name}): {desc}")
    return "\n".join(lines)


def strip_markdown_codeblock(text: str) -> str:
    """マークダウンコードブロック（```json ... ```）を除去して中身を返す。

    LLM が JSON をコードブロックで囲んで出力するケースに対応する。
    コードブロックがない場合はそのまま返す。
    """
    cleaned = text.strip()
    if "```json" in cleaned:
        cleaned = cleaned.split("```json", 1)[1].split("```", 1)[0].strip()
    elif "```" in cleaned:
        cleaned = cleaned.split("```", 1)[1].split("```", 1)[0].strip()
    return cleaned
