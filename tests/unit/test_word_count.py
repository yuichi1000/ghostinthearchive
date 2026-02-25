"""count_words ツールのユニットテスト。"""

import json

from mystery_agents.tools.word_count import count_words


class TestCountWords:
    """count_words() の基本動作検証。"""

    def test_counts_words_correctly(self):
        """単語数を正しくカウントすること。"""
        result = json.loads(count_words("one two three four five"))
        assert result["word_count"] == 5

    def test_empty_text(self):
        """空文字列は 0 語を返すこと。"""
        result = json.loads(count_words(""))
        assert result["word_count"] == 0

    def test_no_range_specified(self):
        """min/max 未指定時は範囲チェックしないこと。"""
        result = json.loads(count_words("hello world"))
        assert result["word_count"] == 2
        assert "within_range" not in result

    def test_within_range(self):
        """範囲内の場合 within_range が True であること。"""
        text = " ".join(["word"] * 100)
        result = json.loads(count_words(text, min_words=50, max_words=200))
        assert result["within_range"] is True
        assert result["word_count"] == 100

    def test_below_minimum(self):
        """最小語数未満の場合 within_range が False であること。"""
        text = " ".join(["word"] * 10)
        result = json.loads(count_words(text, min_words=50, max_words=200))
        assert result["within_range"] is False
        assert "Too short" in result["message"]

    def test_above_maximum(self):
        """最大語数超過の場合 within_range が False であること。"""
        text = " ".join(["word"] * 300)
        result = json.loads(count_words(text, min_words=50, max_words=200))
        assert result["within_range"] is False
        assert "Too long" in result["message"]

    def test_at_exact_minimum(self):
        """ちょうど最小語数の場合 within_range が True であること。"""
        text = " ".join(["word"] * 50)
        result = json.loads(count_words(text, min_words=50, max_words=200))
        assert result["within_range"] is True

    def test_at_exact_maximum(self):
        """ちょうど最大語数の場合 within_range が True であること。"""
        text = " ".join(["word"] * 200)
        result = json.loads(count_words(text, min_words=50, max_words=200))
        assert result["within_range"] is True

    def test_returns_json_string(self):
        """戻り値が有効な JSON 文字列であること。"""
        result = count_words("hello world", min_words=1, max_words=10)
        parsed = json.loads(result)
        assert isinstance(parsed, dict)
        assert "word_count" in parsed

    def test_polymath_range(self):
        """Polymath の 5,000-10,000 語範囲で正しく判定すること。"""
        text = " ".join(["word"] * 7000)
        result = json.loads(count_words(text, min_words=5000, max_words=10000))
        assert result["within_range"] is True
        assert result["word_count"] == 7000

    def test_storyteller_range(self):
        """Storyteller の 2,000-3,500 語範囲で正しく判定すること。"""
        text = " ".join(["word"] * 2500)
        result = json.loads(count_words(text, min_words=2000, max_words=3500))
        assert result["within_range"] is True
        assert result["word_count"] == 2500
