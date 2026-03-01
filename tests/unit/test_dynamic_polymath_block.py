"""Unit tests for DynamicPolymathBlock."""

from mystery_agents.agents.dynamic_polymath_block import (
    QUALITY_DOC_THRESHOLD,
    SCHOLAR_WORDS_THRESHOLD,
    TIER_NORMAL,
    TIER_REDUCED,
    _build_analyses_section,
    _count_quality_documents,
    _count_scholar_words,
    assess_source_richness,
    create_dynamic_polymath_block,
)


class TestDynamicPolymathBlockCreation:
    """DynamicPolymathBlock ファクトリのテスト。"""

    def test_creates_base_agent(self):
        """BaseAgent を継承していること。"""
        from google.adk.agents import BaseAgent

        dpb = create_dynamic_polymath_block()
        assert isinstance(dpb, BaseAgent)

    def test_agent_name(self):
        dpb = create_dynamic_polymath_block()
        assert "dynamic_polymath_block" in repr(dpb)

    def test_has_description(self):
        dpb = create_dynamic_polymath_block()
        assert dpb.description
        assert "dynamically" in dpb.description.lower()


class TestBuildAnalysesSection:
    """_build_analyses_section のテスト。"""

    def test_contains_only_active_langs(self):
        """2言語アクティブ時にその2言語のプレースホルダーのみ含まれること。"""
        section = _build_analyses_section(["en", "ja"])
        assert "{scholar_analysis_en}" in section
        assert "{scholar_analysis_ja}" in section
        assert "{scholar_analysis_de}" not in section
        assert "{scholar_analysis_es}" not in section

    def test_single_language(self):
        """1言語のみの場合でも正しくセクションを構築すること。"""
        section = _build_analyses_section(["de"])
        assert "{scholar_analysis_de}" in section
        assert "1 source(s)" in section
        assert "{scholar_analysis_en}" not in section

    def test_includes_language_names(self):
        """言語名がセクションに含まれること。"""
        section = _build_analyses_section(["en", "de"])
        assert "English" in section
        assert "German" in section

    def test_with_multilingual(self):
        """has_multilingual=True で multilingual プレースホルダーが含まれること。"""
        section = _build_analyses_section(["en", "de"], has_multilingual=True)
        assert "{scholar_analysis_en}" in section
        assert "{scholar_analysis_de}" in section
        assert "{scholar_analysis_multilingual}" in section
        assert "Multilingual" in section
        assert "3 source(s)" in section

    def test_without_multilingual(self):
        """has_multilingual=False で multilingual プレースホルダーが含まれないこと。"""
        section = _build_analyses_section(["en", "de"], has_multilingual=False)
        assert "{scholar_analysis_multilingual}" not in section
        assert "2 source(s)" in section

    def test_all_named_languages(self):
        """Named Scholar 全6言語を指定した場合のテスト。"""
        all_langs = ["en", "de", "es", "fr", "ja", "it"]
        section = _build_analyses_section(all_langs)
        for lang in all_langs:
            assert f"{{scholar_analysis_{lang}}}" in section
        assert "6 source(s)" in section


class TestInstructionComposition:
    """動的 instruction 構築の結合テスト。"""

    def test_composed_instruction_contains_debate_whiteboard(self):
        """組み立てた instruction が {debate_whiteboard} を常に含むこと。"""
        from mystery_agents.agents.armchair_polymath import (
            INSTRUCTION_BODY,
            INSTRUCTION_PREAMBLE,
        )

        section = _build_analyses_section(["en"])
        instruction = INSTRUCTION_PREAMBLE + "\n" + section + "\n" + INSTRUCTION_BODY
        assert "{debate_whiteboard}" in instruction

    def test_composed_instruction_contains_preamble(self):
        """組み立てた instruction がペルソナ紹介を含むこと。"""
        from mystery_agents.agents.armchair_polymath import (
            INSTRUCTION_BODY,
            INSTRUCTION_PREAMBLE,
        )

        section = _build_analyses_section(["en"])
        instruction = INSTRUCTION_PREAMBLE + "\n" + section + "\n" + INSTRUCTION_BODY
        assert "Armchair Polymath" in instruction
        assert "sardonic" in instruction


