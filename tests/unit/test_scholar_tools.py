"""Unit tests for Scholar tools - save_structured_report.

Tests for saving structured analysis reports to session state via tool_context.
"""

import json
from unittest.mock import MagicMock

from mystery_agents.tools.scholar_tools import (
    _validate_evidence,
    _validate_evidence_grounding,
    save_structured_report,
)


def _make_ctx(state: dict | None = None) -> MagicMock:
    """事前チェックフラグ付きのモック ToolContext を作成する。"""
    ctx = MagicMock()
    ctx.state = {
        "_inventory_consulted": True,
        "_word_count_verified": True,
        **(state or {}),
    }
    return ctx


class TestSaveStructuredReport:
    """Tests for save_structured_report()."""

    def test_saves_report_to_session_state(self):
        """Should save parsed JSON to tool_context.state['structured_report']."""
        report_data = {
            "title": "The Vanishing Ship",
            "summary": "A ship disappeared",
            "evidence_a": {"source_url": "https://example.com", "source_date": "1842-03-15", "relevant_excerpt": "The ship vanished"},
            "evidence_b": {"source_url": "https://example.com/es", "source_date": "1842-03-20", "relevant_excerpt": "El barco desapareció"},
            "hypothesis": "The ship faked its sinking",
            "alternative_hypotheses": ["Mistaken identity"],
            "classification": "OCC",
            "country_code": "US",
            "region_code": "BOS",
        }
        report_json = json.dumps(report_data)

        mock_tool_context = _make_ctx()

        result = save_structured_report(report_json, mock_tool_context)
        result_data = json.loads(result)

        assert result_data["status"] == "success"
        assert "structured_report" in mock_tool_context.state
        assert mock_tool_context.state["structured_report"] == report_data

    def test_returns_saved_field_names(self):
        """Should return the list of saved field names."""
        report_data = {
            "title": "Test",
            "hypothesis": "Test hypothesis",
            "evidence_a": {},
        }
        report_json = json.dumps(report_data)

        mock_tool_context = _make_ctx()

        result = save_structured_report(report_json, mock_tool_context)
        result_data = json.loads(result)

        assert set(result_data["fields_saved"]) == {"title", "hypothesis", "evidence_a"}

    def test_handles_invalid_json(self):
        """Should return error for invalid JSON input."""
        mock_tool_context = _make_ctx()

        result = save_structured_report("not valid json", mock_tool_context)
        result_data = json.loads(result)

        assert result_data["status"] == "error"
        assert "Invalid JSON" in result_data["error"]
        assert "structured_report" not in mock_tool_context.state

    def test_overwrites_previous_report(self):
        """Should overwrite any previous structured_report in state."""
        mock_tool_context = _make_ctx({
            "structured_report": {"old": "data"},
        })

        new_report = {"title": "New Report", "hypothesis": "New hypothesis"}
        result = save_structured_report(json.dumps(new_report), mock_tool_context)
        result_data = json.loads(result)

        assert result_data["status"] == "success"
        assert mock_tool_context.state["structured_report"] == new_report
        assert "old" not in mock_tool_context.state["structured_report"]

    def test_preserves_all_fields(self):
        """Should preserve all fields from the input JSON including nested objects."""
        report_data = {
            "title": "Test Mystery",
            "summary": "Summary",
            "discrepancy_detected": "Discrepancy",
            "discrepancy_type": "event_outcome",
            "evidence_a": {
                "source_type": "newspaper",
                "source_language": "en",
                "source_title": "Boston Daily",
                "source_date": "1842-03-15",
                "source_url": "https://example.com",
                "relevant_excerpt": "The vessel departed...",
                "location_context": "Boston Harbor",
            },
            "evidence_b": {
                "source_type": "newspaper",
                "source_language": "es",
                "source_title": "Diario de la Marina",
                "source_date": "1842-03-20",
                "source_url": "https://example.com/es",
                "relevant_excerpt": "El buque llegó...",
                "location_context": "Havana",
            },
            "additional_evidence": [],
            "hypothesis": "Hypothesis text",
            "alternative_hypotheses": ["Alt 1", "Alt 2"],
            "confidence_level": "medium",
            "historical_context": {
                "time_period": "Early 19th Century",
                "geographic_scope": ["Boston", "Havana"],
                "relevant_events": ["War of 1812"],
                "key_figures": ["Captain Smith"],
                "political_climate": "Tensions",
            },
            "research_questions": ["What cargo?"],
            "story_hooks": ["Ghost ship"],
            "classification": "OCC",
            "country_code": "US",
            "region_code": "BOS",
        }
        report_json = json.dumps(report_data)

        mock_tool_context = _make_ctx()

        save_structured_report(report_json, mock_tool_context)

        saved = mock_tool_context.state["structured_report"]
        assert saved["evidence_a"]["source_url"] == "https://example.com"
        assert saved["evidence_b"]["source_language"] == "es"
        assert saved["historical_context"]["geographic_scope"] == ["Boston", "Havana"]
        assert saved["classification"] == "OCC"


