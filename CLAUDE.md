# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

Ghost in the Archive - 公開デジタルアーカイブから歴史的ミステリーと民俗学的怪異を発掘し、物語・音声・プロダクトへと変換する自律型エージェント AI システム

### 設計思想：Fact × Folklore のハイブリッド

本システムは **歴史的事実（Fact-based）** と **民俗学的怪異・伝説（Folklore-based）** の両方をターゲットにする。

- **Fact（左脳的アプローチ）**: 歴史的記録の矛盾、日付の不一致、人物の消失など検証可能な歴史的アノマリー
- **Folklore（右脳的アプローチ）**: 地元の信仰、禁忌、都市伝説、未解決の怪異など文化的記憶

この二つを融合させた独自のナラティブを生成する。

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

## Tech Stack

- **Infrastructure:** Google Cloud (Cloud Run, Cloud Scheduler)
- **AI/ML:** Vertex AI (Gemini Pro/Flash, Imagen 3, Chirp 3, Text-to-Speech)
- **Agent Framework:** Agent Development Kit (ADK)
- **Data:** Cloud Storage, Firestore
- **Web:** Next.js

## Web Architecture (ISR)

- Next.js は ISR（Incremental Static Regeneration）で動作
- 公開ページ（`/`, `/mystery/[id]`）: `revalidate = 86400`（24時間キャッシュ）
  - 24時間以内のアクセスは Firestore にアクセスせずキャッシュを返す
  - 記事公開・承認時は `/api/revalidate` で即座にキャッシュ破棄
- 管理画面（`/admin`）: クライアントサイドレンダリング（毎回 Firestore アクセス）
- 記事更新頻度: 1日最大1回

## TODO

- [ ] Cloud Run の `min-instances` 設定検討（コールドスタート vs 常時起動コスト）
- [ ] ADK 評価実行テストの CI/CD 統合（`GOOGLE_CLOUD_PROJECT` 環境変数設定、Vertex AI API 認証）
- [ ] Librarian エージェントのリンク品質検証機能
  - 取得した資料リンクの疎通確認（HTTP HEAD リクエストでリンク切れ検出）
  - リンク先コンテンツと資料メタデータの整合性検証（誤ったリンクの除外）
- [ ] Illustrator エージェントの画像生成堅牢化
  - 記事内容との整合性を検証し、不適切な画像は再生成
  - 画像生成失敗時のリトライ・フォールバック機構（プロンプト調整による再試行）
- [ ] 管理画面の記事一覧 UI 改善（段階的対応）
  - Phase 1（30件〜）: 検索バー + 人気タグ表示
  - Phase 2（50件〜）: Era/地域ファセットフィルタ
  - Phase 3（100件〜）: ページネーション

## Multi-Agent System

2つの独立した ADK パイプラインで構成：

### ブログ作成パイプライン（`archive_agents/`）

| エージェント | 役割 | 入力 | 出力 |
|------------|------|------|------|
| **Librarian** | 資料調査・収集（デジタルアーカイブ＋民俗資料） | 調査クエリ | collected_documents |
| **Scholar** | 歴史学×民俗学×文化人類学の学際分析 | collected_documents | mystery_report |
| **Storyteller** | 歴史的厳密さと怪異的情緒の融合（ブログ記事） | mystery_report | creative_content (ブログ原稿) |
| **Illustrator** | トップ画像生成 | creative_content | visual_assets (Imagen 3 によるトップ画像1枚) |
| **Publisher** | 納品・公開 | 全アセット | published_episode (Firestore 保存、管理画面反映) |

### 翻訳パイプライン（`translator_agents/`）

管理画面で Approve ボタン押下時に自動実行。翻訳完了後に公開される。

| エージェント | 役割 | 入力 | 出力 |
|------------|------|------|------|
| **Translator** | 日本語→英語翻訳 | narrative_content, title, summary 等 | 英語翻訳フィールド（*_en） |

