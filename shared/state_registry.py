"""セッション状態キーのレジストリ。

パイプライン全体でどのエージェント/ツールがどのセッション状態キーを
読み書きするかを宣言的に記述する。ランタイム強制は行わず、
ドキュメント + テスト検証用途。

使用例:
    from shared.state_registry import STATE_KEYS, generate_mermaid
    print(generate_mermaid())
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class StateKey:
    """セッション状態キーの定義。

    Attributes:
        name: キー名（テンプレート変数 {lang} を含む場合あり）
        description: キーの説明（日本語）
        written_by: このキーに書き込むエージェント/ツールのリスト
        read_by: このキーを読み取るエージェント/ツールのリスト
    """

    name: str
    description: str
    written_by: tuple[str, ...] = field(default_factory=tuple)
    read_by: tuple[str, ...] = field(default_factory=tuple)


# ---------------------------------------------------------------------------
# ブログパイプライン（mystery_agents）
# ---------------------------------------------------------------------------
STATE_KEYS: list[StateKey] = [
    StateKey(
        name="selected_languages",
        description="調査対象言語リスト（パイプライン初期化で全言語セット）",
        written_by=("pipeline_init",),
        read_by=("language_gate", "pipeline_gate"),
    ),
    StateKey(
        name="collected_documents_{lang}",
        description="Librarian が収集した資料（言語別）",
        written_by=("librarian_{lang}",),
        read_by=("scholar_{lang}", "pipeline_gate", "publisher_tools"),
    ),
    StateKey(
        name="raw_search_results",
        description="Librarian ツールが直接書き込む検索結果リスト（ベースキー）",
        written_by=("librarian_tools",),
        read_by=("search_metadata", "search_metrics"),
    ),
    StateKey(
        name="raw_search_results_{lang}",
        description="Librarian ツールが直接書き込む検索結果リスト（言語別）",
        written_by=("librarian_tools",),
        read_by=("search_metadata", "search_metrics"),
    ),
    StateKey(
        name="scholar_analysis_{lang}",
        description="Scholar（分析モード）の分析レポート（言語別）",
        written_by=("scholar_{lang}",),
        read_by=("armchair_polymath", "pipeline_gate", "publisher_tools"),
    ),
    StateKey(
        name="debate_whiteboard",
        description="討論ホワイトボード（Scholar 討論モードが累積書き込み）",
        written_by=("pipeline_init", "debate_tools"),
        read_by=("armchair_polymath",),
    ),
    StateKey(
        name="structured_report",
        description="Armchair Polymath の構造化分析 JSON",
        written_by=("scholar_tools",),
        read_by=("publisher_tools",),
    ),
    StateKey(
        name="mystery_report",
        description="Armchair Polymath の統合分析レポート（output_key）",
        written_by=("armchair_polymath",),
        read_by=("storyteller", "pipeline_gate"),
    ),
    StateKey(
        name="creative_content",
        description="Storyteller の英語ブログ原稿（output_key）",
        written_by=("storyteller",),
        read_by=("illustrator_tools", "translator_{lang}", "pipeline_gate", "publisher_tools"),
    ),
    StateKey(
        name="visual_assets",
        description="Illustrator のトップ画像アセット（output_key）",
        written_by=("illustrator",),
        read_by=("publisher_tools",),
    ),
    StateKey(
        name="image_metadata",
        description="Illustrator の画像メタデータ（ツール書き込み）",
        written_by=("illustrator_tools",),
        read_by=("publisher_tools",),
    ),
    StateKey(
        name="translation_result_{lang}",
        description="Translator の翻訳結果（言語別 JSON、output_key）",
        written_by=("translator_{lang}",),
        read_by=("publisher_tools",),
    ),
    StateKey(
        name="archive_images",
        description="Librarian が収集したアーカイブ資料画像リスト（title, source_url, thumbnail_url, image_url 等）",
        written_by=("librarian_tools",),
        read_by=("storyteller",),
    ),
    StateKey(
        name="published_episode",
        description="Publisher の公開結果（output_key）",
        written_by=("publisher",),
        read_by=(),
    ),
    # --- Podcast パイプライン ---
    StateKey(
        name="podcast_script",
        description="Scriptwriter のポッドキャスト台本（output_key）",
        written_by=("scriptwriter",),
        read_by=("podcast_translator",),
    ),
    StateKey(
        name="structured_script",
        description="Scriptwriter の構造化台本 JSON（ツール書き込み）",
        written_by=("script_tools",),
        read_by=("podcast_cli",),
    ),
    StateKey(
        name="podcast_script_ja",
        description="Podcast Translator の日本語台本（output_key）",
        written_by=("podcast_translator",),
        read_by=("podcast_cli",),
    ),
]


def generate_mermaid() -> str:
    """Mermaid flowchart 形式のステート依存関係図を生成する。

    Returns:
        Mermaid 記法の文字列
    """
    lines = ["flowchart LR"]

    for key in STATE_KEYS:
        # ノード名（Mermaid ID に使える形に変換）
        node_id = key.name.replace("{lang}", "lang").replace("{", "").replace("}", "")

        for writer in key.written_by:
            writer_id = writer.replace("{lang}", "lang").replace("{", "").replace("}", "")
            lines.append(f"    {writer_id} -->|writes| {node_id}[{key.name}]")

        for reader in key.read_by:
            reader_id = reader.replace("{lang}", "lang").replace("{", "").replace("}", "")
            lines.append(f"    {node_id}[{key.name}] -->|reads| {reader_id}")

    return "\n".join(lines)
