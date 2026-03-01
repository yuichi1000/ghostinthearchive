# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

Ghost in the Archive - 5つの学術領域（歴史学・民俗学・文化人類学・言語学・文書館学）のAI自律調査で世界の公開デジタルアーカイブを分析し、記録の隙間に潜む Ghost を発掘するエージェントシステム

### 設計思想：Ghost = 記録の隙間に潜むアノマリー

**Ghost の定義**: 世界の公開デジタルアーカイブをAIが学際的に分析した結果浮かび上がるアノマリー。公開情報だけで仮説を立て、公開情報だけで検証する。それでもなお残る「説明不能な余白」— 不在の中の存在感 — それが Ghost。

**5つの柱**:

1. **自律型AIエージェント** — 人間のバイアスや疲労なき調査
2. **公開情報の透明性** — すべての仮説は公開記録のみで構築・検証可能
3. **AI横断発見** — 複数のアーカイブ・学問分野を横断して初めて見えるアノマリー
4. **学際的分析** — 歴史学・民俗学・文化人類学・言語学・文書館学の5領域
5. **知的畏怖としての怪異** — センセーショナリズムではなく、学術的探究の正当な対象

**Ghost の認定3条件:**

1. **複数独立ソース条件**: 2つ以上の独立した一次資料間に、通常の記録慣行では説明できない矛盾が存在する
2. **API 限界排除条件**: デジタル化範囲・API 制限・OCR 品質・検索用語の限界では矛盾を説明できない
3. **再現性条件**: 公開情報のみで第三者が同じ矛盾を確認できる

**Ghost 度の段階定義:**

| 段階 | 名称 | 条件 |
|------|------|------|
| HIGH | Confirmed Ghost | 3条件すべてを満たし、3+独立資料で裏付け |
| MEDIUM | Suspected Ghost | 条件1+3を満たすが、API限界による説明の余地あり |
| LOW | Archival Echo | 単一ソースまたは表記差で説明可能。さらなる調査が必要 |

**Folklore の位置づけ**: 民俗資料は装飾ではない。公式記録が沈黙する部分を埋める補完的証拠である。

**トーン**: 学術的誠実さ + ドライなウィット。

## Development Workflow

### ブランチ戦略

- コード修正時は必ず feature ブランチを作成してから作業する
- `main` ブランチへの直接コミットは行わない
- Claude Code と GitHub での並列開発に対応するため `git worktree` を使用する
- ブランチ名は Conventional Commits 準拠のプレフィックスを使用する：
  - `feat/` - 新機能
  - `fix/` - バグ修正
  - `docs/` - ドキュメント変更
  - `refactor/` - リファクタリング
  - `test/` - テスト追加・修正
  - `chore/` - その他（設定変更、依存関係更新等）
- プランモードで計画を立てる際は、実装時に使用するブランチ名を計画内に必ず明記する

### リリースブランチ運用（v2.0: 2026/2/19 〜 2026/3/3）

この期間中は `release/v2.0` をベースブランチとして開発を進める。

- トピックブランチは **`release/v2.0` から作成**する（`main` からではない）
- PR のマージ先は **`release/v2.0`**（`main` ではない）
- 2026/3/3 に `release/v2.0` を `main` にマージしてリリースする

```bash
# worktree 作成時は release/v2.0 を起点にする
git worktree add ../ghostinthearchive-<branch-name> -b <prefix>/<branch-name> release/v2.0

# PR 作成時は release/v2.0 をベースに指定する
gh pr create --base release/v2.0 --title "タイトル" --body "説明"
```

> **注意**: この期間が終了したら、このセクションを削除し、通常の `main` ベース運用に戻すこと。

### git worktree 運用

```bash
# 新しい作業ブランチを worktree として追加
git worktree add ../ghostinthearchive-<branch-name> -b <prefix>/<branch-name>

# 作業完了後に worktree を削除
git worktree remove ../ghostinthearchive-<branch-name>
```

- 各 worktree は独立したディレクトリで動作するため、複数ブランチの並列作業が可能
- worktree のディレクトリ名は `ghostinthearchive-<branch-name>` とする

