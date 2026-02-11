"""Tests for search query builder utility."""

from mystery_agents.tools.search_utils import build_search_query


class TestBuildSearchQuery:
    def test_single_word_keywords(self):
        assert build_search_query(["ghost", "haunting"]) == "ghost OR haunting"

    def test_multi_word_phrase_is_quoted(self):
        assert build_search_query(["Bell Witch", "Tennessee"]) == '"Bell Witch" OR Tennessee'

    def test_mixed_phrases_and_words(self):
        result = build_search_query(["Bell Witch", "Adams Tennessee", "poltergeist"])
        assert '"Bell Witch"' in result
        assert '"Adams Tennessee"' in result
        assert "poltergeist" in result

    def test_empty_keywords_filtered(self):
        assert build_search_query(["ghost", "", "  "]) == "ghost"

    def test_empty_list(self):
        assert build_search_query([]) == ""
