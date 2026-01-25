# Ghost in the Archive

**米公文書館から歴史的ミステリーを発掘し、物語・音声・プロダクトへと変換する自律型エージェント AI システム**

## 1. プロジェクト概要

本プロジェクトは、米国議会図書館（LOC）や国立公文書館（NARA）に死蔵されている膨大な歴史データから、AI エージェントが自律的に「謎」や「矛盾」を発掘し、現代的なコンテンツおよび物理プロダクトとして再構築する自律型メディア・コマースシステムです。

## 2. 3 つのコア・プロセス (Core Processes)

- **デジタル発掘 (Exhumation):** 公文書データから、AI エージェントが「知の鉱脈」となる未解決の謎を特定します。
- **マルチモーダル再構築 (Reconstruction):** Gemini を中心とした AI 群が、ブログ、Podcast 台本、BGM、プロダクトデザインを生成します。
- **アーティファクトの定着 (Establishment):** デジタルコンテンツの配信（Next.js, Spotify）と、物理的なプロダクト（T シャツ、メモ帳等）への還元を行います。

## 3. マルチエージェント構成 (Multi-Agent System)

ADK (Agent Development Kit) を活用し、以下の 6 つの専門エージェントが協調動作します。

| エージェント | 役割 | 入力 | 出力 |
|------------|------|------|------|
| **Librarian** | 資料調査・収集 | 調査クエリ | 収集資料 |
| **Historian** | 資料精査・矛盾検出 | 収集資料 | Mystery Report |
| **Storyteller** | 脚本・構成 | Mystery Report | ブログ原稿、ポッドキャスト台本、デザインコンセプト案 |
| **Designer** | 視覚表現 | デザインコンセプト | Imagen 3 用プロンプト、生成画像 |
| **Producer** | 音声表現 | ポッドキャスト台本 | Chirp 3 / TTS によるバイリンガル音声ファイル |
| **Publisher** | 納品・公開 | 全アセット | Firestore 保存、管理画面反映 |

### Agent Workflow

```
Librarian → Historian → Storyteller → Designer  ─┐
                              │                   │
                              └──→ Producer ──────┼──→ Publisher → Firestore
```

## 4. 技術スタック (Tech Stack)

- **Infrastructure:** Google Cloud (Cloud Run, Cloud Scheduler)
- **AI/ML:** Vertex AI (Gemini Pro/Flash, Imagen 3, Chirp 3, Text-to-Speech)
- **Agent Framework:** Agent Development Kit (ADK)
- **Data:** BigQuery, Cloud Storage, Firestore
- **Web:** Next.js

## 5. プロジェクト構成 (Project Structure)

```
ghostinthearchive/
├── agents/                 # エージェントモジュール
│   ├── __init__.py
│   ├── librarian.py       # 司書エージェント（資料調査・収集）
│   ├── historian.py       # 歴史家エージェント（分析・矛盾発見）
│   ├── storyteller.py     # 物語作家エージェント（コンテンツ生成）
│   ├── designer.py        # デザイナーエージェント（画像生成）
│   ├── producer.py        # プロデューサーエージェント（音声生成）
│   └── publisher.py       # 発行者エージェント（配信）
├── tools/                  # エージェント用ツール
│   └── __init__.py
├── data/                   # 取得データの保存用
├── web/                    # Next.js フロントエンド
├── .env                    # 環境変数（Git管理外）
├── .gitignore
├── CLAUDE.md              # Claude Code向けガイド
├── main.py                # エントリーポイント
├── pyproject.toml         # プロジェクト設定・依存関係
├── README.md
└── uv.lock                # 依存関係ロックファイル
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
