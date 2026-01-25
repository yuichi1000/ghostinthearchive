# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

Ghost in the Archive - 米公文書館から歴史的ミステリーを発掘し、物語・音声・プロダクトへと変換する自律型エージェント AI システム

## Tech Stack

- **Infrastructure:** Google Cloud (Cloud Run, Cloud Scheduler)
- **AI/ML:** Vertex AI (Gemini Pro/Flash, Imagen 3, MusicFX, Text-to-Speech)
- **Agent Framework:** Agent Development Kit (ADK)
- **Data:** BigQuery, Cloud Storage
- **Web:** Next.js

## Multi-Agent System

ADK を使用した 5 つの専門エージェント構成：

- **Librarian Agent:** 公文書館 API からの資料調査・収集（Gemini Flash）
- **Historian Agent:** 資料精査、矛盾・空白の初期検出（Gemini Flash）
- **Analyst Agent:** 深い推論、隠された真実の分析、Mystery Report 生成（Gemini Pro）
- **Storyteller Agent:** コンテンツ生成（ブログ、Podcast、デザイン）
- **Publisher Agent:** 各プラットフォームへの配信

### Agent Workflow

```
Librarian → Historian → Analyst → Storyteller → Publisher
   ↓           ↓           ↓
 data/     分析Context   Mystery Report
```
