# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

Ghost in the Archive - 米公文書館から歴史的ミステリーを発掘し、物語・音声・プロダクトへと変換する自律型エージェント AI システム

## Tech Stack

- **Infrastructure:** Google Cloud (Cloud Run, Cloud Scheduler)
- **AI/ML:** Vertex AI (Gemini Pro/Flash, Imagen 3, Chirp 3, Text-to-Speech)
- **Agent Framework:** Agent Development Kit (ADK)
- **Data:** BigQuery, Cloud Storage, Firestore
- **Web:** Next.js

## Multi-Agent System

ADK を使用した 6 つの専門エージェント構成：

| エージェント | 役割 | 入力 | 出力 |
|------------|------|------|------|
| **Librarian** | 資料調査・収集 | 調査クエリ | collected_documents |
| **Historian** | 資料精査・矛盾検出 | collected_documents | mystery_report |
| **Storyteller** | 脚本・構成 | mystery_report | creative_content (ブログ原稿、ポッドキャスト台本、デザインコンセプト案) |
| **Designer** | 視覚表現 | creative_content | visual_assets (Imagen 3 用プロンプト、生成画像) |
| **Producer** | 音声表現 | creative_content | audio_assets (Chirp 3 / TTS によるバイリンガル音声ファイル) |
| **Publisher** | 納品・公開 | 全アセット | published_episode (Firestore 保存、管理画面反映) |

### Agent Workflow

```
                    ┌─────────────┐
                    │  Librarian  │
                    │ (資料収集)   │
                    └──────┬──────┘
                           │ collected_documents
                           ▼
                    ┌─────────────┐
                    │  Historian  │
                    │ (矛盾検出)   │
                    └──────┬──────┘
                           │ mystery_report
                           ▼
                    ┌─────────────┐
                    │ Storyteller │
                    │ (脚本・構成) │
                    └──────┬──────┘
                           │ creative_content
              ┌────────────┼────────────┐
              ▼            ▼            ▼
       ┌──────────┐ ┌──────────┐ ┌──────────┐
       │ Designer │ │ Producer │ │          │
       │ (画像)   │ │ (音声)   │ │          │
       └────┬─────┘ └────┬─────┘ │          │
            │            │       │          │
            ▼            ▼       │          │
      visual_assets  audio_assets│          │
            │            │       │          │
            └────────────┴───────┘          │
                         │                  │
                         ▼                  │
                  ┌─────────────┐           │
                  │  Publisher  │◄──────────┘
                  │ (納品・公開) │
                  └─────────────┘
                         │
                         ▼
                    Firestore
```

### Session State Keys

各エージェントは `output_key` を使用してセッション状態にデータを保存：

- `collected_documents` - Librarian が収集した資料
- `mystery_report` - Historian の分析レポート
- `creative_content` - Storyteller のコンテンツ
- `visual_assets` - Designer の画像アセット
- `audio_assets` - Producer の音声アセット
- `published_episode` - Publisher の公開結果

### Models

- **Librarian:** gemini-2.5-flash (高速な資料検索)
- **Historian:** gemini-3-pro-preview (深い分析)
- **Storyteller:** gemini-3-pro-preview (クリエイティブ生成)
- **Designer:** gemini-3-pro-preview + Imagen 3 (画像生成)
- **Producer:** gemini-3-pro-preview + Chirp 3 / TTS (音声生成)
- **Publisher:** gemini-3-pro-preview (データ整理・公開)