class TestValidateEvidence:
    """Tests for _validate_evidence() helper."""

    def test_valid_evidence_returns_no_warnings(self):
        """正常な evidence は警告なし。"""
        evidence = {
            "source_url": "https://example.com",
            "relevant_excerpt": "The vessel departed Boston Harbor...",
        }
        warnings = _validate_evidence(evidence, "evidence_a")
        assert warnings == []

    def test_empty_excerpt_returns_warning(self):
        """relevant_excerpt が空文字 → 警告。"""
        evidence = {
            "source_url": "https://example.com",
            "relevant_excerpt": "",
        }
        warnings = _validate_evidence(evidence, "evidence_a")
        assert len(warnings) == 1
        assert "relevant_excerpt" in warnings[0]

    def test_missing_excerpt_returns_warning(self):
        """relevant_excerpt キーがない → 警告。"""
        evidence = {
            "source_url": "https://example.com",
        }
        warnings = _validate_evidence(evidence, "evidence_b")
        assert len(warnings) == 1
        assert "relevant_excerpt" in warnings[0]

    def test_empty_source_url_returns_warning(self):
        """source_url が空文字 → 警告。"""
        evidence = {
            "source_url": "",
            "relevant_excerpt": "Some text",
        }
        warnings = _validate_evidence(evidence, "evidence_a")
        assert len(warnings) == 1
        assert "source_url" in warnings[0]

    def test_missing_source_url_returns_warning(self):
        """source_url キーがない → 警告。"""
        evidence = {
            "relevant_excerpt": "Some text",
        }
        warnings = _validate_evidence(evidence, "evidence_a")
        assert len(warnings) == 1
        assert "source_url" in warnings[0]

    def test_both_empty_returns_two_warnings(self):
        """両方空 → 警告2件。"""
        evidence = {
            "source_url": "",
            "relevant_excerpt": "",
        }
        warnings = _validate_evidence(evidence, "evidence_a")
        assert len(warnings) == 2

    def test_whitespace_only_excerpt_returns_warning(self):
        """空白のみの excerpt → 警告。"""
        evidence = {
            "source_url": "https://example.com",
            "relevant_excerpt": "   ",
        }
        warnings = _validate_evidence(evidence, "evidence_a")
        assert len(warnings) == 1
        assert "relevant_excerpt" in warnings[0]


