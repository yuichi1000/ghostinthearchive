"""Tests for search query builder utility."""

from mystery_agents.tools.search_utils import build_combined_query, build_search_query


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

    def test_and_operator(self):
        assert build_search_query(["Salem", "1692"], operator="AND") == "Salem AND 1692"

    def test_and_operator_with_phrase(self):
        result = build_search_query(["Salem witch trials", "1692"], operator="AND")
        assert result == '"Salem witch trials" AND 1692'


class TestBuildCombinedQuery:
    def test_both_ref_and_exp(self):
        result = build_combined_query(["Salem", "1692"], ["witchcraft", "trial"])
        assert result == "(Salem AND 1692) AND (witchcraft OR trial)"

    def test_ref_only(self):
        result = build_combined_query(["Salem"], [])
        assert result == "Salem"

    def test_exp_only(self):
        result = build_combined_query([], ["ghost", "haunting"])
        assert result == "ghost OR haunting"

    def test_both_empty(self):
        result = build_combined_query([], [])
        assert result == ""

    def test_phrase_in_ref(self):
        result = build_combined_query(["Salem witch trials"], ["haunting"])
        assert result == '("Salem witch trials") AND (haunting)'

    def test_phrase_in_exp(self):
        result = build_combined_query(["Salem"], ["Bell Witch", "ghost"])
        assert result == '(Salem) AND ("Bell Witch" OR ghost)'

    def test_single_ref_single_exp(self):
        result = build_combined_query(["Salem"], ["witchcraft"])
        assert result == "(Salem) AND (witchcraft)"
