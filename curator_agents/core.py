"""Curator ビジネスロジック — テーマ提案の共通処理を一元管理。

CLI (`cli.py`) と HTTP サービス (`services/curator.py`) の両方から呼ばれる。
Firestore クエリ → セッション状態構築 → エージェント実行 → JSON パース・検証
の一連の処理を `suggest_themes()` に集約する。
"""

import asyncio
import json
import logging

from .agents.curator import curator_agent
from .probe import probe_all_themes
from .queries import (
    get_existing_titles,
    get_category_distribution,
    format_category_distribution,
)
from .runner import run_single_agent
from .schemas import strip_markdown_codeblock, validate_suggestions
from shared.constants import is_meaningful
from shared.pipeline_failure import get_recent_failures

logger = logging.getLogger(__name__)


async def suggest_themes(
    *,
    user_message: str = "Suggest 5 research themes.",
    empty_titles_text: str = "(None - no themes have been investigated yet)",
) -> list[dict]:
    """テーマ提案の共通ロジック。

    1. Firestore 3クエリ並列実行（既存タイトル, 最近の失敗, カテゴリ分布）
    2. テキスト整形 + セッション状態構築
    3. Curator エージェント実行
    4. マークダウンコードブロック除去 + JSON パース + バリデーション

    Args:
        user_message: エージェントに送信するメッセージ（CLI: 日本語、サービス: 英語）
        empty_titles_text: 既存タイトルが0件の場合の表示テキスト

    Returns:
        検証済みテーマ提案の dict リスト

    Raises:
        json.JSONDecodeError: エージェント出力の JSON パースに失敗した場合
        ValueError: 全件バリデーション失敗の場合
    """
    # Firestore 3クエリを並列実行
    existing_titles, recent_failures, distribution = await asyncio.gather(
        asyncio.to_thread(get_existing_titles),
        asyncio.to_thread(get_recent_failures, 20),
        asyncio.to_thread(get_category_distribution),
    )

    titles_text = (
        "\n".join(f"- {t}" for t in existing_titles)
        if existing_titles
        else empty_titles_text
    )

    failed_themes = list({f["theme"] for f in recent_failures if f.get("theme")})
    failed_themes_text = (
        "\n".join(f"- {t}" for t in failed_themes) if failed_themes else "(None)"
    )

    category_distribution_text = format_category_distribution(distribution)

    result_text = await run_single_agent(
        curator_agent,
        app_name="ghost_in_the_archive_curator",
        user_id="curator",
        session_id="theme_suggestion",
        state={
            "existing_titles": titles_text,
            "failed_themes": failed_themes_text,
            "category_distribution": category_distribution_text,
        },
        user_message=user_message,
    )

    # 失敗マーカー早期検出（JSONDecodeError より先に判定）
    if not is_meaningful(result_text):
        raise ValueError(
            f"Agent returned failure marker. Raw: {result_text[:500]}"
        )

    # マークダウンコードブロック除去 + JSON パース
    cleaned = strip_markdown_codeblock(result_text)
    raw_suggestions = json.loads(cleaned)

    # スキーマ検証
    suggestions = validate_suggestions(raw_suggestions)
    if not suggestions:
        raise ValueError(
            f"All suggestions failed schema validation. Raw: {result_text[:500]}"
        )

    # API プローブ: 実際のヒット件数に基づいて coverage_score を算出・上書き
    suggestions = await asyncio.to_thread(probe_all_themes, suggestions)

    # カバレッジスコア順にソート（HIGH → MEDIUM → LOW）
    _SCORE_ORDER = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}
    suggestions.sort(key=lambda s: _SCORE_ORDER.get(s.get("coverage_score", "LOW"), 2))

    return suggestions