class TestSaveStructuredReportEvidenceValidation:
    """Tests for evidence validation in save_structured_report()."""

    def test_empty_excerpt_in_evidence_a_gets_fallback(self):
        """evidence_a の excerpt が空 → フォールバック文が挿入される。"""
        report_data = {
            "title": "Test",
            "evidence_a": {
                "source_url": "https://example.com",
                "source_title": "Boston Globe",
                "relevant_excerpt": "",
            },
            "evidence_b": {
                "source_url": "https://example.com/b",
                "relevant_excerpt": "Valid excerpt",
            },
        }
        mock_ctx = _make_ctx()

        result = save_structured_report(json.dumps(report_data), mock_ctx)
        result_data = json.loads(result)

        assert result_data["status"] == "success"
        saved = mock_ctx.state["structured_report"]
        assert saved["evidence_a"]["relevant_excerpt"] == "[See original source: Boston Globe]"
        assert any("replaced with fallback" in w for w in result_data["warnings"])

    def test_empty_excerpt_in_evidence_b_gets_fallback(self):
        """evidence_b の excerpt が空 → フォールバック文が挿入される。"""
        report_data = {
            "title": "Test",
            "evidence_a": {
                "source_url": "https://example.com",
                "relevant_excerpt": "Valid excerpt",
            },
            "evidence_b": {
                "source_url": "https://example.com/b",
                "source_title": "Le Monde",
                "relevant_excerpt": "   ",
            },
        }
        mock_ctx = _make_ctx()

        result = save_structured_report(json.dumps(report_data), mock_ctx)
        result_data = json.loads(result)

        assert result_data["status"] == "success"
        saved = mock_ctx.state["structured_report"]
        assert saved["evidence_b"]["relevant_excerpt"] == "[See original source: Le Monde]"
        assert any("evidence_b" in w and "replaced with fallback" in w for w in result_data["warnings"])

    def test_empty_excerpt_in_additional_evidence_filtered_out(self):
        """additional_evidence の excerpt が空 → フィルタリングされる。"""
        report_data = {
            "title": "Test",
            "evidence_a": {
                "source_url": "https://example.com",
                "relevant_excerpt": "Valid",
            },
            "additional_evidence": [
                {
                    "source_url": "https://example.com/1",
                    "relevant_excerpt": "Good excerpt",
                },
                {
                    "source_url": "https://example.com/2",
                    "relevant_excerpt": "",
                },
                {
                    "source_url": "https://example.com/3",
                    "relevant_excerpt": "Another good one",
                },
            ],
        }
        mock_ctx = _make_ctx()

        result = save_structured_report(json.dumps(report_data), mock_ctx)
        result_data = json.loads(result)

        assert result_data["status"] == "success"
        saved = mock_ctx.state["structured_report"]
        # 空 excerpt の項目がフィルタリングされて2件のみ
        assert len(saved["additional_evidence"]) == 2
        assert all(
            ev["relevant_excerpt"] for ev in saved["additional_evidence"]
        )

    def test_all_additional_evidence_empty_results_in_empty_list(self):
        """全 additional_evidence が空 excerpt → 空リスト。"""
        report_data = {
            "title": "Test",
            "additional_evidence": [
                {"source_url": "https://a.com", "relevant_excerpt": ""},
                {"source_url": "https://b.com", "relevant_excerpt": "  "},
            ],
        }
        mock_ctx = _make_ctx()

        result = save_structured_report(json.dumps(report_data), mock_ctx)
        result_data = json.loads(result)

        assert result_data["status"] == "success"
        assert mock_ctx.state["structured_report"]["additional_evidence"] == []

    def test_valid_report_has_no_warnings(self):
        """全 evidence が正常 → warnings 空リスト。"""
        report_data = {
            "title": "Test",
            "evidence_a": {
                "source_url": "https://example.com",
                "relevant_excerpt": "Excerpt A",
            },
            "evidence_b": {
                "source_url": "https://example.com/b",
                "relevant_excerpt": "Excerpt B",
            },
            "additional_evidence": [
                {
                    "source_url": "https://example.com/c",
                    "relevant_excerpt": "Excerpt C",
                },
            ],
        }
        mock_ctx = _make_ctx()

        result = save_structured_report(json.dumps(report_data), mock_ctx)
        result_data = json.loads(result)

        assert result_data["status"] == "success"
        assert result_data["warnings"] == []


