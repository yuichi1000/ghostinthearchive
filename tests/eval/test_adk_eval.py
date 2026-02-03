"""ADK Evaluation tests using the official evaluation framework.

These tests use Google ADK's AgentEvaluator to assess agent quality
against Golden Datasets. They require Vertex AI API access.

Run with:
    pytest tests/eval/test_adk_eval.py -v -m adk_eval

Or use ADK CLI directly:
    adk eval archive_agents tests/eval/eval_sets/
"""

import json
import os
from pathlib import Path

import pytest

# Skip all tests in this module if ADK evaluation is not available
pytestmark = [
    pytest.mark.adk_eval,
    pytest.mark.slow,
]


EVAL_SETS_DIR = Path(__file__).parent / "eval_sets"
CONFIG_FILE = Path(__file__).parent / "test_config.json"


def load_eval_config():
    """Load evaluation configuration."""
    with open(CONFIG_FILE) as f:
        return json.load(f)


def get_eval_set_files():
    """Get all evaluation set JSON files."""
    return list(EVAL_SETS_DIR.glob("*.json"))


class TestADKEvaluationSetup:
    """Tests to verify ADK evaluation infrastructure is properly set up."""

    def test_eval_sets_directory_exists(self):
        """eval_sets directory should exist."""
        assert EVAL_SETS_DIR.exists()
        assert EVAL_SETS_DIR.is_dir()

    def test_config_file_exists(self):
        """test_config.json should exist."""
        assert CONFIG_FILE.exists()

    def test_config_file_valid_json(self):
        """test_config.json should be valid JSON."""
        config = load_eval_config()
        assert "criteria" in config
        assert "tool_trajectory_avg_score" in config["criteria"]

    def test_librarian_eval_exists(self):
        """librarian_eval.json should exist."""
        librarian_eval = EVAL_SETS_DIR / "librarian_eval.json"
        assert librarian_eval.exists()

    def test_librarian_eval_valid_structure(self):
        """librarian_eval.json should have valid ADK eval structure."""
        with open(EVAL_SETS_DIR / "librarian_eval.json") as f:
            data = json.load(f)

        assert "eval_set_id" in data
        assert "evals" in data
        assert len(data["evals"]) > 0

        # Check first eval has required fields
        first_eval = data["evals"][0]
        assert "eval_id" in first_eval
        assert "conversation" in first_eval

    def test_all_eval_sets_valid_json(self):
        """All eval set files should be valid JSON."""
        for eval_file in get_eval_set_files():
            with open(eval_file) as f:
                data = json.load(f)
            assert "evals" in data, f"{eval_file.name} missing 'evals' key"


@pytest.mark.skipif(
    not os.environ.get("GOOGLE_CLOUD_PROJECT"),
    reason="GOOGLE_CLOUD_PROJECT not set - skipping ADK evaluation tests"
)
class TestADKEvaluationExecution:
    """Integration tests that run actual ADK evaluations.

    These tests require:
    - GOOGLE_CLOUD_PROJECT environment variable set
    - Vertex AI API access
    - Valid API credentials
    """

    @pytest.fixture(autouse=True)
    def check_credentials(self):
        """Skip if no credentials available."""
        if not os.environ.get("GOOGLE_APPLICATION_CREDENTIALS"):
            # Check for default credentials
            import google.auth
            try:
                google.auth.default()
            except Exception:
                pytest.skip("No Google Cloud credentials available")

    @pytest.mark.asyncio
    async def test_librarian_evaluation(self):
        """Run ADK evaluation on Librarian agent."""
        try:
            from google.adk.evaluation import AgentEvaluator
        except ImportError:
            pytest.skip("google.adk.evaluation not available")

        config = load_eval_config()

        results = await AgentEvaluator.evaluate(
            agent_module="archive_agents",
            eval_dataset_file_path_or_dir=str(EVAL_SETS_DIR / "librarian_eval.json"),
            num_runs=config.get("num_samples", 1),
        )

        # Check that evaluation completed
        assert results is not None

        # Check score thresholds
        if hasattr(results, "tool_trajectory_avg_score"):
            threshold = config["criteria"]["tool_trajectory_avg_score"]["threshold"]
            assert results.tool_trajectory_avg_score >= threshold, (
                f"Tool trajectory score {results.tool_trajectory_avg_score} "
                f"below threshold {threshold}"
            )

    @pytest.mark.asyncio
    async def test_full_pipeline_evaluation(self):
        """Run ADK evaluation on full blog pipeline."""
        try:
            from google.adk.evaluation import AgentEvaluator
        except ImportError:
            pytest.skip("google.adk.evaluation not available")

        full_pipeline_eval = EVAL_SETS_DIR / "full_pipeline_eval.json"
        if not full_pipeline_eval.exists():
            pytest.skip("full_pipeline_eval.json not yet created")

        results = await AgentEvaluator.evaluate(
            agent_module="archive_agents",
            eval_dataset_file_path_or_dir=str(full_pipeline_eval),
            num_runs=1,
        )

        assert results is not None


class TestEvalSetContent:
    """Tests for eval set content quality."""

    def test_librarian_eval_covers_key_scenarios(self):
        """Librarian eval should cover key usage scenarios."""
        with open(EVAL_SETS_DIR / "librarian_eval.json") as f:
            data = json.load(f)

        eval_ids = [e["eval_id"] for e in data["evals"]]

        # Should have basic search test
        assert any("basic" in eid.lower() or "search" in eid.lower() for eid in eval_ids)

        # Should have folklore test
        assert any("folklore" in eid.lower() for eid in eval_ids)

        # Should have no-results handling test
        assert any("no_result" in eid.lower() or "no-result" in eid.lower() for eid in eval_ids)

    def test_eval_conversations_are_in_japanese(self):
        """Eval conversations should be in Japanese to match expected usage."""
        with open(EVAL_SETS_DIR / "librarian_eval.json") as f:
            data = json.load(f)

        for eval_case in data["evals"]:
            for turn in eval_case["conversation"]:
                if "user_content" in turn:
                    # Check for Japanese characters
                    content = turn["user_content"]
                    has_japanese = any(
                        "\u3040" <= char <= "\u309F" or  # Hiragana
                        "\u30A0" <= char <= "\u30FF" or  # Katakana
                        "\u4E00" <= char <= "\u9FFF"     # Kanji
                        for char in content
                    )
                    assert has_japanese, (
                        f"Eval {eval_case['eval_id']} user_content should be in Japanese"
                    )
