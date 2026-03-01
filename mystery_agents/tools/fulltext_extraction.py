"""全文テキストのキーワード指向抽出モジュール。

先頭切り詰めに代わり、全文中からテーマキーワードにヒットする箇所を検索し、
前後コンテキストを抽出して結合する。Scholar が受け取るテキストの分析品質を向上させる。
"""


def extract_keyword_passages(
    full_text: str,
    keywords: list[str],
    *,
    context_chars: int = 500,
    max_output_chars: int = 5000,
    separator: str = "\n[...]\n",
) -> str:
    """全文からキーワード周辺のパッセージを抽出して結合する。

    Args:
        full_text: 全文テキスト
        keywords: 抽出対象のキーワードリスト
        context_chars: 各ヒットの前後に含めるコンテキスト文字数
        max_output_chars: 出力の最大文字数
        separator: 非連続パッセージ間の区切り文字列

    Returns:
        キーワード周辺のパッセージを結合した文字列。
        短いテキストはそのまま返す。キーワードがヒットしない場合は先頭にフォールバック。
    """
    if not full_text:
        return ""

    # 短いテキストはそのまま返す
    if len(full_text) <= max_output_chars:
        return full_text

    # キーワードが空 → 先頭フォールバック
    if not keywords:
        return full_text[:max_output_chars]

    # 全文を小文字化してキーワードの出現位置を収集
    text_lower = full_text.lower()
    hit_positions: list[int] = []
    for kw in keywords:
        kw_lower = kw.lower()
        if not kw_lower:
            continue
        start = 0
        while True:
            pos = text_lower.find(kw_lower, start)
            if pos == -1:
                break
            hit_positions.append(pos)
            start = pos + 1

    # ヒットなし → 先頭フォールバック
    if not hit_positions:
        return full_text[:max_output_chars]

    # 各ヒット位置を ±context_chars に拡張して範囲を生成
    text_len = len(full_text)
    ranges: list[tuple[int, int]] = []
    for pos in hit_positions:
        r_start = max(0, pos - context_chars)
        r_end = min(text_len, pos + context_chars)
        ranges.append((r_start, r_end))

    # ソート → 重複・隣接をマージ
    ranges.sort()
    merged: list[tuple[int, int]] = [ranges[0]]
    for r_start, r_end in ranges[1:]:
        prev_start, prev_end = merged[-1]
        if r_start <= prev_end:
            merged[-1] = (prev_start, max(prev_end, r_end))
        else:
            merged.append((r_start, r_end))

    # 元テキスト（大文字保持）からパッセージを切り出し
    passages: list[str] = []
    total_len = 0
    for i, (r_start, r_end) in enumerate(merged):
        passage = full_text[r_start:r_end]
        # セパレータ分も含めた累積長を計算
        added_len = len(passage) + (len(separator) if i > 0 else 0)
        if total_len + added_len > max_output_chars:
            # 残り文字数分だけ切り出して終了
            remaining = max_output_chars - total_len - (len(separator) if i > 0 else 0)
            if remaining > 0:
                passages.append(passage[:remaining])
            break
        passages.append(passage)
        total_len += added_len

    return separator.join(passages)


def build_extraction_keywords(
    search_keywords: list[str],
    *,
    title: str = "",
    subjects: list[str] | None = None,
    min_word_length: int = 4,
) -> list[str]:
    """検索キーワード + ドキュメントメタデータから抽出用キーワードを構築する。

    Args:
        search_keywords: ベースとなる検索キーワード
        title: ドキュメントのタイトル（スペース分割で単語を追加）
        subjects: サブジェクトタグのリスト
        min_word_length: タイトルから追加する単語の最小文字数

    Returns:
        重複除去済みのキーワードリスト（大文字小文字を無視して重複排除）
    """
    seen_lower: set[str] = set()
    result: list[str] = []

    def _add(keyword: str) -> None:
        kw_stripped = keyword.strip()
        if not kw_stripped:
            return
        lower = kw_stripped.lower()
        if lower not in seen_lower:
            seen_lower.add(lower)
            result.append(kw_stripped)

    # 検索キーワードをベースに追加
    for kw in search_keywords:
        _add(kw)

    # タイトルをスペース分割 → 十分な長さの単語を追加
    if title:
        for word in title.split():
            if len(word) >= min_word_length:
                _add(word)

    # subjects リストをそのまま追加
    if subjects:
        for subj in subjects:
            _add(subj)

    return result
