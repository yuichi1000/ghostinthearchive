"""Multilingual Scholar の生成・instruction 検証テスト。"""

from mystery_agents.agents.language_scholars import (
    NAMED_SCHOLAR_LANGUAGES,
    create_multilingual_scholar,
    get_scholar_config,
)


class TestGetScholarConfig:
    """get_scholar_config() のテスト。"""

    def test_known_language_returns_config(self):
        """SCHOLAR_CONFIGS に定義済みの言語は既存設定を返す。"""
        config = get_scholar_config("en")
        assert config["language_name"] == "English"
        assert config["lang_code"] == "en"
        assert "cultural_perspective" in config

    def test_italian_returns_config(self):
        """IT は新規追加された Named Scholar。"""
        config = get_scholar_config("it")
        assert config["language_name"] == "Italian"
        assert "Microhistory" in config["cultural_perspective"]

    def test_unknown_language_generates_template(self):
        """未知の言語コードは汎用テンプレートを動的生成する。"""
        config = get_scholar_config("pl")
        assert config["language_name"] == "Polish"
        assert config["lang_code"] == "pl"
        assert "Polish" in config["cultural_perspective"]

    def test_unknown_language_has_required_keys(self):
        """動的生成された設定が必須キーを持つ。"""
        config = get_scholar_config("sv")
        assert "language_name" in config
        assert "lang_code" in config
        assert "cultural_perspective" in config


class TestNamedScholarLanguages:
    """NAMED_SCHOLAR_LANGUAGES 定数のテスト。"""

    def test_contains_six_languages(self):
        assert len(NAMED_SCHOLAR_LANGUAGES) == 6

    def test_contains_expected_languages(self):
        expected = {"en", "de", "ja", "fr", "es", "it"}
        assert NAMED_SCHOLAR_LANGUAGES == expected

    def test_nl_and_pt_not_in_named(self):
        """NL, PT は Named ではなく Multilingual に振り分けられる。"""
        assert "nl" not in NAMED_SCHOLAR_LANGUAGES
        assert "pt" not in NAMED_SCHOLAR_LANGUAGES


class TestCreateMultilingualScholar:
    """create_multilingual_scholar() のテスト。"""

    def test_analysis_mode_output_key(self):
        """分析モードの output_key が scholar_analysis_multilingual であること。"""
        scholar = create_multilingual_scholar(["nl", "pt"], mode="analysis")
        assert scholar.output_key == "scholar_analysis_multilingual"

    def test_analysis_mode_name(self):
        scholar = create_multilingual_scholar(["nl", "pt"], mode="analysis")
        assert "scholar_multilingual" in repr(scholar)

    def test_analysis_instruction_references_documents(self):
        """分析 instruction が対象言語の collected_documents を参照する。"""
        scholar = create_multilingual_scholar(["nl", "pt"], mode="analysis")
        assert "{collected_documents_nl}" in scholar.instruction
        assert "{collected_documents_pt}" in scholar.instruction

    def test_analysis_instruction_references_english(self):
        """分析 instruction が英語 collected_documents も参照する。"""
        scholar = create_multilingual_scholar(["nl", "pt"], mode="analysis")
        assert "{collected_documents_en}" in scholar.instruction

    def test_analysis_instruction_contains_language_names(self):
        """分析 instruction に言語名が含まれる。"""
        scholar = create_multilingual_scholar(["nl", "pt"], mode="analysis")
        assert "Dutch" in scholar.instruction
        assert "Portuguese" in scholar.instruction

    def test_debate_mode_has_whiteboard_tool(self):
        """討論モードが append_to_whiteboard ツールを持つ。"""
        from mystery_agents.tools.debate_tools import append_to_whiteboard

        scholar = create_multilingual_scholar(
            ["nl", "pt"],
            mode="debate",
            active_named_langs=["en", "de"],
        )
        assert append_to_whiteboard in scholar.tools

    def test_debate_mode_references_named_analyses(self):
        """討論 instruction が Named Scholar の分析を参照する。"""
        scholar = create_multilingual_scholar(
            ["nl", "pt"],
            mode="debate",
            active_named_langs=["en", "de"],
        )
        assert "{scholar_analysis_en}" in scholar.instruction
        assert "{scholar_analysis_de}" in scholar.instruction

    def test_debate_mode_references_own_analysis(self):
        """討論 instruction が自身の分析 (multilingual) を参照する。"""
        scholar = create_multilingual_scholar(
            ["nl", "pt"],
            mode="debate",
            active_named_langs=["en"],
        )
        assert "{scholar_analysis_multilingual}" in scholar.instruction

    def test_debate_mode_name(self):
        scholar = create_multilingual_scholar(
            ["nl"], mode="debate", active_named_langs=["en"]
        )
        assert "scholar_multilingual_debate" in repr(scholar)

    def test_invalid_mode_raises(self):
        """不正なモードは ValueError。"""
        import pytest

        with pytest.raises(ValueError, match="Unknown mode"):
            create_multilingual_scholar(["nl"], mode="invalid")

    def test_single_language(self):
        """1言語でも正常に生成される。"""
        scholar = create_multilingual_scholar(["pl"], mode="analysis")
        assert "{collected_documents_pl}" in scholar.instruction
        assert "Polish" in scholar.instruction
