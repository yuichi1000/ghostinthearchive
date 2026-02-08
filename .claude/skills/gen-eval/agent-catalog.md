# エージェントカタログ

プロジェクト内の全 ADK エージェントのプロパティと期待される eval シナリオの一覧。

## Archive パイプライン（`archive_agents/`）

パイプライン順序: Librarian → Scholar → Storyteller → Illustrator → Publisher

Curator はスタンドアロンエージェント（シーケンシャルパイプラインには含まれない）。

### Librarian

| プロパティ | 値 |
|----------|-------|
| モジュール | `archive_agents/agents/librarian.py` |
| 変数名 | `librarian_agent` |
| モデル | `gemini-3-pro-preview` |
| 出力キー | `collected_documents` |
| ツール | `search_newspapers`, `search_archives`, `get_available_keywords` |
| 前段 | （なし — 最初のエージェント） |
| チェックするマーカー | （なし） |
| 出力するマーカー | `NO_DOCUMENTS_FOUND` |
| プレースホルダー | （なし） |

**Eval シナリオ:**

| eval_id | 説明 | tool_uses | final_response キーワード |
|---------|------|-----------|------------------------|
| `librarian_basic_search` | 基本的な歴史文書検索 | `search_newspapers`, `search_archives` | `collected_documents total_found` |
| `librarian_folklore_search` | 民俗・伝説検索（キーワード探索あり） | `get_available_keywords`, `search_newspapers` | `ghost legend folklore` |
| `librarian_no_results` | 文書なし（不可能なクエリ） | `search_newspapers` | `NO_DOCUMENTS_FOUND` |
| `librarian_bilingual_expansion` | バイリンガル（英語＋スペイン語）検索 | `search_newspapers`, `search_archives` | `sources_searched` |

---

### Scholar

| プロパティ | 値 |
|----------|-------|
| モジュール | `archive_agents/agents/scholar.py` |
| 変数名 | `scholar_agent` |
| モデル | `gemini-3-pro-preview` |
| 出力キー | `mystery_report` |
| ツール | （なし） |
| 前段 | Librarian（`collected_documents`） |
| チェックするマーカー | `NO_DOCUMENTS_FOUND` |
| 出力するマーカー | `INSUFFICIENT_DATA` |
| プレースホルダー | `{collected_documents}` |

**Eval シナリオ:**

| eval_id | 説明 | tool_uses | final_response キーワード |
|---------|------|-----------|------------------------|
| `scholar_fact_based_analysis` | 歴史的事実の分析（日付・事象の矛盾） | `[]` | `mystery_report DATE_MISMATCH` |
| `scholar_folklore_analysis` | 民俗学的アノマリー分析（反復パターン、禁忌） | `[]` | `Folkloric Context RECURRING_PATTERN` |
| `scholar_anthropological_analysis` | 文化人類学分析（権力構造、儀礼） | `[]` | `Anthropological Context POWER_ERASURE` |
| `scholar_insufficient_data` | データ不足時の処理 | `[]` | `INSUFFICIENT_DATA NO_DOCUMENTS_FOUND` |
| `scholar_cross_reference_analysis` | 事実・民俗・人類学の相互参照 | `[]` | `Folkloric Context Anthropological Context` |

---

### Storyteller

| プロパティ | 値 |
|----------|-------|
| モジュール | `archive_agents/agents/storyteller.py` |
| 変数名 | `storyteller_agent` |
| モデル | `gemini-3-pro-preview` |
| 出力キー | `creative_content` |
| ツール | （なし） |
| 前段 | Scholar（`mystery_report`） |
| チェックするマーカー | `INSUFFICIENT_DATA` |
| 出力するマーカー | `NO_CONTENT` |
| プレースホルダー | `{mystery_report}` |

**Eval シナリオ:**

| eval_id | 説明 | tool_uses | final_response キーワード |
|---------|------|-----------|------------------------|
| `storyteller_complete_narrative` | 完全なブログ記事生成 | `[]` | `creative_content Sources Firestore` |
| `storyteller_fact_folklore_balance` | 歴史的事実と民俗要素のバランス | `[]` | `伝説 記録 Firestore` |
| `storyteller_four_part_structure` | 4部構成（発掘、証拠、文脈、余韻） | `[]` | `アーカイブ Sources Firestore` |
| `storyteller_insufficient_data` | 入力不足時の NO_CONTENT 出力 | `[]` | `NO_CONTENT INSUFFICIENT_DATA` |

---

### Illustrator

| プロパティ | 値 |
|----------|-------|
| モジュール | `archive_agents/agents/illustrator.py` |
| 変数名 | `illustrator_agent` |
| モデル | `gemini-3-pro-preview` |
| 出力キー | `visual_assets` |
| ツール | `generate_image` |
| 前段 | Storyteller（`creative_content`） |
| チェックするマーカー | `NO_CONTENT` |
| 出力するマーカー | （なし） |
| プレースホルダー | `{creative_content}` |

**Eval シナリオ:**

| eval_id | 説明 | tool_uses | final_response キーワード |
|---------|------|-----------|------------------------|
| `illustrator_fact_style` | Fact 系画像（白黒写真風） | `generate_image` | `visual_assets Fact` |
| `illustrator_folklore_style` | Folklore 系画像（19世紀版画風） | `generate_image` | `visual_assets Folklore` |
| `illustrator_no_content_skip` | NO_CONTENT 時の生成スキップ | `[]` | `NO_CONTENT` |

---

### Publisher

