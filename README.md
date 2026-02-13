# Ghost in the Archive

**公開デジタルアーカイブから歴史的ミステリーと民俗学的怪異を発掘し、物語・音声・プロダクトへと変換する自律型エージェント AI システム**

## 1. プロジェクト概要

本プロジェクトは、米国議会図書館（LOC）、DPLA、NYPL、Internet Archive などの公開デジタルアーカイブに眠る膨大な歴史データから、AI エージェントが自律的に「謎」や「矛盾」を発掘し、現代的なコンテンツおよび物理プロダクトとして再構築する自律型メディア・コマースシステムです。

### 設計思想：Fact と Folklore の均衡（Equilibrium）

本システムは、**歴史的事実（Fact-based）** と **民俗学的怪異・伝説（Folklore-based）** の両方をターゲットにするハイブリッド設計を採用しています。

- **左脳的アプローチ（Fact）**: 歴史的記録の矛盾、日付の不一致、人物の消失など、検証可能な歴史的アノマリーの発見
- **右脳的アプローチ（Folklore）**: 地元の信仰、禁忌、都市伝説、未解決の怪異など、文化的記憶の再発見

この二つのアプローチを融合させることで、単なる歴史研究でも単なる怪談でもない、**独自のナラティブ**を生成します。

## 2. 3 つのコア・プロセス (Core Processes)

- **デジタル発掘 (Exhumation):** 公開デジタルアーカイブから、AI エージェントが「知の鉱脈」となる未解決の謎を特定します。歴史的記録の裏に隠された**地元の信仰、禁忌、未解決の怪異**の痕跡も探索対象とします。
- **マルチモーダル再構築 (Reconstruction):** Gemini を中心とした AI 群が、歴史的厳密さと怪異的情緒を両立させたブログ、Podcast 台本、BGM、プロダクトデザインを生成します。
- **アーティファクトの定着 (Establishment):** デジタルコンテンツの配信（Next.js, Spotify）と、物理的なプロダクト（T シャツ、メモ帳等）への還元を行います。

## 3. マルチエージェント構成 (Multi-Agent System)

ADK (Agent Development Kit) を活用した 2 つの独立したパイプラインで構成されます。

### ブログ作成パイプライン（`mystery_agents/`）

```
Librarian → Scholar → Storyteller → Visualizer → Publisher → Firestore
```

| エージェント | 役割 | 入力 | 出力 |
|------------|------|------|------|
| **Librarian** | 資料調査・収集（デジタルアーカイブ＋民俗資料） | 調査クエリ | collected_documents |
| **Scholar** | 歴史学×民俗学×文化人類学の学際分析 | collected_documents | mystery_report |
| **Storyteller** | 歴史的厳密さと怪異的情緒の融合（ブログ記事） | mystery_report | creative_content |
| **Visualizer** | トップ画像生成 | creative_content | visual_assets (Imagen 3) |
| **Publisher** | Firestore 保存・公開 | 全アセット | published_episode |

### Podcast 作成パイプライン（`podcast_agents/`）

管理画面から公開済み記事に対してオンデマンドで実行。

```
Firestore (narrative_content) → Scriptwriter → Producer → Firestore
```

| エージェント | 役割 | 入力 | 出力 |
|------------|------|------|------|
| **Scriptwriter** | ポッドキャスト脚本作成 | creative_content | podcast_script |
| **Producer** | 音声表現 | podcast_script | audio_assets (Chirp 3 / TTS) |

## 4. 技術スタック (Tech Stack)

- **Infrastructure:** Google Cloud (Cloud Run, Cloud Scheduler)
- **AI/ML:** Vertex AI (Gemini Pro, Imagen 3, Chirp 3, Text-to-Speech)
- **Agent Framework:** Agent Development Kit (ADK)
- **Data:** Cloud Storage, Firestore
- **Web:** Next.js

### Web Architecture

- **web-public**: SSG（Static Site Generation）で動作（`output: "export"`）
  - ビルド時に全ページを静的 HTML として生成
  - 記事更新時は Cloud Build で再ビルド・再デプロイ
- **web-admin**: クライアントサイドレンダリング（毎回 Firestore アクセス）

## 5. プロジェクト構成 (Project Structure)

```
ghostinthearchive/
├── shared/                       # インフラ共有層
│   └── firestore.py              # Firebase Admin 初期化, Firestore/Storage クライアント
│
├── mystery_agents/               # ブログ作成パイプライン
│   ├── agent.py                  # root_agent = ghost_commander
│   ├── agents/                   # 各エージェント定義
│   ├── tools/                    # Publisher 用 Firestore/Storage ツール
│   └── utils/                    # PipelineLogger 等
│
├── podcast_agents/               # Podcast 作成パイプライン
│   ├── agent.py                  # root_agent = podcast_commander
│   ├── agents/                   # Scriptwriter, Producer
│   └── tools/                    # Podcast 用 Firestore ツール
│
├── web/                          # Next.js 管理画面・公開サイト
├── main.py                       # ブログパイプライン CLI
├── podcast_main.py               # Podcast パイプライン CLI
├── CLAUDE.md                     # Claude Code 向けガイド
├── pyproject.toml                # プロジェクト設定・依存関係
└── uv.lock                       # 依存関係ロックファイル
```

## 6. セットアップ (Setup)

```bash
# 仮想環境の作成と有効化
uv venv
source .venv/bin/activate  # Windowsの場合: .venv\Scripts\activate

# 依存関係のインストール
uv sync

# 環境変数の設定
cp .env.example .env  # 必要に応じて編集
```

## 7. 使用方法 (Usage)

```bash
# デフォルトの調査クエリで実行
uv run python main.py

# カスタムクエリで実行
uv run python main.py "1840年代のボストンにおけるスペイン関連の歴史的矛盾を調査せよ"
```

## 8. TODO

- [ ] **CI/CD パイプライン構築**
  - [ ] `.github/workflows/test.yml` の作成
  - [ ] develop → main への PR 時に単体テスト自動実行
  - [ ] main へのマージ後に統合テスト実行（オプション）
  - [ ] テスト依存関係のインストール方法を修正（`pip install -e ".[dev]"` の代替）
- [ ] Cloud Run の `min-instances` 設定検討（コールドスタート vs 常時起動コスト）