class TestCountQualityDocuments:
    """_count_quality_documents のテスト。"""

    def test_counts_documents_with_keywords_matched(self):
        """keywords_matched が非空の文書のみカウントする。"""
        state = {
            "raw_search_results_en": [
                {
                    "documents": [
                        {"source_url": "https://a.com", "keywords_matched": ["kw1"]},
                        {"source_url": "https://b.com", "keywords_matched": []},
                        {"source_url": "https://c.com", "keywords_matched": ["kw2", "kw3"]},
                    ],
                }
            ],
        }
        assert _count_quality_documents(state) == 2

    def test_deduplicates_by_url(self):
        """同一 URL が複数キーに出現しても1回のみカウントする。"""
        state = {
            "raw_search_results_en": [
                {
                    "documents": [
                        {"source_url": "https://a.com", "keywords_matched": ["kw1"]},
                    ],
                }
            ],
            "raw_search_results_de": [
                {
                    "documents": [
                        {"source_url": "https://a.com", "keywords_matched": ["kw1"]},
                        {"source_url": "https://b.com", "keywords_matched": ["kw2"]},
                    ],
                }
            ],
        }
        assert _count_quality_documents(state) == 2

    def test_empty_state_returns_zero(self):
        """空の state では 0 を返す。"""
        assert _count_quality_documents({}) == 0

    def test_base_and_lang_keys_both_scanned(self):
        """ベースキー raw_search_results と言語別キーの両方を走査する。"""
        state = {
            "raw_search_results": [
                {
                    "documents": [
                        {"source_url": "https://base.com", "keywords_matched": ["kw"]},
                    ],
                }
            ],
            "raw_search_results_ja": [
                {
                    "documents": [
                        {"source_url": "https://ja.com", "keywords_matched": ["kw"]},
                    ],
                }
            ],
        }
        assert _count_quality_documents(state) == 2

    def test_missing_keywords_matched_treated_as_empty(self):
        """keywords_matched キーがない文書はカウントしない。"""
        state = {
            "raw_search_results_en": [
                {
                    "documents": [
                        {"source_url": "https://a.com"},
                    ],
                }
            ],
        }
        assert _count_quality_documents(state) == 0


class TestCountScholarWords:
    """_count_scholar_words のテスト。"""

    def test_sums_words_across_languages(self):
        """複数言語の分析テキストの語数を合算する。"""
        state = {
            "scholar_analysis_en": "word " * 1000,  # 1000 words
            "scholar_analysis_de": "word " * 500,   # 500 words
        }
        assert _count_scholar_words(state, ["en", "de"], False) == 1500

    def test_includes_multilingual_when_flag_set(self):
        """has_multilingual=True の場合、multilingual の語数も加算する。"""
        state = {
            "scholar_analysis_en": "word " * 1000,
            "scholar_analysis_multilingual": "word " * 800,
        }
        assert _count_scholar_words(state, ["en"], True) == 1800

    def test_excludes_multilingual_when_flag_false(self):
        """has_multilingual=False の場合、multilingual は加算しない。"""
        state = {
            "scholar_analysis_en": "word " * 1000,
            "scholar_analysis_multilingual": "word " * 800,
        }
        assert _count_scholar_words(state, ["en"], False) == 1000

    def test_skips_failure_markers(self):
        """失敗マーカーで始まる分析は語数に含めない。"""
        state = {
            "scholar_analysis_en": "word " * 1000,
            "scholar_analysis_de": "INSUFFICIENT_DATA: No data available",
        }
        assert _count_scholar_words(state, ["en", "de"], False) == 1000

    def test_empty_state_returns_zero(self):
        """分析がない場合は 0 を返す。"""
        assert _count_scholar_words({}, [], False) == 0


