# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

Ghost in the Archive - 公開デジタルアーカイブから歴史的ミステリーと民俗学的怪異を発掘し、物語・音声・プロダクトへと変換する自律型エージェント AI システム

### 設計思想：Fact × Folklore のハイブリッド

本システムは **歴史的事実（Fact-based）** と **民俗学的怪異・伝説（Folklore-based）** の両方をターゲットにする。

- **Fact（左脳的アプローチ）**: 歴史的記録の矛盾、日付の不一致、人物の消失など検証可能な歴史的アノマリー
- **Folklore（右脳的アプローチ）**: 地元の信仰、禁忌、都市伝説、未解決の怪異など文化的記憶

この二つを融合させた独自のナラティブを生成する。

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

## Multi-Agent System

2つの独立した ADK パイプラインで構成：

### ブログ作成パイプライン（`archive_agents/`）

| エージェント | 役割 | 入力 | 出力 |
|------------|------|------|------|
| **Librarian** | 資料調査・収集（デジタルアーカイブ＋民俗資料） | 調査クエリ | collected_documents |
| **Scholar** | 歴史学×民俗学×文化人類学の学際分析 | collected_documents | mystery_report |
| **Storyteller** | 歴史的厳密さと怪異的情緒の融合（ブログ記事） | mystery_report | creative_content (ブログ原稿) |
| **Visualizer** | トップ画像生成 | creative_content | visual_assets (Imagen 3 によるトップ画像1枚) |
| **Publisher** | 納品・公開 | 全アセット | published_episode (Firestore 保存、管理画面反映) |

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

**Scriptwriter（脚本家）**
- Storyteller のブログ記事をベースにポッドキャスト用の脚本を作成
- 音声で聴いて理解しやすい形にコンテンツを再構成

### Agent Workflow

#### ブログ作成パイプライン（`archive_agents/`）

```
Librarian → Scholar → Storyteller → Visualizer → Publisher → Firestore
```

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
- `visual_assets` - Visualizer のトップ画像アセット
- `published_episode` - Publisher の公開結果

**Podcast パイプライン（`podcast_agents`）:**
- `creative_content` - Firestore の narrative_content から事前セット
- `podcast_script` - Scriptwriter のポッドキャスト台本
- `audio_assets` - Producer の音声アセット

### Models

- **Librarian:** gemini-3-pro-preview (資料検索)
- **Scholar:** gemini-3-pro-preview (学際的分析)
- **Storyteller:** gemini-3-pro-preview (ブログ記事生成)
- **Scriptwriter:** gemini-3-pro-preview (ポッドキャスト脚本)
- **Visualizer:** gemini-3-pro-preview + Imagen 3 (トップ画像生成)
- **Producer:** gemini-3-pro-preview + Chirp 3 / TTS (音声生成)
- **Publisher:** gemini-3-pro-preview (データ整理・公開)

## ADK 規約・ベストプラクティス

本プロジェクトでは ADK（Agent Development Kit）の規約とベストプラクティスに必ず従うこと。

### エージェントパッケージ構成
- 各パイプラインは独立したパッケージ（`archive_agents/`, `podcast_agents/`）として構成する
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

web/                          # Next.js 管理画面・公開サイト
main.py                       # ブログパイプライン CLI
podcast_main.py               # Podcast パイプライン CLI
```
