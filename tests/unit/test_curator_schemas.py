"""Unit tests for curator_agents/schemas.py.

カテゴリ定義の一元化、LLM 出力のスキーマ検証、ユーティリティ関数をテストする。
"""

import pytest

from curator_agents.schemas import (
    ALL_CATEGORIES,
    ThemeSuggestion,
    build_category_prompt_section,
    strip_markdown_codeblock,
    validate_suggestions,
)
from mystery_agents.schemas.mystery_id import ClassificationCode


class TestAllCategories:
    """ALL_CATEGORIES が ClassificationCode enum と一致することを検証。"""

    def test_derived_from_classification_code(self):
        expected = [code.value for code in ClassificationCode]
        assert ALL_CATEGORIES == expected


class TestThemeSuggestion:
    """ThemeSuggestion Pydantic モデルの検証。"""

    def test_valid_suggestion(self):
        data = {
            "theme": "Test theme",
            "description": "Test description",
            "category": "HIS",
        }
        suggestion = ThemeSuggestion.model_validate(data)
        assert suggestion.theme == "Test theme"
        assert suggestion.category == "HIS"

    def test_invalid_category_rejected(self):
        data = {
            "theme": "Test theme",
            "description": "Test description",
            "category": "INVALID",
        }
        with pytest.raises(Exception):
            ThemeSuggestion.model_validate(data)

    def test_missing_theme_rejected(self):
        data = {
            "description": "Test description",
            "category": "HIS",
        }
        with pytest.raises(Exception):
            ThemeSuggestion.model_validate(data)

    def test_missing_description_rejected(self):
        data = {
            "theme": "Test theme",
            "category": "HIS",
        }
        with pytest.raises(Exception):
            ThemeSuggestion.model_validate(data)


class TestValidateSuggestions:
    """validate_suggestions() のテスト。"""

    def test_all_valid_entries_returned(self):
        raw = [
            {"theme": "Theme A", "description": "Desc A", "category": "HIS"},
            {"theme": "Theme B", "description": "Desc B", "category": "OCC"},
        ]
        result = validate_suggestions(raw)
        assert len(result) == 2
        assert result[0]["theme"] == "Theme A"
        assert result[1]["category"] == "OCC"

    def test_invalid_entry_excluded(self):
        raw = [
            {"theme": "Good", "description": "Valid", "category": "FLK"},
            {"theme": "Bad", "description": "Invalid category", "category": "XXX"},
            {"theme": "Also Good", "description": "Valid too", "category": "CRM"},
        ]
        result = validate_suggestions(raw)
        assert len(result) == 2
        assert result[0]["theme"] == "Good"
        assert result[1]["theme"] == "Also Good"

    def test_empty_list_returns_empty(self):
        assert validate_suggestions([]) == []

    def test_all_invalid_returns_empty(self):
        raw = [
            {"theme": "Bad 1", "category": "XXX"},
            {"no_theme": "Bad 2"},
        ]
        result = validate_suggestions(raw)
        assert result == []

    def test_missing_key_excluded(self):
        raw = [
            {"theme": "No description", "category": "HIS"},
        ]
        result = validate_suggestions(raw)
        assert result == []

    def test_logs_warning_for_invalid_entry(self, caplog):
        import logging
        with caplog.at_level(logging.WARNING, logger="curator_agents.schemas"):
            validate_suggestions([{"bad": "data"}])
        assert "テーマ提案 #0 を除外" in caplog.text


class TestBuildCategoryPromptSection:
    """build_category_prompt_section() のテスト。"""

    def test_contains_all_classification_codes(self):
        result = build_category_prompt_section()
        for code in ClassificationCode:
            assert code.value in result

    def test_contains_english_descriptions(self):
        result = build_category_prompt_section()
        assert "Historical record discrepancies" in result
        assert "Local traditions" in result
        assert "Place-bound anomalies" in result

    def test_format_is_bullet_list(self):
        result = build_category_prompt_section()
        lines = result.strip().split("\n")
        assert len(lines) == 8
        for line in lines:
            assert line.startswith("- ")


class TestStripMarkdownCodeblock:
    """strip_markdown_codeblock() のテスト。"""

    def test_strips_json_codeblock(self):
        text = '```json\n[{"theme": "test"}]\n```'
        result = strip_markdown_codeblock(text)
        assert result == '[{"theme": "test"}]'

    def test_strips_generic_codeblock(self):
        text = '```\n[{"theme": "test"}]\n```'
        result = strip_markdown_codeblock(text)
        assert result == '[{"theme": "test"}]'

    def test_no_codeblock_returns_stripped(self):
        text = '  [{"theme": "test"}]  '
        result = strip_markdown_codeblock(text)
        assert result == '[{"theme": "test"}]'

    def test_surrounding_text_removed(self):
        text = 'Here is the JSON:\n```json\n[{"a": 1}]\n```\nDone.'
        result = strip_markdown_codeblock(text)
        assert result == '[{"a": 1}]'

    def test_empty_string(self):
        assert strip_markdown_codeblock("") == ""

    def test_whitespace_only(self):
        assert strip_markdown_codeblock("   \n  ") == ""
