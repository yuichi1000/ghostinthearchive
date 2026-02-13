"""Curator ドメインクエリ — Firestore からテーマ提案に必要な情報を取得する。

CLI (`cli.py`) と本番サービス (`services/curator.py`) の両方から使用される。
"""

from __future__ import annotations

from collections import Counter

from shared.firestore import get_firestore_client

# 8分類コードの定義（mystery_id プレフィックス）
ALL_CATEGORIES = ["HIS", "FLK", "ANT", "OCC", "URB", "CRM", "REL", "LOC"]


def get_existing_titles() -> list[str]:
    """Fetch titles of all existing mysteries from Firestore."""
    try:
        db = get_firestore_client()
        docs = db.collection("mysteries").select(["title"]).stream(timeout=10)
        return [
            title
            for doc in docs
            if (title := doc.to_dict().get("title"))
        ]
    except Exception as e:
        print(f"Warning: Could not fetch existing titles: {e}")
        return []


def get_category_distribution() -> dict[str, int]:
    """Firestore の mystery_id フィールドからカテゴリ分布を集計する。

    mystery_id は {CLS}-{ST}-{AREA}-{TS} 形式で、先頭3文字が分類コード。
    """
    try:
        db = get_firestore_client()
        docs = db.collection("mysteries").select(["mystery_id"]).stream(timeout=10)
        prefixes = []
        for doc in docs:
            mystery_id = doc.to_dict().get("mystery_id", "")
            if mystery_id and len(mystery_id) >= 3:
                prefix = mystery_id[:3].upper()
                if prefix in ALL_CATEGORIES:
                    prefixes.append(prefix)
        return dict(Counter(prefixes))
    except Exception as e:
        print(f"Warning: Could not fetch category distribution: {e}")
        return {}


def format_category_distribution(distribution: dict[str, int]) -> str:
    """カテゴリ分布をプロンプト用テキストに変換する。

    空の場合はコールドスタート向けメッセージを返す。
    データありの場合は各カテゴリの件数と過小表現カテゴリを表示。
    """
    if not distribution:
        return (
            "No existing articles yet. This is a fresh start — "
            "use all 8 categories broadly. Aim for maximum diversity across "
            "HIS, FLK, ANT, OCC, URB, CRM, REL, and LOC."
        )

    total = sum(distribution.values())
    lines = []
    for cat in ALL_CATEGORIES:
        count = distribution.get(cat, 0)
        lines.append(f"  {cat}: {count} article(s)")

    # 過小表現カテゴリ（0件 or 平均以下）の特定
    avg = total / len(ALL_CATEGORIES)
    underrepresented = [
        cat for cat in ALL_CATEGORIES
        if distribution.get(cat, 0) < avg
    ]

    if underrepresented:
        lines.append(
            f"\nUnderrepresented categories (prioritize these): "
            f"{', '.join(underrepresented)}"
        )

    return "\n".join(lines)
