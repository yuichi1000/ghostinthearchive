# エージェントカタログ

プロジェクト内の全 ADK エージェントのプロパティと期待される eval シナリオの一覧。

## ブログ作成パイプライン（`mystery_agents/`）

パイプライン順序: ThemeAnalyzer → ParallelLibrarians → [ScholarGate] → ParallelScholars(分析) → DebateLoop(討論) → [PolymathGate] → ArmchairPolymath → [StorytellerGate] → Storyteller → [PostStoryGate] → Illustrator → Translator → Publisher

Curator はスタンドアロンエージェント（シーケンシャルパイプラインには含まれない）。

### ThemeAnalyzer

| プロパティ | 値 |
|----------|-------|
| モジュール | `mystery_agents/agents/theme_analyzer.py` |
| 変数名 | `theme_analyzer_agent` |
| モデル | `gemini-2.5-flash` |
| 出力キー | `theme_analysis` |
| ツール | `save_language_selection` |
| 前段 | （なし — パイプライン最初のエージェント） |
| チェックするマーカー | （なし） |
| 出力するマーカー | （なし） |
| プレースホルダー | （なし） |

**Eval シナリオ:**

| eval_id | 説明 | tool_uses | final_response キーワード |
|---------|------|-----------|------------------------|
| `theme_analyzer_geographic_selection` | 地理的手がかりに基づく言語選択（ニューオーリンズ → en, fr, es） | `save_language_selection` | `theme_analysis selected_languages en fr es` |
| `theme_analyzer_cultural_selection` | 文化的手がかりに基づく言語選択（ペンシルベニア独系 → en, de） | `save_language_selection` | `theme_analysis selected_languages en de` |
| `theme_analyzer_default_fallback` | デフォルトフォールバック（南部一般 → en, es） | `save_language_selection` | `theme_analysis selected_languages en es` |
| `theme_analyzer_single_language` | 単一言語選択（西部開拓 → en のみ） | `save_language_selection` | `theme_analysis selected_languages en` |

---

### Librarian

| プロパティ | 値 |
|----------|-------|
| モジュール | `mystery_agents/agents/language_librarians.py` |
| 変数名 | `create_librarian(lang_code)` ファクトリ関数 |
| モデル | `gemini-2.5-flash` |
| 出力キー | `collected_documents_{lang}` |
| ツール | EN: `search_newspapers`, `search_archives`, `get_available_keywords` / 他言語: `search_archives` のみ |
| 前段 | ThemeAnalyzer（言語選択） |
| チェックするマーカー | （なし） |
| 出力するマーカー | `NO_DOCUMENTS_FOUND` |
| プレースホルダー | `{language_name}`, `{lang_code}`, `{cultural_context}`, `{sources_hint}`, `{newspaper_instruction}` |

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
| モジュール | `mystery_agents/agents/language_scholars.py` |
| 変数名 | `create_scholar(lang_code, mode)` ファクトリ関数 |
| モデル | `gemini-3-pro-preview` |
| 出力キー | `scholar_analysis_{lang}` |
| ツール | 分析モード: （なし）/ 討論モード: `append_to_whiteboard` |
| 前段 | Librarian（`collected_documents_{lang}`） |
| チェックするマーカー | `NO_DOCUMENTS_FOUND` |
| 出力するマーカー | `INSUFFICIENT_DATA` |
| プレースホルダー | 分析: `{collected_documents_{lang}}`, `{collected_documents_en}` / 討論: `{scholar_analysis_*}`, `{debate_whiteboard}` |

**Eval シナリオ:**

| eval_id | 説明 | tool_uses | final_response キーワード |
|---------|------|-----------|------------------------|
| `scholar_fact_based_analysis` | 歴史的事実の分析（日付・事象の矛盾） | `[]` | `mystery_report DATE_MISMATCH` |
| `scholar_folklore_analysis` | 民俗学的アノマリー分析（反復パターン、禁忌） | `[]` | `Folkloric Context RECURRING_PATTERN` |
| `scholar_anthropological_analysis` | 文化人類学分析（権力構造、儀礼） | `[]` | `Anthropological Context POWER_ERASURE` |
| `scholar_insufficient_data` | データ不足時の処理 | `[]` | `INSUFFICIENT_DATA NO_DOCUMENTS_FOUND` |
| `scholar_cross_reference_analysis` | 事実・民俗・人類学の相互参照 | `[]` | `Folkloric Context Anthropological Context` |

---

### Armchair Polymath