**状態遷移:**
```
pending → (Approve) → translating → (翻訳完了) → published
```

**翻訳対象フィールド:**
- `title` → `title_en`
- `summary` → `summary_en`
- `narrative_content` → `narrative_content_en`
- `discrepancy_detected` → `discrepancy_detected_en`
- `hypothesis` → `hypothesis_en`
- `alternative_hypotheses` → `alternative_hypotheses_en`
- `historical_context.political_climate` → `historical_context_en.political_climate`

### Podcast 作成パイプライン（`podcast_agents/`）

管理画面から公開済み記事に対してオンデマンドで実行。

| エージェント | 役割 | 入力 | 出力 |
|------------|------|------|------|
| **Scriptwriter** | ポッドキャスト脚本作成 | creative_content (Firestoreから取得) | podcast_script (ポッドキャスト台本) |
| **Producer** | 音声表現 | podcast_script | audio_assets (Chirp 3 / TTS によるバイリンガル音声ファイル) |

### Agent Roles（詳細）

**Librarian（司書）**
- 検索対象: デジタルアーカイブ（LOC, DPLA, NYPL, Internet Archive）＋ **Folklore, Legends, Myths, Local Beliefs**
- 歴史的記録と民俗資料の両方を収集し、Fact と Folklore の素材を揃える

**Scholar（学者）**
- 矛盾検出: 日付の不一致、人物の消失、記録の欠落など
- **民俗学的アノマリーの特定**: 説明のつかない現象、地元の禁忌、繰り返される怪異パターン
- **事実と伝説の相関分析**: 実際の事件がどのように伝説化したか、逆に伝説の背後にある史実は何か
- **文化人類学的分析**: 儀礼・社会構造・権力関係・物質文化・口承伝統・異文化接触の視点

**Storyteller（語り部）**
- **歴史的厳密さ**と**怪異的情緒**を両立させたブログ記事の作成
- センセーショナリズムに走らず、学術的誠実さを保ちながらも、読者の好奇心を刺激する構成

**Translator（翻訳家）**
- 日本語記事を英語圏読者向けに翻訳
- 歴史用語・民俗学用語の正確な翻訳
- Fact × Folklore のニュアンス維持
- Atlas Obscura, Smithsonian Magazine のような読みやすさ

**Scriptwriter（脚本家）**
- Storyteller のブログ記事をベースにポッドキャスト用の脚本を作成
- 音声で聴いて理解しやすい形にコンテンツを再構成

### Agent Workflow

#### ブログ作成パイプライン（`archive_agents/`）

```
Librarian → Scholar → Storyteller → Illustrator → Publisher → Firestore
```

#### 翻訳パイプライン（`translator_agents/`）

```
Firestore (日本語記事) → Translator → Firestore (英語翻訳 + status=published)
```

管理画面の「Approve」ボタン押下時に自動起動。翻訳完了後に公開される。

#### Podcast 作成パイプライン（`podcast_agents/`）

```
Firestore (narrative_content) → Scriptwriter → Producer → Firestore (podcast_script, audio_assets)
```

管理画面の「Podcast 作成」ボタンからオンデマンドで起動。

### Session State Keys

各エージェントは `output_key` を使用してセッション状態にデータを保存：

**ブログパイプライン（`archive_agents`）:**
- `collected_documents` - Librarian が収集した資料（デジタルアーカイブ＋Folklore両方を含む）
- `mystery_report` - Scholar の分析レポート（Folkloric Context + Anthropological Context を含む）
- `creative_content` - Storyteller のブログ原稿
- `visual_assets` - Illustrator のトップ画像アセット
- `published_episode` - Publisher の公開結果

**翻訳パイプライン（`translator_agents`）:**
- `title`, `summary`, `narrative_content` 等 - Firestore から事前セット
- `translation_result` - Translator の翻訳結果（JSON形式）

**Podcast パイプライン（`podcast_agents`）:**
- `creative_content` - Firestore の narrative_content から事前セット
- `podcast_script` - Scriptwriter のポッドキャスト台本
- `audio_assets` - Producer の音声アセット

