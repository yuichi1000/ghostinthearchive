"""Unit tests for bilingual keyword expansion logic."""


from archive_agents.tools.bilingual_search import (
    KEYWORD_PAIRS,
    expand_keywords_bilingual,
    get_all_keywords,
)


class TestExpandKeywordsBilingual:
    """Tests for expand_keywords_bilingual function."""

    def test_expand_english_to_spanish(self):
        """English keyword should expand to include Spanish equivalent."""
        result = expand_keywords_bilingual(["conspiracy"])
        assert "conspiracy" in result["en"]
        assert "conspiración" in result["es"]

    def test_expand_spanish_to_english(self):
        """Spanish keyword should expand to include English equivalent."""
        result = expand_keywords_bilingual(["conspiración"])
        assert "conspiracy" in result["en"]
        assert "conspiración" in result["es"]

    def test_unknown_keyword_added_to_both(self):
        """Unknown keyword should be added to both language lists."""
        result = expand_keywords_bilingual(["unknownword123"])
        assert "unknownword123" in result["en"]
        assert "unknownword123" in result["es"]

    def test_multiple_keywords_expansion(self):
        """Multiple keywords should all be expanded."""
        result = expand_keywords_bilingual(["conspiracy", "shipwreck", "ghost"])
        # English keywords
        assert "conspiracy" in result["en"]
        assert "shipwreck" in result["en"]
        assert "ghost" in result["en"]
        # Spanish equivalents
        assert "conspiración" in result["es"]
        assert "naufragio" in result["es"]
        assert "fantasma" in result["es"]

    def test_case_insensitivity(self):
        """Keyword lookup should be case-insensitive."""
        result_lower = expand_keywords_bilingual(["conspiracy"])
        result_upper = expand_keywords_bilingual(["CONSPIRACY"])
        result_mixed = expand_keywords_bilingual(["CoNsPiRaCy"])

        assert result_lower["en"] == result_upper["en"]
        assert result_lower["es"] == result_upper["es"]
        assert result_lower["en"] == result_mixed["en"]

    def test_whitespace_trimming(self):
        """Keywords should have whitespace trimmed."""
        result = expand_keywords_bilingual(["  conspiracy  "])
        assert "conspiracy" in result["en"]
        assert "conspiración" in result["es"]

    def test_empty_list(self):
        """Empty keyword list should return empty result lists."""
        result = expand_keywords_bilingual([])
        assert result["en"] == []
        assert result["es"] == []

    def test_mixed_languages_input(self):
        """Mix of English and Spanish keywords should work."""
        result = expand_keywords_bilingual(["conspiracy", "naufragio"])
        # Both should have English
        assert "conspiracy" in result["en"]
        assert "shipwreck" in result["en"]
        # Both should have Spanish
        assert "conspiración" in result["es"]
        assert "naufragio" in result["es"]

    def test_no_duplicates_in_output(self):
        """Output should not contain duplicates."""
        # "murder" and "assassination" both map to "asesinato"
        result = expand_keywords_bilingual(["murder", "assassination"])
        # Spanish list should only have "asesinato" once
        assert result["es"].count("asesinato") == 1

    def test_proper_nouns_passthrough(self):
        """Proper nouns not in dictionary should pass through to both."""
        result = expand_keywords_bilingual(["Boston", "Havana"])
        assert "boston" in result["en"]
        assert "havana" in result["en"]
        assert "boston" in result["es"]
        assert "havana" in result["es"]


class TestGetAllKeywords:
    """Tests for get_all_keywords function."""

    def test_returns_copy(self):
        """get_all_keywords should return a copy, not the original."""
        keywords1 = get_all_keywords()
        keywords2 = get_all_keywords()
        keywords1["test"] = "test"
        assert "test" not in keywords2

    def test_contains_core_keywords(self):
        """Should contain essential keyword pairs."""
        keywords = get_all_keywords()
        # Core mystery terms
        assert "conspiracy" in keywords
        assert "mystery" in keywords
        assert "secret" in keywords
        # Maritime terms
        assert "shipwreck" in keywords
        assert "smuggling" in keywords
        # Folklore terms
        assert "ghost" in keywords
        assert "legend" in keywords
        assert "curse" in keywords

    def test_keyword_values_are_spanish(self):
        """Values in the dictionary should be Spanish translations."""
        keywords = get_all_keywords()
        assert keywords["conspiracy"] == "conspiración"
        assert keywords["ghost"] == "fantasma"
        assert keywords["treasure"] == "tesoro"


class TestKeywordPairsCompleteness:
    """Tests to verify keyword coverage for the project's themes."""

    def test_maritime_coverage(self):
        """Should have comprehensive maritime vocabulary."""
        maritime_terms = ["smuggling", "piracy", "shipwreck", "mutiny", "cargo", "vessel", "harbor", "captain"]
        for term in maritime_terms:
            assert term in KEYWORD_PAIRS, f"Missing maritime term: {term}"

    def test_folklore_coverage(self):
        """Should have comprehensive folklore vocabulary."""
        folklore_terms = [
            "ghost", "legend", "curse", "superstition", "haunted",
            "witch", "demon", "omen", "prophecy"
        ]
        for term in folklore_terms:
            assert term in KEYWORD_PAIRS, f"Missing folklore term: {term}"

    def test_political_coverage(self):
        """Should have political/diplomatic vocabulary."""
        political_terms = ["rebellion", "treaty", "exile", "diplomat", "ambassador"]
        for term in political_terms:
            assert term in KEYWORD_PAIRS, f"Missing political term: {term}"

    def test_crime_coverage(self):
        """Should have crime-related vocabulary."""
        crime_terms = ["assassination", "murder", "spy", "espionage", "fugitive", "theft"]
        for term in crime_terms:
            assert term in KEYWORD_PAIRS, f"Missing crime term: {term}"