class TestSaveStructuredReportNewFields:
    """source_coverage と confidence_rationale の保存テスト。"""

    def test_source_coverage_preserved(self):
        """source_coverage オブジェクトがそのまま保存される。"""
        report_data = {
            "title": "Test",
            "source_coverage": {
                "apis_searched": ["chronicling_america", "loc", "dpla"],
                "apis_with_results": ["chronicling_america", "loc"],
                "apis_without_results": ["dpla"],
                "known_undigitized_sources": ["Parish registers"],
                "coverage_assessment": "About 20% digitized",
            },
        }
        mock_ctx = _make_ctx()

        result = save_structured_report(json.dumps(report_data), mock_ctx)
        result_data = json.loads(result)

        assert result_data["status"] == "success"
        saved = mock_ctx.state["structured_report"]
        assert saved["source_coverage"]["apis_searched"] == ["chronicling_america", "loc", "dpla"]
        assert saved["source_coverage"]["apis_without_results"] == ["dpla"]
        assert saved["source_coverage"]["coverage_assessment"] == "About 20% digitized"

    def test_confidence_rationale_preserved(self):
        """confidence_rationale 文字列がそのまま保存される。"""
        report_data = {
            "title": "Test",
            "confidence_rationale": "Rated LOW because only one source was found via API.",
        }
        mock_ctx = _make_ctx()

        result = save_structured_report(json.dumps(report_data), mock_ctx)
        result_data = json.loads(result)

        assert result_data["status"] == "success"
        saved = mock_ctx.state["structured_report"]
        assert saved["confidence_rationale"] == "Rated LOW because only one source was found via API."


class TestInventoryConsultedCheck:
    """inventory 参照強制チェックのテスト。"""

    def test_error_when_inventory_not_consulted(self):
        """inventory 未参照で save_structured_report → エラー。"""
        mock_ctx = MagicMock()
        mock_ctx.state = {}  # _inventory_consulted なし

        report_data = {"title": "Test", "hypothesis": "Test"}
        result = save_structured_report(json.dumps(report_data), mock_ctx)
        result_data = json.loads(result)

        assert result_data["status"] == "error"
        assert "get_document_inventory" in result_data["error"]
        assert "structured_report" not in mock_ctx.state

    def test_error_when_inventory_consulted_false(self):
        """_inventory_consulted = False でもエラー。"""
        mock_ctx = MagicMock()
        mock_ctx.state = {"_inventory_consulted": False}

        report_data = {"title": "Test"}
        result = save_structured_report(json.dumps(report_data), mock_ctx)
        result_data = json.loads(result)

        assert result_data["status"] == "error"

    def test_success_when_inventory_consulted(self):
        """_inventory_consulted = True で正常保存。"""
        mock_ctx = _make_ctx()

        report_data = {"title": "Test"}
        result = save_structured_report(json.dumps(report_data), mock_ctx)
        result_data = json.loads(result)

        assert result_data["status"] == "success"

    def test_invalid_json_error_takes_priority_over_inventory(self):
        """不正 JSON のエラーは事前チェック通過後に検出される。"""
        mock_ctx = MagicMock()
        mock_ctx.state = {
            "_inventory_consulted": True,
            "_word_count_verified": True,
        }

        result = save_structured_report("not valid json", mock_ctx)
        result_data = json.loads(result)

        assert result_data["status"] == "error"
        assert "Invalid JSON" in result_data["error"]