### Git Hooks

本リポジトリは `.githooks/` ディレクトリで Git hook を管理する。初回クローン時に以下を実行：

```bash
git config core.hooksPath .githooks
```

これにより main ブランチへの直接コミットがブロックされる。

### 日本語使用ルール

- **コミットメッセージ**: 日本語で記述する
- **プルリクエスト**: タイトル・説明文は日本語で記述する
- **ソースコードのコメント**: 日本語で記述する
- **エージェントプロンプト（instruction）**: 英語で記述する（Prompt Language Policy 参照）

### Claude Code ファイル除外設定

- Claude Code が読み取る必要のないファイル・フォルダは `.claude/settings.json` の `permissions.deny` で管理する
- デバッグ時に必要になりうるファイル（`logs/`、`.adk/`、ロックファイル等）は `permissions.ask` に設定し、読み取り時に確認プロンプトを表示する
- 新たにビルド出力、キャッシュ、大容量の生成物などが追加された場合は `.claude/settings.json` の deny/ask ルールも合わせて更新する

### 共有コード管理（DRY 原則）

web-admin と web-public で共通するコードは `packages/shared/`（`@ghost/shared`）で一元管理する。
同じコードを2箇所にコピーしない。

**`@ghost/shared` に入れるもの:**

- 型定義（`types/mystery.ts` 等）
- Firebase クライアント設定（`lib/firebase/config.ts`）
- Firestore 読み取りクエリ（`lib/firestore/queries.ts`）
- ユーティリティ関数（`lib/utils.ts`）
- ローカライズ関数（`lib/localize.ts` — `localizeMystery()`, `getTranslatedExcerpt()`）
- 共通 UI コンポーネント（`evidence-block.tsx`, `footer.tsx`, `button.tsx`）

**各アプリに残すもの（アプリ固有）:**

- web-admin: 書き込み操作（approve, archive 等）、認証（NextAuth）、管理画面コンポーネント、言語セレクタ
- web-public: i18n 辞書（`lib/i18n/dictionaries/`）、言語スイッチャー、公開サイト固有コンポーネント
- ページコンポーネント（`app/` 配下）は常にアプリ固有

## Tech Stack

- **Infrastructure:** Google Cloud (Cloud Run)
- **AI/ML:** Vertex AI (Gemini Pro/Flash, Imagen 3, Chirp 3, Text-to-Speech)
- **Agent Framework:** Agent Development Kit (ADK)
- **Data:** Cloud Storage, Firestore
- **Web:** Next.js

## Web Architecture

- **web-public**: SSG（Static Site Generation）で動作（`output: "export"`）
  - 4言語（en/ja/es/de）× N記事 の静的 HTML をビルド時に生成
  - `React.cache` で Firestore クエリを 4N→1 回に最適化
  - 記事更新時は Cloud Build（E2_HIGHCPU_8）で再ビルド・再デプロイ
  - ルート `/` はブラウザ言語を検出して `/{lang}/` にリダイレクト
- **web-admin**: クライアントサイドレンダリング（毎回 Firestore アクセス）
- 記事更新頻度: 1日最大1回

## Multi-Agent System

複数の独立した ADK パイプラインで構成：

### ブログ作成パイプライン（`mystery_agents/`）

| エージェント          | 役割                                                 | 入力                                 | 出力                                                                     |
| --------------------- | ---------------------------------------------------- | ------------------------------------ | ------------------------------------------------------------------------ |
| **Librarian**         | 資料調査・収集（デジタルアーカイブ＋民俗資料）       | 調査クエリ                           | collected_documents                                                      |
| **Scholar**           | 歴史学×民俗学×文化人類学の学際分析＋討論（英語出力） | collected_documents                  | scholar_analysis（分析モード）/ debate_whiteboard への追記（討論モード） |
| **Armchair Polymath** | 学際統合分析（書斎の安楽椅子学者）               | scholar_analysis + debate_whiteboard | mystery_report                                                           |
| **Storyteller**       | 歴史的厳密さと怪異的情緒の融合（英語ブログ記事）     | mystery_report                       | creative_content (英語ブログ原稿)                                        |
| **Illustrator**       | トップ画像生成                                       | creative_content                     | visual_assets (Imagen 3 によるトップ画像1枚)                             |
| **Translator**        | 英語→多言語翻訳（3言語並列）                         | creative_content + structured_report | translation*result*{lang} (各言語翻訳)                                   |
| **Publisher**         | 納品・公開（EN+JA両方保存）                          | 全アセット                           | published_episode (Firestore 保存、管理画面反映)                         |