| プロパティ | 値 |
|----------|-------|
| モジュール | `archive_agents/agents/publisher.py` |
| 変数名 | `publisher_agent` |
| モデル | `gemini-3-pro-preview` |
| 出力キー | `published_episode` |
| ツール | `upload_images`, `publish_mystery` |
| 前段 | Illustrator（`visual_assets`）+ 全上流キー |
| チェックするマーカー | 全上流マーカー（`NO_DOCUMENTS_FOUND`, `INSUFFICIENT_DATA`, `NO_CONTENT`） |
| 出力するマーカー | （なし） |
| プレースホルダー | `{collected_documents}`, `{mystery_report}`, `{creative_content}`, `{visual_assets}` |

**Eval シナリオ:**

| eval_id | 説明 | tool_uses | final_response キーワード |
|---------|------|-----------|------------------------|
| `publisher_full_workflow` | 画像アップロード付きフル公開ワークフロー | `upload_images`, `publish_mystery` | `published_episode Firestore mystery_id` |
| `publisher_document_structure` | Firestore 必須フィールドの検証 | `publish_mystery` | `mystery_id status Firestore` |
| `publisher_failure_handling` | 上流失敗検出時の公開スキップ | `[]` | `INSUFFICIENT_DATA NO_CONTENT` |

---

### Curator

| プロパティ | 値 |
|----------|-------|
| モジュール | `archive_agents/agents/curator.py` |
| 変数名 | `curator_agent` |
| モデル | `gemini-3-pro-preview` |
| 出力キー | `suggested_themes` |
| ツール | （なし） |
| 前段 | （スタンドアロン — シーケンシャルパイプライン外） |
| チェックするマーカー | （なし） |
| 出力するマーカー | （なし） |
| プレースホルダー | `{existing_titles}` |

**Eval シナリオ:**

| eval_id | 説明 | tool_uses | final_response キーワード |
|---------|------|-----------|------------------------|
| `curator_theme_suggestion` | 調査テーマの提案 | `[]` | `suggested_themes Fact Folklore` |
| `curator_duplicate_avoidance` | 既存タイトルとの重複回避 | `[]` | `suggested_themes 重複なし` |

---

## Podcast パイプライン（`podcast_agents/`）

パイプライン順序: Scriptwriter → Producer

### Scriptwriter

| プロパティ | 値 |
|----------|-------|
| モジュール | `podcast_agents/agents/scriptwriter.py` |
| 変数名 | `scriptwriter_agent` |
| モデル | `gemini-3-pro-preview` |
| 出力キー | `podcast_script` |
| ツール | （なし） |
| 前段 | （Firestore から `creative_content` を事前セット） |
| チェックするマーカー | `NO_CONTENT` |
| 出力するマーカー | `NO_SCRIPT` |
| プレースホルダー | `{creative_content}` |

**Eval シナリオ:**

| eval_id | 説明 | tool_uses | final_response キーワード |
|---------|------|-----------|------------------------|
| `scriptwriter_complete_script` | 完全なポッドキャスト脚本生成 | `[]` | `podcast_script INTRO OUTRO` |
| `scriptwriter_segment_structure` | INTRO/SEGMENTS/OUTRO 構成の検証 | `[]` | `INTRO SEGMENTS OUTRO` |
| `scriptwriter_no_content_failure` | NO_CONTENT 入力時の NO_SCRIPT 出力 | `[]` | `NO_SCRIPT NO_CONTENT` |

---

### Producer

| プロパティ | 値 |
|----------|-------|
| モジュール | `podcast_agents/agents/producer.py` |
| 変数名 | `producer_agent` |
| モデル | `gemini-3-pro-preview` |
| 出力キー | `audio_assets` |
| ツール | （なし） |
| 前段 | Scriptwriter（`podcast_script`） |
| チェックするマーカー | （なし） |
| 出力するマーカー | （なし） |
| プレースホルダー | `{podcast_script}` |

**Eval シナリオ:**

| eval_id | 説明 | tool_uses | final_response キーワード |
|---------|------|-----------|------------------------|
| `producer_audio_plan` | 音声制作プランの生成 | `[]` | `audio_assets voice SFX` |
| `producer_bilingual_text` | バイリンガル（日本語/英語）テキストセグメント | `[]` | `bilingual 日本語 English` |
| `producer_voice_sfx_settings` | ボイスと SFX の設定 | `[]` | `voice SFX BGM` |

---

## Translator パイプライン（`translator_agents/`）

### Translator

| プロパティ | 値 |
|----------|-------|
| モジュール | `translator_agents/agents/translator.py` |
| 変数名 | `translator_agent` |
| モデル | `gemini-3-pro-preview` |
| 出力キー | `translation_result` |
| ツール | （なし） |
| 前段 | （Firestore から事前セットされたフィールドを読み取り） |
| チェックするマーカー | `NO_CONTENT` |
| 出力するマーカー | `NO_TRANSLATION` |
| プレースホルダー | `{title}`, `{summary}`, `{narrative_content}`, `{discrepancy_detected}`, `{hypothesis}`, `{alternative_hypotheses}`, `{political_climate}`, `{story_hooks}` |

**Eval シナリオ:**

| eval_id | 説明 | tool_uses | final_response キーワード |
|---------|------|-----------|------------------------|
| `translator_complete_translation` | 完全な日英翻訳 | `[]` | `translation_result title_en summary_en narrative_content_en` |
| `translator_no_content_skip` | NO_CONTENT 入力時の NO_TRANSLATION 出力 | `[]` | `NO_TRANSLATION NO_CONTENT` |
| `translator_json_output_format` | _en フィールド付き JSON 出力構造の検証 | `[]` | `translation_result JSON title_en` |

---

## メンテナンス

新しいエージェントをパイプラインに追加する際:

1. 同じテーブル形式でこのカタログにエージェント定義を追加する
2. 新しいエージェントに対して `/gen-eval` を実行し eval テストを生成する
3. `pytest tests/eval/ tests/integration/ -v` で全テストが通ることを確認する
