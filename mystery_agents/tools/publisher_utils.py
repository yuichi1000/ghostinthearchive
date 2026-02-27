"""Publisher ユーティリティ関数。

JSON 抽出、Mystery ID 生成、_PublishContext データクラスなど、
publisher_tools.py から分離した純粋ユーティリティ。
"""

import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional


@dataclass
class _PublishContext:
    """publish_mystery の tool_context.state インターフェースをエミュレートするプロキシ。

    Custom Agent から publish_mystery を LLM 非経由で呼び出す際に使用する。
    """

    state: dict


def _extract_json_from_text(text: str) -> Optional[dict]:
    """LLM テキスト出力から JSON dict を抽出する。

    Gemini は JSON を markdown コードブロック（```json ... ```）で包むことがある。
    直接パースを試み、失敗時にコードブロックを剥がしてリトライする。

    Args:
        text: LLM の出力テキスト

    Returns:
        パース済みの dict、または抽出できなかった場合は None
    """
    # 1. 直接パースを試行
    try:
        parsed = json.loads(text, strict=False)
        if isinstance(parsed, dict):
            return parsed
    except (json.JSONDecodeError, ValueError):
        pass

    # 2. markdown コードブロックを剥がしてリトライ
    match = re.search(r"```(?:json)?\s*\n?(.*?)\n?\s*```", text, re.DOTALL)
    if match:
        try:
            parsed = json.loads(match.group(1), strict=False)
            if isinstance(parsed, dict):
                return parsed
        except (json.JSONDecodeError, ValueError):
            pass

    return None


def _generate_mystery_id(classification: str, country_code: str, region_code: str) -> str:
    """Generate a unique mystery_id with timestamp.

    Args:
        classification: 3-letter classification code (e.g., "OCC", "HIS", "FLK").
        country_code: 2-letter ISO 3166-1 alpha-2 country code (e.g., "US", "GB", "JP").
        region_code: 3-5 letter IATA region code (e.g., "BOS", "LHR", "NRT").

    Returns:
        Mystery ID in format: {CLS}-{CC}-{REGION}-{YYYYMMDDHHMMSS}
        Example: OCC-US-BOS-20260207143025
    """
    now = datetime.now(timezone.utc)
    timestamp = now.strftime("%Y%m%d%H%M%S")
    return f"{classification.upper()}-{country_code.upper()}-{region_code.upper()}-{timestamp}"