**Translator Factory パターン（`mystery_agents/agents/translator.py`）:**

- `create_translator(lang)` → 単一言語の `LlmAgent` を返す
- `create_all_translators()` → 3言語分の dict を返す
- `translator_agent = create_translator("ja")` で後方互換維持（Curator での利用）

**状態遷移:**

```
pending (EN原文 + 翻訳あり) → (Approve) → published
```

- `translating` ステータスは新規記事では不要（後方互換のため型定義には残す）

**Firestore フィールド命名規則:**

- ベースフィールド (`title`, `summary`, `narrative_content` 等) → **英語**（原文）
- `translations` map (`translations.ja.title`, `translations.es.summary` 等) → **各言語翻訳**（新方式）
- `*_ja` サフィックス → **レガシー**（後方互換用、`localizeMystery()` がフォールバックで参照）
- `*_en` フィールド → 非推奨（レガシー、後方互換用）

**翻訳対象フィールド（translations map 内）:**

- `title`, `summary`, `narrative_content`
- `discrepancy_detected`, `hypothesis`, `alternative_hypotheses`
- `historical_context.political_climate`, `story_hooks`
- `evidence_a_excerpt`, `evidence_b_excerpt`, `additional_evidence_excerpts`
- `confidence_rationale`

### Podcast 作成パイプライン（`podcast_agents/`）

管理画面から公開済み記事に対してオンデマンドで実行。

| エージェント      | 役割                         | 入力                              | 出力                                                        |
| ----------------- | ---------------------------- | --------------------------------- | ----------------------------------------------------------- |
| **ScriptPlanner** | 脚本アウトライン設計         | creative_content                  | script_outline (セグメント構成・語数配分)                   |
| **Scriptwriter**  | セグメント単位の逐次脚本執筆 | creative_content + script_outline | podcast_script (構造化台本)                                 |
| **Producer**      | 音声表現                     | podcast_script                    | audio_assets (Chirp 3 / TTS によるバイリンガル音声ファイル) |

### Podcast 配信戦略

#### ホスティング: Acast

