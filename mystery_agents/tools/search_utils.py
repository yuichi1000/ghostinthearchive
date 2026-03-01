"""検索クエリ構築ユーティリティ。"""


def _quote_if_phrase(kw: str) -> str:
    """2語以上のキーワードを引用符で囲む。"""
    kw = kw.strip()
    if " " in kw:
        return f'"{kw}"'
    return kw


def build_search_query(keywords: list[str], operator: str = "OR") -> str:
    """キーワードリストから検索クエリを構築する。

    2語以上のキーワード（固有名詞やフレーズ）は引用符で囲み、
    フレーズ検索として扱う。1語のキーワードはそのまま結合する。

    Args:
        keywords: 検索キーワードのリスト
        operator: キーワード結合演算子（デフォルト: "OR"）

    Returns:
        指定演算子で結合された検索クエリ文字列

    Examples:
        >>> build_search_query(["Bell Witch", "Tennessee"])
        '"Bell Witch" OR Tennessee'
        >>> build_search_query(["ghost", "haunting"], operator="AND")
        'ghost AND haunting'
    """
    parts = [_quote_if_phrase(kw) for kw in keywords if kw.strip()]
    return f" {operator} ".join(parts)


def build_combined_query(
    reference_keywords: list[str],
    exploratory_keywords: list[str],
) -> str:
    """参照キーワード(AND)と探索キーワード(OR)を結合する。

    reference_keywords は AND 結合（系統的検索: 固有名詞、日付、場所）、
    exploratory_keywords は OR 結合（探索的検索: 連想的・創造的キーワード）。

    両方が指定された場合は (ref AND) AND (exp OR) の形式で結合する。
    片方のみの場合はそれぞれ単独で構築する。

    Args:
        reference_keywords: 系統的キーワード（AND 結合）
        exploratory_keywords: 探索的キーワード（OR 結合）

    Returns:
        結合された検索クエリ文字列

    Examples:
        >>> build_combined_query(["Salem", "1692"], ["witchcraft", "trial"])
        '(Salem AND 1692) AND (witchcraft OR trial)'
        >>> build_combined_query(["Salem"], [])
        'Salem'
        >>> build_combined_query([], ["ghost", "haunting"])
        'ghost OR haunting'
    """
    ref_query = build_search_query(reference_keywords, operator="AND")
    exp_query = build_search_query(exploratory_keywords, operator="OR")

    if ref_query and exp_query:
        return f"({ref_query}) AND ({exp_query})"
    return ref_query or exp_query