class TestEvidenceGrounding:
    """証拠グラウンディング検証のテスト。"""

    def test_matching_url_overwrites_metadata(self):
        """URL が raw_search_results と一致 → title/date を上書き。"""
        mock_ctx = _make_ctx({
            "raw_search_results_en": [{
                "documents": [{
                    "title": "Correct Title From API",
                    "source_url": "https://loc.gov/item/123",
                    "date": "1893-01-15",
                    "source_type": "loc_digital",
                }],
            }],
        })

        report_data = {
            "title": "Test",
            "evidence_a": {
                "source_url": "https://loc.gov/item/123",
                "source_title": "Wrong Title From LLM",
                "source_date": "1893",
                "relevant_excerpt": "Some text",
            },
        }
        result = save_structured_report(json.dumps(report_data), mock_ctx)
        result_data = json.loads(result)

        assert result_data["status"] == "success"
        saved_ev = mock_ctx.state["structured_report"]["evidence_a"]
        # raw データで上書きされている
        assert saved_ev["source_title"] == "Correct Title From API"
        assert saved_ev["source_date"] == "1893-01-15"
        assert saved_ev["archive_source"] == "loc_digital"

    def test_non_matching_url_warns(self):
        """URL が raw_search_results に不在 → 警告。"""
        mock_ctx = _make_ctx({
            "raw_search_results_en": [{
                "documents": [{
                    "title": "Real Doc",
                    "source_url": "https://loc.gov/item/real",
                    "source_type": "loc_digital",
                }],
            }],
        })

        report_data = {
            "title": "Test",
            "evidence_a": {
                "source_url": "https://loc.gov/item/hallucinated",
                "relevant_excerpt": "Made up text",
            },
        }
        result = save_structured_report(json.dumps(report_data), mock_ctx)
        result_data = json.loads(result)

        assert result_data["status"] == "success"
        assert any("source_url not found" in w for w in result_data["warnings"])

    def test_additional_evidence_grounding(self):
        """additional_evidence も URL 照合される。"""
        mock_ctx = _make_ctx({
            "raw_search_results_en": [{
                "documents": [
                    {
                        "title": "Doc A",
                        "source_url": "https://archive.org/details/a",
                        "date": "1900-01-01",
                        "source_type": "internet_archive",
                    },
                    {
                        "title": "Doc B",
                        "source_url": "https://loc.gov/item/b",
                        "date": "1901-06-15",
                        "source_type": "loc_digital",
                    },
                ],
            }],
        })

        report_data = {
            "title": "Test",
            "evidence_a": {
                "source_url": "https://archive.org/details/a",
                "source_title": "Wrong",
                "relevant_excerpt": "Text",
            },
            "evidence_b": {
                "source_url": "https://loc.gov/item/b",
                "source_title": "Also Wrong",
                "relevant_excerpt": "Text",
            },
            "additional_evidence": [
                {
                    "source_url": "https://not-real.com/fake",
                    "relevant_excerpt": "Hallucinated",
                },
            ],
        }
        result = save_structured_report(json.dumps(report_data), mock_ctx)
        result_data = json.loads(result)

        saved = mock_ctx.state["structured_report"]
        assert saved["evidence_a"]["source_title"] == "Doc A"
        assert saved["evidence_a"]["archive_source"] == "internet_archive"
        assert saved["evidence_b"]["source_title"] == "Doc B"
        assert saved["evidence_b"]["archive_source"] == "loc_digital"
        # additional_evidence[0] は URL 不在で警告
        assert any("additional_evidence[0]" in w for w in result_data["warnings"])

    def test_no_raw_search_results_skips_grounding(self):
        """raw_search_results がない場合はグラウンディングをスキップ。"""
        mock_ctx = _make_ctx()  # raw_search_results なし

        report_data = {
            "title": "Test",
            "evidence_a": {
                "source_url": "https://example.com",
                "relevant_excerpt": "Text",
            },
        }
        result = save_structured_report(json.dumps(report_data), mock_ctx)
        result_data = json.loads(result)

        assert result_data["status"] == "success"
        # グラウンディング警告はなし（raw data がないのでスキップ）
        grounding_warnings = [w for w in result_data["warnings"] if "source_url not found" in w]
        assert grounding_warnings == []

    def test_grounding_uses_base_and_lang_keys(self):
        """raw_search_results（ベース）と raw_search_results_{lang} の両方を参照する。"""
        mock_ctx = _make_ctx({
            "raw_search_results": [{
                "documents": [{
                    "title": "Base Doc",
                    "source_url": "https://example.com/base",
                    "date": "1800-01-01",
                    "source_type": "dpla",
                    "keywords_matched": ["keyword"],
                }],
            }],
            "raw_search_results_ja": [{
                "documents": [{
                    "title": "JA Doc",
                    "source_url": "https://ndl.go.jp/ja/1",
                    "date": "1900-05-01",
                    "source_type": "ndl",
                    "keywords_matched": ["キーワード"],
                }],
            }],
        })

        report_data = {
            "title": "Test",
            "evidence_a": {
                "source_url": "https://example.com/base",
                "relevant_excerpt": "Text",
            },
            "evidence_b": {
                "source_url": "https://ndl.go.jp/ja/1",
                "relevant_excerpt": "Text",
            },
        }
        result = save_structured_report(json.dumps(report_data), mock_ctx)
        result_data = json.loads(result)

        saved = mock_ctx.state["structured_report"]
        assert saved["evidence_a"]["archive_source"] == "dpla"
        assert saved["evidence_b"]["archive_source"] == "ndl"
        assert result_data["warnings"] == []


