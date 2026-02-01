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

ADK (Agent Development Kit) を活用し、以下の 6 つの専門エージェントが協調動作します。

| エージェント | 役割 | 入力 | 出力 |
|------------|------|------|------|
| **Librarian** | 資料調査・収集（デジタルアーカイブ＋民俗資料） | 調査クエリ | 収集資料（Fact＋Folklore） |
| **Historian** | 矛盾検出＋民俗学的アノマリー分析 | 収集資料 | Mystery Report（事実と伝説の相関分析を含む） |
| **Storyteller** | 歴史的厳密さと怪異的情緒の融合 | Mystery Report | ブログ原稿、ポッドキャスト台本、デザインコンセプト案 |
| **Visualizer** | トップ画像生成 | ブログ原稿 | Imagen 3 によるトップ画像1枚 |
| **Producer** | 音声表現 | ポッドキャスト台本 | Chirp 3 / TTS によるバイリンガル音声ファイル |
| **Publisher** | 納品・公開 | 全アセット | Firestore 保存、管理画面反映 |

### Agent Workflow

```
                    ┌─────────────────────────────────────┐
                    │            Librarian                │
                    │   Fact（アーカイブ）＋ Folklore（民俗）  │
                    └─────────────────┬───────────────────┘
                                      │
                                      ▼
                    ┌─────────────────────────────────────┐
                    │            Historian                │
                    │  矛盾検出 ╳ 民俗学的アノマリー分析    │
                    │    （事実と伝説の Cross-reference）   │
                    └─────────────────┬───────────────────┘
                                      │
                                      ▼
                    ┌─────────────────────────────────────┐
                    │           Storyteller               │
                    │   歴史的厳密さ ⚖ 怪異的情緒の融合    │
                    └──────────┬──────────────────────────┘
                               │
              ┌────────────────┼────────────────┐
              ▼                ▼                ▼
         Visualizer        Producer         Publisher → Firestore
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
│   ├── visualizer.py      # ビジュアライザーエージェント（トップ画像生成）
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
