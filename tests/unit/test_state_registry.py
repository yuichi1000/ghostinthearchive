"""Tests for shared/state_registry.py の整合性検証。"""

from shared.state_registry import STATE_KEYS, generate_mermaid


class TestStateKeyDefinitions:
    """StateKey 定義の整合性テスト。"""

    def test_all_keys_have_writers(self):
        """全てのキーに少なくとも1つの writer がある。"""
        for key in STATE_KEYS:
            assert len(key.written_by) > 0, f"{key.name} has no writers"

    def test_no_orphan_keys(self):
        """writer はあるが reader がいないキーは published_episode のみ許容。"""
        orphans = [k.name for k in STATE_KEYS if not k.read_by]
        # active_languages は PR 3 の DynamicScholarBlock が reader になる予定
        allowed_orphans = {"published_episode", "active_languages"}
        unexpected = set(orphans) - allowed_orphans
        assert not unexpected, f"Unexpected orphan keys: {unexpected}"

    def test_key_names_are_unique(self):
        """キー名が重複しない。"""
        names = [k.name for k in STATE_KEYS]
        assert len(names) == len(set(names)), "Duplicate key names found"

    def test_all_keys_have_descriptions(self):
        """全てのキーに説明がある。"""
        for key in STATE_KEYS:
            assert key.description, f"{key.name} has empty description"


class TestExpectedKeys:
    """CLAUDE.md に記載のキーが全て登録されているか。"""

    EXPECTED_KEYS = {
        "selected_languages",
        "collected_documents_{lang}",
        "scholar_analysis_{lang}",
        "debate_whiteboard",
        "structured_report",
        "mystery_report",
        "creative_content",
        "visual_assets",
        "image_metadata",
        "translation_result_{lang}",
        "published_episode",
        "podcast_script",
        "structured_script",
        "podcast_script_ja",
    }

    def test_all_expected_keys_present(self):
        """CLAUDE.md 記載のキーが全て STATE_KEYS に含まれる。"""
        registered = {k.name for k in STATE_KEYS}
        missing = self.EXPECTED_KEYS - registered
        assert not missing, f"Missing keys: {missing}"


class TestGenerateMermaid:
    """generate_mermaid() の出力形式テスト。"""

    def test_output_starts_with_flowchart(self):
        """Mermaid 出力が flowchart で始まる。"""
        output = generate_mermaid()
        assert output.startswith("flowchart LR")

    def test_output_contains_arrows(self):
        """writes/reads の矢印が含まれる。"""
        output = generate_mermaid()
        assert "-->|writes|" in output
        assert "-->|reads|" in output

    def test_output_contains_state_keys(self):
        """主要なステートキーがノードとして含まれる。"""
        output = generate_mermaid()
        assert "creative_content" in output
        assert "mystery_report" in output
        assert "selected_languages" in output
