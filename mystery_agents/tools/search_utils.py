"""検索クエリ構築ユーティリティ。"""


def build_search_query(keywords: list[str]) -> str:
    """キーワードリストから OR 検索クエリを構築する。

    2語以上のキーワード（固有名詞やフレーズ）は引用符で囲み、
    フレーズ検索として扱う。1語のキーワードはそのまま結合する。

    Args:
        keywords: 検索キーワードのリスト

    Returns:
        OR 結合された検索クエリ文字列

    Examples:
        >>> build_search_query(["Bell Witch", "Tennessee"])
        '"Bell Witch" OR Tennessee'
        >>> build_search_query(["ghost", "haunting"])
        'ghost OR haunting'
    """
    parts = []
    for kw in keywords:
        kw = kw.strip()
        if not kw:
            continue
        if " " in kw:
            parts.append(f'"{kw}"')
        else:
            parts.append(kw)
    return " OR ".join(parts)