### Models

- **Librarian:** gemini-3-pro-preview (資料検索)
- **Scholar:** gemini-3-pro-preview (学際的分析)
- **Storyteller:** gemini-3-pro-preview (ブログ記事生成)
- **Translator:** gemini-3-pro-preview (日英翻訳)
- **Scriptwriter:** gemini-3-pro-preview (ポッドキャスト脚本)
- **Illustrator:** gemini-3-pro-preview + Imagen 3 (トップ画像生成)
- **Producer:** gemini-3-pro-preview + Chirp 3 / TTS (音声生成)
- **Publisher:** gemini-3-pro-preview (データ整理・公開)

## Mystery ID 命名規則

記事IDは FBI Central Records System および米国議会図書館分類法を参考に設計。

### ID形式

```
{分類3文字}-{州2文字}-{エリア3桁}-{YYYYMMDDHHMMSS}
例: OCC-MA-617-20260207143025
```

### 分類コード（Classification）

| コード | 分類 | 説明 |
|-------|------|------|
| HIS | 歴史 | 歴史的記録の矛盾、消失した人物、文書の欠落 |
| FLK | 民俗 | 地方伝承、祭り、口承伝統、民間信仰 |
| ANT | 人類学 | 儀礼、社会構造、物質文化、異文化接触 |
| OCC | 怪奇 | 説明不能な現象、超常的事象 |
| URB | 都市伝説 | 近代の噂話、現代の怪談 |
| CRM | 未解決事件 | 未解決犯罪、失踪事件、謎の死 |
| REL | 信仰・禁忌 | 宗教的タブー、呪い、カルト |
| LOC | 地霊・場所 | 特定の場所に紐づく怪異、心霊スポット |

### 地域コード

- **州コード**: USPS/ISO 3166-2:US 標準（2文字）
- **エリアコード**: 米国電話エリアコード（3桁）

主要エリアコード:
- BOSTON: MA-617, SALEM: MA-978
- NEW_YORK: NY-212, BROOKLYN: NY-718
- PHILADELPHIA: PA-215, CHICAGO: IL-312
- NEW_ORLEANS: LA-504, SAN_FRANCISCO: CA-415

詳細定義: `archive_agents/schemas/mystery_id.py`

## ADK 規約・ベストプラクティス

本プロジェクトでは ADK（Agent Development Kit）の規約とベストプラクティスに必ず従うこと。

### エージェントパッケージ構成
- 各パイプラインは独立したパッケージ（`archive_agents/`, `podcast_agents/`, `translator_agents/`）として構成する
- パッケージ直下の `agent.py` に `root_agent` 変数を定義する（ADK ローダーの発見規約）
- `__init__.py` で `from . import agent` をエクスポートする

### レイヤー分離
- **エージェント定義**（instruction, model, output_key）は各パッケージの `agents/` に配置
- **ドメイン固有ツール**（publish_mystery, save_podcast_result 等）は各パッケージの `tools/` に配置
- **インフラ層**（Firestore 接続, Cloud Storage 接続）は `shared/` で一元管理し、各パッケージから import する

### コード原則
- エージェントの instruction 内で `{session_state_key}` プレースホルダーを使用してセッション状態を参照する
- 各エージェントは前段の失敗マーカー（`NO_DOCUMENTS_FOUND`, `NO_CONTENT` 等）をチェックし、適切に中断する
- Firebase Admin SDK はシングルトン（`firebase_admin._apps`）で管理されるため、初期化は `shared/firestore.py` に集約する

## Project Structure

