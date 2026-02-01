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
- **Data:** BigQuery, Cloud Storage, Firestore
- **Web:** Next.js

## Multi-Agent System

ADK を使用した 7 つの専門エージェント構成：

| エージェント | 役割 | 入力 | 出力 |
|------------|------|------|------|
| **Librarian** | 資料調査・収集（デジタルアーカイブ＋民俗資料） | 調査クエリ | collected_documents |
| **Historian** | 矛盾検出＋民俗学的アノマリー分析 | collected_documents | mystery_report |
| **Storyteller** | 歴史的厳密さと怪異的情緒の融合（ブログ記事） | mystery_report | creative_content (ブログ原稿) |
| **Scriptwriter** | ポッドキャスト脚本作成 | creative_content | podcast_script (ポッドキャスト台本) |
| **Visualizer** | トップ画像生成 | creative_content | visual_assets (Imagen 3 によるトップ画像1枚) |
| **Producer** | 音声表現 | podcast_script | audio_assets (Chirp 3 / TTS によるバイリンガル音声ファイル) |
| **Publisher** | 納品・公開 | 全アセット | published_episode (Firestore 保存、管理画面反映) |

### Agent Roles（詳細）

**Librarian（司書）**
- 検索対象: デジタルアーカイブ（LOC, DPLA, NYPL, Internet Archive）＋ **Folklore, Legends, Myths, Local Beliefs**
- 歴史的記録と民俗資料の両方を収集し、Fact と Folklore の素材を揃える

**Historian（歴史家）**
- 矛盾検出: 日付の不一致、人物の消失、記録の欠落など
- **民俗学的アノマリーの特定**: 説明のつかない現象、地元の禁忌、繰り返される怪異パターン
- **事実と伝説の相関分析**: 実際の事件がどのように伝説化したか、逆に伝説の背後にある史実は何か

**Storyteller（語り部）**
- **歴史的厳密さ**と**怪異的情緒**を両立させたブログ記事の作成
- センセーショナリズムに走らず、学術的誠実さを保ちながらも、読者の好奇心を刺激する構成

**Scriptwriter（脚本家）**
- Storyteller のブログ記事をベースにポッドキャスト用の脚本を作成
- 音声で聴いて理解しやすい形にコンテンツを再構成

### Agent Workflow

```
                    ┌───────────────────────────────┐
                    │          Librarian            │
                    │  Fact（アーカイブ）＋ Folklore（民俗）│
                    └───────────────┬───────────────┘
                                    │ collected_documents
                                    │ (FactとFolkloreの両素材)
                                    ▼
                    ┌───────────────────────────────┐
                    │          Historian            │
                    │   矛盾検出 ╳ 民俗学的アノマリー   │
                    │   (Cross-reference Analysis)  │
                    └───────────────┬───────────────┘
                                    │ mystery_report
                                    │ (Folkloric Context含む)
                                    ▼
                    ┌───────────────────────────────┐
                    │         Storyteller           │
                    │  歴史的厳密さ ⚖ 怪異的情緒     │
                    │      (ブログ記事)              │
                    └───────────────┬───────────────┘
                                    │ creative_content
              ┌─────────────────────┼─────────────────────┐
              ▼                     ▼                     ▼
       ┌──────────────┐      ┌──────────┐          ┌──────────┐
       │ Scriptwriter │      │Visualizer│          │          │
       │ (脚本)       │      │ (画像)   │          │          │
       └──────┬───────┘      └────┬─────┘          │          │
              │ podcast_script    │                 │          │
              ▼                   ▼                 │          │
       ┌──────────┐        visual_assets            │          │
       │ Producer │              │                  │          │
       │ (音声)   │              │                  │          │
       └────┬─────┘              │                  │          │
            │                    │                  │          │
            ▼                    │                  │          │
      audio_assets               │                  │          │
            │                    │                  │          │
            └────────────────────┴──────────────────┘          │
                                 │                             │
                                 ▼                             │
                          ┌─────────────┐                      │
                          │  Publisher  │◄─────────────────────┘
                          │ (納品・公開) │
                          └─────────────┘
                                 │
                                 ▼
                            Firestore
```

### Session State Keys

各エージェントは `output_key` を使用してセッション状態にデータを保存：

- `collected_documents` - Librarian が収集した資料（デジタルアーカイブ＋Folklore両方を含む）
- `mystery_report` - Historian の分析レポート
  - **Folkloric Context 属性を含む**: 事実と伝説の相関、民俗学的アノマリー、地域の信仰・禁忌への言及
- `creative_content` - Storyteller のブログ原稿
- `podcast_script` - Scriptwriter のポッドキャスト台本
- `visual_assets` - Visualizer のトップ画像アセット
- `audio_assets` - Producer の音声アセット
- `published_episode` - Publisher の公開結果

### Models

- **Librarian:** gemini-3-pro-preview (資料検索)
- **Historian:** gemini-3-pro-preview (深い分析)
- **Storyteller:** gemini-3-pro-preview (ブログ記事生成)
- **Scriptwriter:** gemini-3-pro-preview (ポッドキャスト脚本)
- **Visualizer:** gemini-3-pro-preview + Imagen 3 (トップ画像生成)
- **Producer:** gemini-3-pro-preview + Chirp 3 / TTS (音声生成)
- **Publisher:** gemini-3-pro-preview (データ整理・公開)
