"""Unit tests for mystery_agents/tools/fulltext_extraction.py."""

from mystery_agents.tools.fulltext_extraction import (
    build_extraction_keywords,
    extract_keyword_passages,
)


class TestExtractKeywordPassages:
    """extract_keyword_passages のテスト。"""

    def test_short_text_returned_as_is(self):
        """max_output_chars 以下のテキストはそのまま返す。"""
        text = "Short text about ghosts."
        result = extract_keyword_passages(text, ["ghosts"], max_output_chars=5000)
        assert result == text

    def test_single_keyword_single_hit(self):
        """単一キーワード・単一ヒットでコンテキストが正しく抽出される。"""
        # "ghost" を10000文字目付近に配置
        text = "A" * 10000 + "The ghost appeared." + "B" * 10000
        result = extract_keyword_passages(
            text, ["ghost"], context_chars=50, max_output_chars=5000
        )
        assert "ghost" in result
        assert len(result) <= 5000
        # 先頭の "AAA..." ではなくキーワード周辺が抽出される
        assert result != text[:5000]

    def test_multiple_keywords_multiple_hits(self):
        """複数キーワード・複数ヒットで全ヒットが網羅される。"""
        text = "A" * 5000 + "ghost" + "A" * 5000 + "haunted" + "A" * 5000
        result = extract_keyword_passages(
            text, ["ghost", "haunted"], context_chars=100, max_output_chars=5000
        )
        assert "ghost" in result
        assert "haunted" in result

    def test_overlapping_ranges_merged(self):
        """近接キーワードが1つのパッセージに統合される。"""
        text = "A" * 5000 + "ghost haunted" + "A" * 5000
        result = extract_keyword_passages(
            text, ["ghost", "haunted"], context_chars=100, max_output_chars=5000
        )
        assert "ghost haunted" in result
        # セパレータが含まれない（マージされている）
        assert "[...]" not in result

    def test_no_hits_falls_back_to_head(self):
        """キーワードがヒットしない場合は先頭にフォールバック。"""
        text = "A" * 10000
        result = extract_keyword_passages(
            text, ["ghost"], max_output_chars=5000
        )
        assert result == "A" * 5000

    def test_empty_keywords_falls_back_to_head(self):
        """キーワードが空の場合は先頭にフォールバック。"""
        text = "A" * 10000
        result = extract_keyword_passages(text, [], max_output_chars=5000)
        assert result == "A" * 5000

    def test_max_output_chars_limit(self):
        """出力が max_output_chars を超えない。"""
        text = "ghost " * 10000  # キーワードが大量にヒットする
        result = extract_keyword_passages(
            text, ["ghost"], context_chars=500, max_output_chars=3000
        )
        assert len(result) <= 3000

    def test_case_insensitive_matching(self):
        """大文字小文字を無視してマッチする。"""
        text = "A" * 5000 + "The GHOST appeared here." + "B" * 5000
        result = extract_keyword_passages(
            text, ["ghost"], context_chars=50, max_output_chars=5000
        )
        # 元の大文字が保持される
        assert "GHOST" in result

    def test_japanese_text(self):
        """日本語テキストで CJK キーワードが正常動作する。"""
        text = "あ" * 5000 + "怪談の記録がここに残されている" + "い" * 5000
        result = extract_keyword_passages(
            text, ["怪談"], context_chars=100, max_output_chars=5000
        )
        assert "怪談" in result

    def test_separator_between_non_contiguous_passages(self):
        """非連続パッセージ間に [...] 区切りが入る。"""
        text = "A" * 5000 + "ghost" + "B" * 5000 + "haunted" + "C" * 5000
        result = extract_keyword_passages(
            text, ["ghost", "haunted"], context_chars=100, max_output_chars=15000
        )
        assert "[...]" in result

    def test_empty_text_returns_empty(self):
        """空テキストは空文字列を返す。"""
        assert extract_keyword_passages("", ["ghost"]) == ""

    def test_preserves_original_casing(self):
        """抽出されたパッセージは元テキストの大文字小文字を保持する。"""
        text = "X" * 6000 + "The Ghost of Salem was REAL." + "Y" * 6000
        result = extract_keyword_passages(
            text, ["ghost"], context_chars=50, max_output_chars=5000
        )
        assert "Ghost" in result
        assert "REAL" in result


class TestBuildExtractionKeywords:
    """build_extraction_keywords のテスト。"""

    def test_search_keywords_only(self):
        """検索キーワードのみ。"""
        result = build_extraction_keywords(["ghost", "haunted"])
        assert result == ["ghost", "haunted"]

    def test_title_words_added(self):
        """タイトルから十分長い単語が追加される。"""
        result = build_extraction_keywords(
            ["ghost"], title="The Haunted House of Salem"
        )
        assert "ghost" in result
        assert "Haunted" in result
        assert "House" in result
        assert "Salem" in result
        # "The" (3文字) と "of" (2文字) は除外
        assert "The" not in result
        assert "of" not in result

    def test_subjects_added(self):
        """subjects リストが追加される。"""
        result = build_extraction_keywords(
            ["ghost"], subjects=["Folklore", "Massachusetts"]
        )
        assert "ghost" in result
        assert "Folklore" in result
        assert "Massachusetts" in result

    def test_deduplication_case_insensitive(self):
        """大文字小文字を無視して重複除去される。"""
        result = build_extraction_keywords(
            ["Ghost"], title="ghost story", subjects=["GHOST"]
        )
        # "Ghost" のみ（最初に追加されたもの）
        assert len([kw for kw in result if kw.lower() == "ghost"]) == 1

    def test_short_words_filtered(self):
        """min_word_length 未満のタイトル単語はフィルタリングされる。"""
        result = build_extraction_keywords(
            [], title="A Big Cat", min_word_length=4
        )
        # "A" (1文字), "Big" (3文字), "Cat" (3文字) すべて除外
        assert result == []

    def test_empty_inputs(self):
        """全入力が空の場合は空リストを返す。"""
        result = build_extraction_keywords([])
        assert result == []

    def test_combined(self):
        """検索キーワード + タイトル + subjects の組み合わせ。"""
        result = build_extraction_keywords(
            ["Salem", "witch"],
            title="The Salem Witch Trials",
            subjects=["History", "witch"],
        )
        assert "Salem" in result
        assert "witch" in result
        assert "Witch" not in result  # "witch" と重複
        assert "Trials" in result
        assert "History" in result
        assert "The" not in result