class TestAssessSourceRichness:
    """assess_source_richness のテスト。"""

    def test_normal_tier_when_enough_documents(self):
        """質の高い文書数が閾値以上なら Normal。"""
        state = {
            "raw_search_results_en": [
                {
                    "documents": [
                        {"source_url": f"https://a.com/{i}", "keywords_matched": ["kw"]}
                        for i in range(QUALITY_DOC_THRESHOLD)
                    ],
                }
            ],
            "scholar_analysis_en": "word " * 100,
        }
        tier = assess_source_richness(state, ["en"], False)
        assert tier == TIER_NORMAL

    def test_normal_tier_when_enough_scholar_words(self):
        """Scholar 語数が閾値以上なら Normal（文書少でも）。"""
        state = {
            "raw_search_results_en": [
                {
                    "documents": [
                        {"source_url": "https://a.com", "keywords_matched": ["kw"]},
                    ],
                }
            ],
            "scholar_analysis_en": "word " * SCHOLAR_WORDS_THRESHOLD,
        }
        tier = assess_source_richness(state, ["en"], False)
        assert tier == TIER_NORMAL

    def test_reduced_tier_when_both_below_threshold(self):
        """文書数・Scholar 語数の両方が閾値未満なら Reduced。"""
        state = {
            "raw_search_results_en": [
                {
                    "documents": [
                        {"source_url": f"https://a.com/{i}", "keywords_matched": ["kw"]}
                        for i in range(QUALITY_DOC_THRESHOLD - 1)
                    ],
                }
            ],
            "scholar_analysis_en": "word " * (SCHOLAR_WORDS_THRESHOLD - 1),
        }
        tier = assess_source_richness(state, ["en"], False)
        assert tier == TIER_REDUCED

    def test_boundary_exactly_at_threshold_is_normal(self):
        """ちょうど閾値の場合は Normal（>= 判定）。"""
        state = {
            "raw_search_results_en": [
                {
                    "documents": [
                        {"source_url": f"https://a.com/{i}", "keywords_matched": ["kw"]}
                        for i in range(QUALITY_DOC_THRESHOLD)
                    ],
                }
            ],
            "scholar_analysis_en": "word " * (SCHOLAR_WORDS_THRESHOLD - 1),
        }
        tier = assess_source_richness(state, ["en"], False)
        assert tier == TIER_NORMAL

    def test_empty_state_returns_reduced(self):
        """空の state では Reduced を返す。"""
        tier = assess_source_richness({}, [], False)
        assert tier == TIER_REDUCED


class TestInstructionCompositionWithTier:
    """ティアによるプレースホルダー置換のテスト。"""

    def test_placeholders_replaced_with_normal_tier(self):
        """Normal ティアでプレースホルダーが 5000/10000 に置換される。"""
        from mystery_agents.agents.armchair_polymath import (
            INSTRUCTION_BODY,
            INSTRUCTION_PREAMBLE,
        )

        section = _build_analyses_section(["en"])
        body = INSTRUCTION_BODY.replace(
            "{__WORD_COUNT_MIN__}", str(TIER_NORMAL.min_words)
        ).replace("{__WORD_COUNT_MAX__}", str(TIER_NORMAL.max_words))
        instruction = INSTRUCTION_PREAMBLE + "\n" + section + "\n" + body
        assert "5000" in instruction or "5,000" in instruction
        assert "10000" in instruction or "10,000" in instruction
        assert "{__WORD_COUNT_MIN__}" not in instruction
        assert "{__WORD_COUNT_MAX__}" not in instruction

    def test_placeholders_replaced_with_reduced_tier(self):
        """Reduced ティアでプレースホルダーが 2500/5000 に置換される。"""
        from mystery_agents.agents.armchair_polymath import (
            INSTRUCTION_BODY,
            INSTRUCTION_PREAMBLE,
        )

        section = _build_analyses_section(["en"])
        body = INSTRUCTION_BODY.replace(
            "{__WORD_COUNT_MIN__}", str(TIER_REDUCED.min_words)
        ).replace("{__WORD_COUNT_MAX__}", str(TIER_REDUCED.max_words))
        instruction = INSTRUCTION_PREAMBLE + "\n" + section + "\n" + body
        assert "2500" in instruction
        assert "{__WORD_COUNT_MIN__}" not in instruction
        assert "{__WORD_COUNT_MAX__}" not in instruction