| プロパティ | 値 |
|----------|-------|
| モジュール | `mystery_agents/agents/armchair_polymath.py` |
| 変数名 | `armchair_polymath_agent` |
| モデル | `gemini-3-pro-preview` |
| 出力キー | `mystery_report` |
| ツール | `save_structured_report` |
| 前段 | Scholar（`scholar_analysis_{lang}`）+ DebateLoop（`debate_whiteboard`） |
| チェックするマーカー | 全 Scholar 分析が空 → `INSUFFICIENT_DATA` |
| 出力するマーカー | `INSUFFICIENT_DATA` |
| プレースホルダー | `{scholar_analysis_en}`, `{scholar_analysis_de}`, `{scholar_analysis_es}`, `{scholar_analysis_fr}`, `{scholar_analysis_nl}`, `{scholar_analysis_pt}`, `{debate_whiteboard}` |

**Eval シナリオ:**

| eval_id | 説明 | tool_uses | final_response キーワード |
|---------|------|-----------|------------------------|
| `armchair_polymath_cross_language` | 3言語統合分析（en+de+nl）ニューアムステルダム | `save_structured_report` | `mystery_report classification discrepancy hypothesis cross_reference` |
| `armchair_polymath_single_language` | 単一言語分析（en）ボストン幽霊屋敷 | `save_structured_report` | `mystery_report hypothesis evidence historical_context` |
| `armchair_polymath_debate_integration` | 討論ホワイトボード統合、ルイジアナ奴隷反乱 | `save_structured_report` | `mystery_report debate discrepancy cross_reference cultural_bias` |
| `armchair_polymath_insufficient_data` | 全分析空 → 失敗 | `[]` | `INSUFFICIENT_DATA` |

---

### Storyteller

| プロパティ | 値 |
|----------|-------|
| モジュール | `mystery_agents/agents/storyteller.py` |
| 変数名 | `storyteller_agent` |
| モデル | `gemini-3-pro-preview` |
| 出力キー | `creative_content` |
| ツール | （なし） |
| 前段 | Armchair Polymath（`mystery_report`） |
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
| モジュール | `mystery_agents/agents/illustrator.py` |
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
| モジュール | `mystery_agents/agents/publisher.py` |
| 変数名 | `publisher_agent` |
| モデル | `gemini-2.5-flash` |
| 出力キー | `published_episode` |
| ツール | `publish_mystery` |
| 前段 | Illustrator（`visual_assets`）+ Translator（`translation_result`）+ 全上流キー |
| チェックするマーカー | 全上流マーカー（`NO_DOCUMENTS_FOUND`, `INSUFFICIENT_DATA`, `NO_CONTENT`, `NO_TRANSLATION`） |
| 出力するマーカー | （なし） |
| プレースホルダー | `{collected_documents_en}`, `{mystery_report}`, `{creative_content}`, `{visual_assets}`, `{translation_result}` |

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
| モジュール | `curator_agents/agents/curator.py` |
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

ブログパイプライン内で Illustrator → Translator → Publisher の順で実行される。
また、Curator のテーマ提案翻訳にも使用される汎用翻訳エージェント。

### Translator

| プロパティ | 値 |
|----------|-------|
| モジュール | `translator_agents/agents/translator.py` |
| 変数名 | `translator_agent` |
| モデル | `gemini-2.5-flash` |
| 出力キー | `translation_result` |
| ツール | （なし） |
| 前段 | Storyteller（`creative_content`）経由で入力 |
| チェックするマーカー | `NO_CONTENT`, `INSUFFICIENT_DATA` |
| 出力するマーカー | `NO_TRANSLATION` |
| プレースホルダー | （入力は user message JSON として受け取る） |

**Eval シナリオ:**

| eval_id | 説明 | tool_uses | final_response キーワード |
|---------|------|-----------|------------------------|
| `translator_complete_translation` | 全フィールド EN→JA 翻訳 | `[]` | `translation_result title_ja summary_ja narrative_content_ja discrepancy_detected_ja hypothesis_ja` |
| `translator_no_content_skip` | NO_CONTENT 入力時の NO_TRANSLATION 出力 | `[]` | `NO_TRANSLATION NO_CONTENT` |
| `translator_json_output_format` | `_ja` フィールド付き JSON 出力構造の検証 | `[]` | `translation_result title_ja summary_ja hypothesis_ja alternative_hypotheses_ja story_hooks_ja` |

---

## メンテナンス

新しいエージェントをパイプラインに追加する際:

1. 同じテーブル形式でこのカタログにエージェント定義を追加する
2. 新しいエージェントに対して `/gen-eval` を実行し eval テストを生成する
3. `pytest tests/eval/ tests/integration/ -v` で全テストが通ることを確認する
