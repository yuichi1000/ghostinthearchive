# Ghost in the Archive

**米公文書館から歴史的ミステリーを発掘し、物語・音声・プロダクトへと変換する自律型エージェント AI システム**

## 1. プロジェクト概要

本プロジェクトは、米国議会図書館（LOC）や国立公文書館（NARA）に死蔵されている膨大な歴史データから、AI エージェントが自律的に「謎」や「矛盾」を発掘し、現代的なコンテンツおよび物理プロダクトとして再構築する自律型メディア・コマースシステムです。

## 2. 3 つのコア・プロセス (Core Processes)

- **デジタル発掘 (Exhumation):** 公文書データから、AI エージェントが「知の鉱脈」となる未解決の謎を特定します。
- **マルチモーダル再構築 (Reconstruction):** Gemini 1.5 を中心とした AI 群が、ブログ、Podcast 台本、BGM、プロダクトデザインを生成します。
- **アーティファクトの定着 (Establishment):** デジタルコンテンツの配信（Next.js, Spotify）と、物理的なプロダクト（T シャツ、メモ帳等）への還元を行います。

## 3. マルチエージェント構成 (Multi-Agent System)

ADK (Agent Development Kit) を活用し、以下の専門エージェントが協調動作します。

- **Librarian Agent (司書):** 公文書館 API から関連性の高い資料を調査・収集します。
- **Historian Agent (歴史家):** 資料を精査し、記述の矛盾や「歴史の空白」を見つけ出し分析します。
- **Storyteller Agent (物語作家):** 歴史の謎をブログ、Podcast、Imagen 3 によるデザインへと昇華させます。
- **Publisher Agent (発行者):** 各プラットフォーム（Spotify, Next.js, POD ショップ等）へ自動配信します。

## 4. 技術スタック (Tech Stack)

- **Infrastructure:** Google Cloud (Cloud Run, Cloud Scheduler)
- **AI/ML:** Vertex AI (Gemini Pro/Flash, Imagen 3, MusicFX, Text-to-Speech)
- **Agent Framework:** Agent Development Kit (ADK)
- **Data:** BigQuery, Cloud Storage
- **Web:** Next.js
