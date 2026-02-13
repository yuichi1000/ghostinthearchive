"""Unit tests for Translator Agent Factory."""

import pytest

from translator_agents.agents.translator import (
    TRANSLATOR_CONFIGS,
    _BASE_TRANSLATOR_INSTRUCTION,
    create_all_translators,
    create_translator,
    translator_agent,
)


class TestCreateTranslator:
    """Tests for create_translator factory function."""

    def test_returns_agent_instance(self):
        """Should return an agent-like object for a valid language."""
        agent = create_translator("ja")
        assert agent is not None

    def test_raises_for_unsupported_language(self):
        """Should raise ValueError for unsupported language codes."""
        with pytest.raises(ValueError, match="Unsupported target language: zh"):
            create_translator("zh")

    def test_raises_for_english(self):
        """Should raise ValueError for English (source language, not a translation target)."""
        with pytest.raises(ValueError, match="Unsupported target language: en"):
            create_translator("en")

    def test_each_language_returns_distinct_agent(self):
        """Should return a different agent object for each language."""
        agents = [create_translator(lang) for lang in TRANSLATOR_CONFIGS]
        # id() が異なるインスタンスであること
        agent_ids = [id(a) for a in agents]
        assert len(set(agent_ids)) == len(TRANSLATOR_CONFIGS)


class TestCreateAllTranslators:
    """Tests for create_all_translators function."""

    def test_returns_all_six_languages(self):
        """Should return translators for all 6 target languages."""
        translators = create_all_translators()
        assert set(translators.keys()) == {"ja", "es", "de", "fr", "nl", "pt"}

    def test_returns_six_distinct_agents(self):
        """Should return 6 distinct agent instances."""
        translators = create_all_translators()
        agent_ids = [id(a) for a in translators.values()]
        assert len(set(agent_ids)) == 6


class TestBackwardCompatibility:
    """Tests for backward compatibility with existing code."""

    def test_translator_agent_exists(self):
        """Should export translator_agent for backward compat."""
        assert translator_agent is not None


class TestTranslatorConfigs:
    """Tests for TRANSLATOR_CONFIGS structure."""

    def test_all_configs_have_required_keys(self):
        """Each config should have language_name, tone, speculation, terminology."""
        required_keys = {"language_name", "tone", "speculation", "terminology"}
        for lang, config in TRANSLATOR_CONFIGS.items():
            assert required_keys.issubset(config.keys()), (
                f"Missing keys in {lang}: {required_keys - config.keys()}"
            )

    def test_six_languages_configured(self):
        """Should have exactly 6 language configs."""
        assert len(TRANSLATOR_CONFIGS) == 6
        assert set(TRANSLATOR_CONFIGS.keys()) == {"ja", "es", "de", "fr", "nl", "pt"}

    def test_base_instruction_has_required_placeholders(self):
        """Base instruction template should have all required format placeholders."""
        for placeholder in ["{language_name}", "{tone}", "{terminology}", "{speculation}"]:
            assert placeholder in _BASE_TRANSLATOR_INSTRUCTION

    def test_instruction_formats_without_error(self):
        """Should format instruction with all language configs without KeyError."""
        for lang, config in TRANSLATOR_CONFIGS.items():
            result = _BASE_TRANSLATOR_INSTRUCTION.format(
                language_name=config["language_name"],
                tone=config["tone"],
                terminology=config["terminology"],
                speculation=config["speculation"],
            )
            assert config["language_name"] in result

    def test_japanese_instruction_contains_katakana_guidance(self):
        """Japanese config should mention katakana transliteration."""
        config = TRANSLATOR_CONFIGS["ja"]
        formatted = _BASE_TRANSLATOR_INSTRUCTION.format(
            language_name=config["language_name"],
            tone=config["tone"],
            terminology=config["terminology"],
            speculation=config["speculation"],
        )
        assert "katakana" in formatted

    def test_spanish_instruction_contains_speculation_examples(self):
        """Spanish config should include 'Se dice que' example."""
        config = TRANSLATOR_CONFIGS["es"]
        formatted = _BASE_TRANSLATOR_INSTRUCTION.format(
            language_name=config["language_name"],
            tone=config["tone"],
            terminology=config["terminology"],
            speculation=config["speculation"],
        )
        assert "Se dice que" in formatted

    def test_german_instruction_contains_unheimlichkeit(self):
        """German config should mention Unheimlichkeit."""
        config = TRANSLATOR_CONFIGS["de"]
        formatted = _BASE_TRANSLATOR_INSTRUCTION.format(
            language_name=config["language_name"],
            tone=config["tone"],
            terminology=config["terminology"],
            speculation=config["speculation"],
        )
        assert "Unheimlichkeit" in formatted

    def test_instruction_specifies_bare_field_names(self):
        """All formatted instructions should specify NO suffix output."""
        for lang, config in TRANSLATOR_CONFIGS.items():
            formatted = _BASE_TRANSLATOR_INSTRUCTION.format(
                language_name=config["language_name"],
                tone=config["tone"],
                terminology=config["terminology"],
                speculation=config["speculation"],
            )
            assert "NO suffix like _ja or _es" in formatted, f"Missing for {lang}"

    def test_portuguese_uses_brazilian_portuguese(self):
        """Portuguese config should specify Brazilian Portuguese."""
        assert TRANSLATOR_CONFIGS["pt"]["language_name"] == "Brazilian Portuguese"