class TestValidateEvidenceGroundingDirect:
    """_validate_evidence_grounding 関数の直接テスト。"""

    def test_empty_evidence(self):
        """evidence がない場合は警告なし。"""
        mock_ctx = _make_ctx({
            "raw_search_results_en": [{
                "documents": [{
                    "title": "Doc",
                    "source_url": "https://example.com",
                    "source_type": "loc_digital",
                }],
            }],
        })

        report_data = {"title": "Test"}
        warnings = _validate_evidence_grounding(report_data, mock_ctx)
        assert warnings == []

    def test_evidence_without_source_url_skipped(self):
        """source_url がない evidence はスキップされる。"""
        mock_ctx = _make_ctx({
            "raw_search_results_en": [{
                "documents": [{
                    "title": "Doc",
                    "source_url": "https://example.com",
                    "source_type": "loc_digital",
                }],
            }],
        })

        report_data = {
            "evidence_a": {"relevant_excerpt": "Text"},
        }
        warnings = _validate_evidence_grounding(report_data, mock_ctx)
        assert warnings == []


class TestWordCountVerifiedCheck:
    """語数検証フラグ強制チェックのテスト。"""

    def test_error_when_word_count_not_verified(self):
        """_word_count_verified 未設定で save_structured_report → エラー。"""
        mock_ctx = MagicMock()
        mock_ctx.state = {"_inventory_consulted": True}

        report_data = {"title": "Test", "hypothesis": "Test"}
        result = save_structured_report(json.dumps(report_data), mock_ctx)
        result_data = json.loads(result)

        assert result_data["status"] == "error"
        assert "count_words" in result_data["error"]
        assert "structured_report" not in mock_ctx.state

    def test_error_when_word_count_verified_false(self):
        """_word_count_verified = False（範囲外）でもエラー。"""
        mock_ctx = MagicMock()
        mock_ctx.state = {"_inventory_consulted": True, "_word_count_verified": False}

        report_data = {"title": "Test"}
        result = save_structured_report(json.dumps(report_data), mock_ctx)
        result_data = json.loads(result)

        assert result_data["status"] == "error"
        assert "count_words" in result_data["error"]

    def test_success_when_word_count_verified(self):
        """_word_count_verified = True で正常保存。"""
        mock_ctx = _make_ctx()

        report_data = {"title": "Test"}
        result = save_structured_report(json.dumps(report_data), mock_ctx)
        result_data = json.loads(result)

        assert result_data["status"] == "success"

    def test_error_message_uses_default_tier_when_unset(self):
        """ティア未設定時はデフォルト（5000/10000）がエラーメッセージに含まれる。"""
        mock_ctx = MagicMock()
        mock_ctx.state = {"_inventory_consulted": True}

        report_data = {"title": "Test"}
        result = save_structured_report(json.dumps(report_data), mock_ctx)
        result_data = json.loads(result)

        assert result_data["status"] == "error"
        assert "5000" in result_data["error"]
        assert "10000" in result_data["error"]

    def test_error_message_uses_reduced_tier(self):
        """Reduced ティア設定時はエラーメッセージに 2500/5000 が含まれる。"""
        mock_ctx = MagicMock()
        mock_ctx.state = {
            "_inventory_consulted": True,
            "_word_count_tier": {"min_words": 2500, "max_words": 5000},
        }

        report_data = {"title": "Test"}
        result = save_structured_report(json.dumps(report_data), mock_ctx)
        result_data = json.loads(result)

        assert result_data["status"] == "error"
        assert "2500" in result_data["error"]
        assert "5000" in result_data["error"]
        # デフォルト値が残っていないことを確認
        assert "10000" not in result_data["error"]