```
shared/                       # インフラ共有層
├── firestore.py              # Firebase Admin 初期化, Firestore/Storage クライアント

archive_agents/               # ブログ作成パイプライン
├── agent.py                  # root_agent = ghost_commander
├── agents/                   # 各エージェント定義
├── tools/                    # Publisher 用 Firestore/Storage ツール
└── utils/                    # PipelineLogger 等

podcast_agents/               # Podcast 作成パイプライン
├── agent.py                  # root_agent = podcast_commander
├── agents/                   # Scriptwriter, Producer
└── tools/                    # Podcast 用 Firestore ツール

translator_agents/            # 翻訳パイプライン
├── agent.py                  # root_agent = translator_commander
├── agents/                   # Translator
└── tools/                    # 翻訳用 Firestore ツール

web/                          # Next.js 管理画面・公開サイト
main.py                       # ブログパイプライン CLI
podcast_main.py               # Podcast パイプライン CLI
translate_main.py             # 翻訳パイプライン CLI

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

| レイヤー | 目的 | 外部依存 | 実行頻度 |
|---------|------|---------|---------|
| **Unit** | スキーマ・ユーティリティの検証 | なし（全モック） | 毎コミット |
| **Integration** | ツール間・エージェント間の連携 | Firebase Emulator | PR 時 |
| **ADK Eval** | エージェント品質評価（Golden Dataset） | Vertex AI API | リリース前 |

### テスト実行コマンド

```bash
# 全ユニットテスト
pytest tests/unit/ -v

# 統合テスト（Firebase Emulator 起動前提）
pytest tests/integration/ -m integration -v

# ADK 評価（API キー必要、時間がかかる）
pytest tests/eval/ -m adk_eval

# カバレッジ付き
pytest tests/unit/ --cov=archive_agents --cov=podcast_agents --cov-report=html

# ADK CLI での評価
adk eval archive_agents tests/eval/eval_sets/
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
          python-version: '3.12'
      - run: pip install -e ".[dev]"
      - run: pytest tests/unit/ --cov

  integration-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      - run: npm install -g firebase-tools
      - run: firebase emulators:exec --only firestore,storage "pytest tests/integration/"
```

### TDD（テスト駆動開発）方針

本プロジェクトでは TDD の原則に従って開発を進める。

#### コード修正時のワークフロー

1. **既存テストの確認**
   - 修正対象のコードに関連するテストが存在するか確認
   - `pytest tests/ -v --collect-only` で関連テストを特定
   - 既存テストがある場合は、まずそのテストを実行して現状を把握

2. **テスト追加の判断基準**
   以下のいずれかに該当する場合、先にテストを作成または更新する：
   - 新機能の追加（新しい関数・クラス・エンドポイント）
   - バグ修正（再発防止のためのリグレッションテスト）
   - 既存ロジックの変更（振る舞いが変わる修正）
   - リファクタリング（既存テストで振る舞いが保たれることを確認）

3. **テスト不要のケース**
   - ドキュメントのみの変更
   - コメントの追加・修正
   - 型ヒントの追加（ロジック変更なし）
   - 設定ファイルの軽微な調整

#### Red-Green-Refactor サイクル

```
1. Red:    失敗するテストを書く（期待する振る舞いを定義）
2. Green:  テストが通る最小限のコードを実装
3. Refactor: コードを整理（テストが通り続けることを確認）
```

#### 修正前チェックリスト

```bash
# 1. 関連テストの確認
pytest tests/ -v --collect-only -k "関連キーワード"

# 2. 既存テストの実行
pytest tests/unit/ -v

# 3. 修正後のテスト実行
pytest tests/unit/ -v --tb=short
```

#### テストファイルの配置規則

| 対象コード | テストファイル |
|-----------|---------------|
| `archive_agents/schemas/*.py` | `tests/unit/test_schemas.py` |
| `archive_agents/tools/*.py` | `tests/unit/test_*.py` or `tests/integration/test_*.py` |
| `archive_agents/utils/*.py` | `tests/unit/test_*.py` |
| `podcast_agents/**/*.py` | `tests/unit/test_*.py` or `tests/integration/test_*.py` |
| エージェント間連携 | `tests/integration/test_agent_handover.py` |
| エージェント品質 | `tests/eval/eval_sets/*.json` |