- **プラットフォーム**: [Acast](https://www.acast.com/)（Starter 無料プラン）
- **配信先**: Acast 経由で Apple Podcasts, Amazon Music 等に配信
- **広告マネタイズ**: 月間 1,000 リスナー到達後、Acast マーケットプレイスで広告収益化（日本対応）

#### 番組フォーマット

- **尺**: 約 20 分/エピソード
- **配信頻度**: 週 1 回
- **コンテンツ**: その週に公開されたブログ記事を題材にエピソードを制作
- **広告**: Acast の広告を挿入（preroll / midroll / postroll）
- **AI 開示**: Acast の AI ガイドラインに従い、番組説明文とエピソード冒頭で AI 生成（Google Cloud TTS）である旨を明記

#### 運用フロー（現在: 手動）

```
1. ブログ記事が公開される（週次）
2. Podcast パイプライン実行（python -m podcast_agents）
   → Scriptwriter: 週の公開記事から台本生成
   → Producer: TTS で音声生成（MP3）
3. 生成された MP3 をダウンロード
4. Acast CMS に手動でアップロード・公開
```

#### 段階的自動化ロードマップ

| Phase     | 条件                | 運用                                   | コスト           |
| --------- | ------------------- | -------------------------------------- | ---------------- |
| 1（現在） | —                   | 手動アップロード                       | 無料（Starter）  |
| 2         | 月間 1,000 リスナー | 広告マネタイズ有効化、エピソード無制限 | 無料             |
| 3         | 収益安定            | Acast Publishing API で自動配信        | €29.99/月（Ace） |

#### 音声技術要件

- **フォーマット**: MP3 / 128 kbps / 最大 150MB
- **カバーアート**: JPG or PNG / 1400x1400 〜 3000x3000 px（1:1 正方形）

### Agent Roles（詳細）

**Librarian（司書）**

- 検索対象: 世界の公開デジタルアーカイブ（LOC, Europeana, Internet Archive, Delpher, NDL, Trove 等）＋ **Folklore, Legends, Myths, Local Beliefs**
- 歴史的記録と民俗資料の両方を収集し、Fact と Folklore の素材を揃える

**Scholar（学者）** — 分析モード + 討論モード（5学術領域: 歴史学・民俗学・文化人類学・言語学・文書館学）

- **分析モード**: 各言語の一次資料を5つの学術領域の視点で分析し、矛盾・アノマリーを特定（output*key: `scholar_analysis*{lang}`）
- **討論モード**: LoopAgent 内で他言語の分析を読み、反論・補強・統合提案をホワイトボードに記録（`append_to_whiteboard` ツール使用）
- 矛盾検出: 日付の不一致、人物の消失、記録の欠落など
- **民俗学的アノマリーの特定**: 説明のつかない現象、地元の禁忌、繰り返される怪異パターン
- **事実と伝説の相関分析**: 実際の事件がどのように伝説化したか、逆に伝説の背後にある史実は何か
- **文化人類学的分析**: 儀礼・社会構造・権力関係・物質文化・口承伝統・異文化接触の視点
- **言語学的分析**: 異なる言語間の記述の差異、翻訳による情報の変質・欠落
- **文書館学的分析**: アーカイブの選別バイアス、記録の不在が語るもの、保存と破棄の政治学

**Armchair Polymath（安楽椅子の博学者）**

- CrossReferenceScholar の後継。書斎から他者の研究成果を俯瞰し、辛辣かつ学術的権威をもって統合分析を行う
- 全言語の Scholar 分析結果（`scholar_analysis_*`）と討論ホワイトボード（`debate_whiteboard`）を読み、言語横断の矛盾・相関を特定
- `save_structured_report` を必ず呼び出し、`mystery_report` を出力（下流互換維持）

**Storyteller（語り部）**

- **歴史的厳密さ**と**怪異的情緒**を両立させたブログ記事の作成
- センセーショナリズムに走らず、学術的誠実さを保ちながらも、読者の好奇心を刺激する構成

**Translator（翻訳家）** — Factory パターン × 3言語

- 英語記事を3言語（ja/es/de）に並列翻訳
- 各言語に専用のトーンガイドライン（ja: 怪異情緒、es: lo misterioso、de: Unheimlichkeit）
- 歴史用語・民俗学用語の正確な翻訳、Fact × Folklore のニュアンス維持
- ブログパイプライン内で Illustrator と並列実行（`mystery_agents/agents/translator.py`）
- `create_translator(lang)` / `create_all_translators()` Factory パターン

**ScriptPlanner（脚本設計者）**

- ブログ記事を分析し、5〜7セグメントのアウトライン（キーポイント・語数配分・トーン指示）を設計
- `save_script_outline` ツールで構造化アウトラインをセッション状態に保存

**Scriptwriter（脚本家）**

- ScriptPlanner のアウトラインに基づき、セグメント単位で逐次脚本を執筆（多段階生成）
- 各セグメントを `save_segment` で蓄積し、`finalize_script` で最終スクリプトを組み立て
- 音声で聴いて理解しやすい形にコンテンツを再構成

### Agent Workflow

#### ブログ作成パイプライン（`mystery_agents/`）

```
ParallelAPILibrarians(6 API groups) → Aggregator → DynamicScholarBlock(分析+討論)
  → [PolymathGate] → ArmchairPolymath → [StorytellerGate] → Storyteller(EN)
  → [PostStoryGate] → Parallel(Illustrator, ParallelTranslators(3言語)) → Publisher → Firestore
```

- API ベース Librarian（US Archives, Europeana, Internet Archive, Delpher, NDL, Trove）がテーマに応じて自律検索
- AggregatorAgent（LLM 不使用）が raw_search_results を言語別に集約 → `collected_documents_{lang}` に書き込み
- DynamicScholarBlock（BaseAgent）が `active_languages` に基づき Scholar を動的生成
  - Phase 1: ドキュメントがある言語の Scholar のみ並列分析
  - Phase 2: 有意な分析が2言語以上なら討論ループ（最大2ラウンド、収束判定で早期終了）
  - 討論 instruction には参加言語のみ記載（肥大化防止）
  - 収束判定は LLM を介さず純粋関数で直接実行
- Scholar は分析モードと討論モードの2つを持つ（`create_scholar(lang, mode, active_langs)`）
- 討論モードの Scholar は `append_to_whiteboard` ツールで共有ホワイトボードに発言を記録
- ParallelTranslators は3言語の翻訳を並列実行する（`create_all_translators()`）
- Approve 時は翻訳不要（ステータス変更のみ）

**パイプラインゲート（カスケード障害対策）:**

| ゲート          | チェック対象                 | スキップ条件                           |
| --------------- | ---------------------------- | -------------------------------------- |
| ScholarGate     | `collected_documents_{lang}` | 全 Librarian が NO_DOCUMENTS_FOUND     |
| PolymathGate    | `scholar_analysis_{lang}`    | 全 Scholar が INSUFFICIENT_DATA        |
| StorytellerGate | `mystery_report`             | mystery_report が空または失敗マーカー  |
| PostStoryGate   | `creative_content`           | creative_content が空または NO_CONTENT |

- 各ゲートは `before_agent_callback` で実装（`mystery_agents/agents/pipeline_gate.py`）
- ゲート発動時は `shared/pipeline_failure.py` で Firestore の `pipeline_failures` コレクションに記録
- Curator がテーマ提案時に `pipeline_failures` を参照し、類似テーマの再提案を回避する

#### Podcast 作成パイプライン（`podcast_agents/`）

```
Firestore (narrative_content) → ScriptPlanner(アウトライン設計) → Scriptwriter(セグメント逐次生成) → Translator(JA) → Firestore
```

管理画面の「Podcast 作成」ボタンからオンデマンドで起動。

### Session State Keys

各エージェントは `output_key` を使用してセッション状態にデータを保存：

**ブログパイプライン（`mystery_agents`）:**

output_key ベース:

- `collected_documents_{lang}` - Librarian が収集した資料（デジタルアーカイブ＋Folklore両方を含む）
- `scholar_analysis_{lang}` - Scholar（分析モード）の分析レポート
- `mystery_report` - Armchair Polymath の統合分析レポート（下流互換維持）
- `creative_content` - Storyteller の英語ブログ原稿
- `visual_assets` - Illustrator のトップ画像アセット
- `translation_result_{lang}` - Translator の翻訳結果（ja, es, de 各言語、JSON形式）
- `published_episode` - Publisher の公開結果

tool_context.state ベース（構造化データ、LLM を経由しない正確なデータ）:

- `raw_search_results` - Librarian ツールが直接書き込む検索結果リスト（URL, 日付, タイトル等）
- `debate_whiteboard` - Scholar（討論モード）が `append_to_whiteboard` で累積書き込みする討論記録（`""` で初期化）
- `structured_report` - Armchair Polymath の `save_structured_report` ツールが書き込む構造化分析JSON
- `image_metadata` - Illustrator の `generate_image` ツールが書き込む画像メタデータ
- `archive_images` - Librarian ツールが蓄積するアーカイブ資料画像リスト（title, source_url, thumbnail_url, image_url, source_type, date）

**Podcast パイプライン（`podcast_agents`）:**

output_key ベース:

- `creative_content` - Firestore の narrative_content から事前セット
- `script_outline` - ScriptPlanner のテキストアウトライン
- `podcast_script` - Scriptwriter のポッドキャスト台本（全文テキスト）
- `podcast_script_ja` - Podcast Translator の日本語訳
- `audio_assets` - Producer の音声アセット

tool_context.state ベース:

- `structured_outline` - ScriptPlanner の `save_script_outline` ツールが書き込む構造化アウトライン JSON
- `segment_buffer` - Scriptwriter の `save_segment` で蓄積するセグメントリスト
- `structured_script` - Scriptwriter の `finalize_script` が書き込む最終構造化スクリプト JSON

### Models

全モデルは `shared/model_config.py` 経由で `HttpRetryOptions`（指数バックオフ + ジッター）付きで構成される。
ADK はデフォルトでリトライしないため、明示的な設定が必須。

- **ThemeAnalyzer:** gemini-2.5-flash (テーマ分析・言語選択)
- **Librarian:** gemini-2.5-flash (資料検索)
- **Scholar:** gemini-3-pro-preview (学際的分析 + 討論)
- **Armchair Polymath:** gemini-3-pro-preview (学際統合分析)
- **Storyteller:** claude-sonnet-4-5-20250929 (ブログ記事生成 — Anthropic API 直接利用)
- **Translator:** gemini-2.5-flash (英日翻訳)
- **ScriptPlanner:** gemini-2.5-flash (脚本アウトライン設計)
- **Scriptwriter:** gemini-3-pro-preview (ポッドキャスト脚本・セグメント逐次生成)
- **Illustrator:** gemini-3-pro-preview + Imagen 3 (トップ画像生成)
- **Producer:** gemini-3-pro-preview + Chirp 3 / TTS (音声生成)
- **Publisher:** Custom Agent (LLM 不使用、BaseAgent 直接実行)

## Mystery ID 命名規則

### v1 形式（US のみ — 既存記事で使用中）

FBI Central Records System および米国議会図書館分類法を参考に設計。

```
{分類3文字}-{州2文字}-{エリア3桁}-{YYYYMMDDHHMMSS}
例: OCC-MA-617-20260207143025
```

### v2 形式（グローバル対応 — 設計案、実装は #176）

```
{分類3文字}-{国ISO2文字}-{地域IATA3-5文字}-{YYYYMMDDHHMMSS}
例: OCC-US-BOS-20260207143025 (アメリカ・ボストン)
    FLK-GB-EDI-20260301120000 (イギリス・エディンバラ)
    HIS-JP-KYO-20260315090000 (日本・京都)
```

設計原則:
- **国コード**: ISO 3166-1 alpha-2（2文字）
- **地域コード**: IATA 空港コードまたは略称（3〜5文字）
- **後方互換**: v1 形式の既存 ID は変更しない（v2 は新規記事のみ適用）

### 分類コード（Classification — v1/v2 共通）

| コード | 分類       | 説明                                       |
| ------ | ---------- | ------------------------------------------ |
| HIS    | 歴史       | 歴史的記録の矛盾、消失した人物、文書の欠落 |
| FLK    | 民俗       | 地方伝承、祭り、口承伝統、民間信仰         |
| ANT    | 人類学     | 儀礼、社会構造、物質文化、異文化接触       |
| OCC    | 怪奇       | 説明不能な現象、超常的事象                 |
| URB    | 都市伝説   | 近代の噂話、現代の怪談                     |
| CRM    | 未解決事件 | 未解決犯罪、失踪事件、謎の死               |
| REL    | 信仰・禁忌 | 宗教的タブー、呪い、カルト                 |
| LOC    | 地霊・場所 | 特定の場所に紐づく怪異、心霊スポット       |

詳細定義: `mystery_agents/schemas/mystery_id.py`

## ADK 規約・ベストプラクティス

本プロジェクトでは ADK（Agent Development Kit）の規約とベストプラクティスに必ず従うこと。

- **エージェント定義・パイプライン構成の変更時は必ず `/adk` スキルをロードしてから着手する**（対象: `agents/` 配下、`agent.py`、パイプライン構成変更、新エージェント追加）

### エージェントパッケージ構成

- 各パイプラインは独立したパッケージ（`mystery_agents/`, `curator_agents/`, `podcast_agents/`）として構成する
- パッケージ直下の `agent.py` に `root_agent` 変数を定義する（ADK ローダーの発見規約）
- `__init__.py` で `from . import agent` をエクスポートする
- `curator_agents` は `agent.py` / `root_agent` を持たない（単一エージェント定義のみ、`services/curator.py` から直接使用される）

### レイヤー分離

- **エージェント定義**（instruction, model, output_key）は各パッケージの `agents/` に配置
- **ドメイン固有ツール**（publish_mystery, save_podcast_result 等）は各パッケージの `tools/` に配置
- **インフラ層**（Firestore 接続, Cloud Storage 接続）は `shared/` で一元管理し、各パッケージから import する

### コード原則

- エージェントの instruction 内で `{session_state_key}` プレースホルダーを使用してセッション状態を参照する
- 各エージェントは前段の失敗マーカー（`NO_DOCUMENTS_FOUND`, `NO_CONTENT` 等）をチェックし、適切に中断する
- Firebase Admin SDK はシングルトン（`firebase_admin._apps`）で管理されるため、初期化は `shared/firestore.py` に集約する

## Prompt Language Policy

- すべてのエージェントプロンプト（instruction文字列）は英語で記述する
- 各プロンプトの直上に、プロンプト全文を日本語に翻訳したコメントブロックを必ず添える
- 英語プロンプトを修正した場合は、対応する日本語コメントも必ず同時に更新する
- 英語と日本語は意味的に等価であること

フォーマット:

```python
# === 日本語訳 ===
# （英語プロンプトの日本語翻訳）
# === End 日本語訳 ===
AGENT_INSTRUCTION = """English prompt here..."""
```

## Project Structure

```
shared/                       # インフラ共有層
├── firestore.py              # Firebase Admin 初期化, Firestore/Storage クライアント
├── model_config.py           # LLM モデル設定（リトライ付き Gemini ファクトリ）
├── pipeline_failure.py       # パイプライン失敗ログ（Firestore 記録 + Curator 連携）

mystery_agents/               # ブログ作成パイプライン（旧 archive_agents）
├── __main__.py               # python -m mystery_agents エントリポイント
├── agent.py                  # root_agent = ghost_commander
├── agents/                   # 各エージェント定義
├── tools/                    # Publisher 用 Firestore/Storage ツール
└── utils/                    # PipelineLogger 等

curator_agents/               # テーマ提案エージェント
├── agents/                   # Curator エージェント定義
└── tools/                    # Curator 用ツール
                              # ※ agent.py / root_agent なし（services/curator.py から直接使用）

podcast_agents/               # Podcast 作成パイプライン
├── __main__.py               # python -m podcast_agents エントリポイント
├── agent.py                  # root_agent = podcast_commander
├── agents/                   # Scriptwriter, Producer
└── tools/                    # Podcast 用 Firestore ツール

services/                     # Cloud Run サービスエントリポイント
├── pipeline_server.py        # パイプライン Cloud Run サービス（Blog/Podcast）
└── curator.py                # Curator Cloud Run サービス

packages/shared/              # web-admin / web-public 共有コード (@ghost/shared)
├── src/types/                # 型定義（mystery.ts: TranslatedContent, translations map 含む）
├── src/lib/firebase/         # Firebase クライアント設定
├── src/lib/firestore/        # Firestore 読み取りクエリ（getAllPublishedMysteriesMap 含む）
├── src/lib/localize.ts       # ローカライズ（localizeMystery, getTranslatedExcerpt）
├── src/lib/utils.ts          # ユーティリティ（cn 等）
└── src/components/           # 共通 UI コンポーネント

web-admin/                    # Next.js 管理画面（日本語表示優先）
web-public/                   # Next.js 公開サイト（4言語対応: en/ja/es/de）
docs/                         # ドキュメント（手順.md 等）

tests/                        # テストスイート
├── conftest.py               # pytest fixtures
├── unit/                     # 単体テスト
├── integration/              # 統合テスト（Firebase Emulator）
├── eval/                     # ADK 評価フレームワーク
└── fixtures/                 # テストデータ
```

## Testing

### Google ADK 公式テスト方針

本プロジェクトは [Google ADK 公式ドキュメント](https://google.github.io/adk-docs/evaluate/) に準拠したテスト戦略を採用する。

ADK が提供する3つのテスト方法：

1. **adk web** - インタラクティブな手動テスト・デバッグ
2. **adk eval** - Golden Dataset を使った CLI 評価
3. **pytest** - CI/CD 統合のための自動テスト

### テスト3層構造

| レイヤー        | 目的                                   | 外部依存          | 実行頻度   |
| --------------- | -------------------------------------- | ----------------- | ---------- |
| **Unit**        | スキーマ・ユーティリティの検証         | なし（全モック）  | 毎コミット |
| **Integration** | ツール間・エージェント間の連携         | Firebase Emulator | PR 時      |
| **ADK Eval**    | エージェント品質評価（Golden Dataset） | Vertex AI API     | リリース前 |

### テスト実行コマンド

```bash
# 全ユニットテスト
pytest tests/unit/ -v

# 統合テスト（Firebase Emulator 起動前提）
pytest tests/integration/ -m integration -v

# ADK 評価（API キー必要、時間がかかる）
pytest tests/eval/ -m adk_eval

# カバレッジ付き
pytest tests/unit/ --cov=mystery_agents --cov=podcast_agents --cov-report=html

# ADK CLI での評価
adk eval mystery_agents tests/eval/eval_sets/
```

### Firebase Emulator Setup

統合テストには Firebase Emulator が必要：

```bash
# Emulator 起動
firebase emulators:start --only firestore,storage

# 環境変数設定（別ターミナルで）
export FIRESTORE_EMULATOR_HOST=localhost:8080
export STORAGE_EMULATOR_HOST=localhost:9199

# 統合テスト実行
pytest tests/integration/ -v
```

### ADK Evaluation（Golden Dataset）

ADK 公式評価フレームワークの概念：

- **Golden Dataset** (`tests/eval/eval_sets/`) - エージェントの期待される動作を定義した「正解」データ
- **Trajectory Evaluation** - ツール呼び出しの経路が期待通りか評価
- **評価メトリクス**:
  - `tool_trajectory_avg_score` - ツール使用の正確性
  - `response_match_score` - 最終回答の品質（ROUGE-1）

### Mocking Strategy

- **外部 API** (`requests`): `responses` ライブラリでモック
- **Firestore/Storage**: 統合テストでは Emulator、ユニットテストでは `pytest-mock`
- **Gemini/Imagen**: `google.genai.Client` をモック
- **時刻**: `freezegun` でタイムスタンプ固定

### CI/CD Integration

GitHub Actions での推奨設定：

```yaml
# .github/workflows/test.yml
jobs:
  unit-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - run: pip install -e ".[dev]"
      - run: pytest tests/unit/ --cov

  integration-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - run: npm install -g firebase-tools
      - run: firebase emulators:exec --only firestore,storage "pytest tests/integration/"
```

### TDD（テスト駆動開発）方針

テストは仕様書である。「今こう動いている」の追認ではなく「こう動くべき」の定義を書く。

- **仕様先行**: テストを先に書き、ソースを後から書く。ソースを書いてからテストを合わせるのは禁止
- **闇雲に書かない**: テストを書くべき明確な仕様がないなら、テストは書かない
- コード変更前に必ず既存テストを確認・実行する
- テスト追加時は重複チェック必須（`pytest tests/ -v --collect-only -k "keyword"`）
- **コード変更・テスト追加時は必ず `/tdd` スキルをロードしてから着手する**（スキル内のワークフロー手順に従うため）
- 詳細なワークフロー・判断基準・アンチパターン集は `/tdd` スキルを参照
