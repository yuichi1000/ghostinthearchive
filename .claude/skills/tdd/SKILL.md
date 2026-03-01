---
name: tdd
description: "TDD ワークフロー・テスト配置規則・テスト肥大化防止ルール。コード修正・テスト追加時に参照"
disable-model-invocation: false
---

# /tdd — テスト駆動開発ガイド

## 核心哲学

**テストは仕様書である。**

テストの役割は「今こう動いている」の追認ではなく、「こう動くべき」の定義。ソースを書いてからテストを合わせるのは禁止。書くなら仕様を先に定義してからソースに取り掛かる。闇雲にテストを書かない。

## 判断基準フローチャート

```
テストを書くべきか？
│
├─ 新機能 → 仕様テスト先行（Red → Green → Refactor）
├─ バグ修正 → リグレッションテスト先行（バグ再現 → 修正 → Green）
├─ リファクタリング（振る舞い変更なし） → 既存テスト実行のみ、新規テスト不要
├─ 仕様が明確にならない → テスト不要（仕様が固まってから書く）
└─ ドキュメント/コメント/型ヒント/設定のみの変更 → テスト不要
```

## 仕様先行ワークフロー（必須手順、順序遵守）

### 1. 既存テストの確認

```bash
pytest tests/ -v --collect-only -k "keyword"
```

関連テストを特定し、現状のパス/フェイルを把握する。

### 2. 仕様をテストで定義する（Red）

コードを書く前に、期待する振る舞いをテストとして記述する。

```python
def test_calculate_ghost_confidence_returns_high_for_three_independent_sources():
    """3つ以上の独立資料がある場合、HIGH を返すべき。"""
    result = calculate_ghost_confidence(
        independent_sources=3,
        api_limitation_excluded=True,
        reproducible=True,
    )
    assert result == GhostConfidence.HIGH
```

このテストが **失敗する** ことを確認する。失敗しないなら、テストは既存の振る舞いの追認であり、新たに書く必要がない。

### 3. テストを通す最小限のコードを実装する（Green）

テストが通る最小限のコードだけを書く。余計な機能を足さない。

### 4. リファクタリング（Refactor）

テストが通り続けることを確認しつつコードを整理する。

### 5. 最終確認

```bash
pytest tests/unit/ -v --tb=short
```

## 良いアサーションの書き方

### 悪い例 → 良い例

**存在確認だけ（MagicMock でも通る）:**

```python
# BAD: 何が返ってきても通る
assert result is not None

# GOOD: 期待する値を具体的に検証
assert result == {"status": "success", "mystery_id": "OCC-MA-617-20260207143025"}
```

**部分文字列チェック（否定文にもマッチ）:**

```python
# BAD: "Do not continue investigating" にもマッチする
assert "continue" in result.lower()

# GOOD: 期待する構造を正確に検証
assert result["recommendation"] == "continue_investigating"
```

**定数の再確認（二重管理）:**

```python
# BAD: 定数を変更するたびにテストも変更が必要
assert MAX_DEBATE_ROUNDS == 2

# GOOD: 定数を使った振る舞いを検証する
debate = run_debate(rounds=MAX_DEBATE_ROUNDS + 1)
assert debate.actual_rounds == MAX_DEBATE_ROUNDS  # 上限で打ち切られる
```

**実装内部への結合（キー名リネームで即死）:**

```python
# BAD: instruction の文字列に依存
assert "{scholar_analysis_de}" in scholar.instruction

# GOOD: 実際にセッション状態のキーを参照できることを検証
state = {"scholar_analysis_de": "analysis data"}
result = scholar.process(state)
assert "analysis data" in result
```

**フレームワーク標準動作の再テスト:**

```python
# BAD: Pydantic が保証する動作をテスト
def test_missing_required_field_raises_error():
    with pytest.raises(ValidationError):
        MysteryReport()  # Pydantic の標準動作

# GOOD: プロジェクト固有のカスタムバリデーションをテスト
def test_mystery_id_rejects_invalid_classification_code():
    with pytest.raises(ValidationError, match="classification"):
        MysteryReport(mystery_id="XXX-MA-617-20260207143025")
```

## アンチパターン集（コードベースの実例）

| # | パターン | 悪い例 | 問題 |
|---|----------|--------|------|
| 1 | 存在確認だけ | `assert result is not None` | MagicMock でも通る。何が返るか不問 |
| 2 | 部分文字列チェック | `assert "continue" in result.lower()` | `"Do not continue"` にもマッチ |
| 3 | 定数の再確認 | `assert MAX_CALLS == 3` | 定数変更 = テスト修正の二重管理 |
| 4 | 実装文字列への結合 | `assert "{scholar_analysis_de}" in scholar.instruction` | キー名リネームで即死 |
| 5 | フレームワーク再テスト | `test_missing_required_field_raises_error` | Pydantic の標準動作を再検証 |

**対処法（共通）**: テストが検証すべきは「仕様として定義された振る舞い」。実装の内部構造やフレームワークが保証する動作ではない。

## テストで検証すべきもの / すべきでないもの

### テストすべきもの（プロジェクト固有の価値）

- カスタムバリデーション（`@field_validator`, `@model_validator`, `max_length` 等）
- ビジネスロジック関数（フィルタリング、変換、パース）
- 定数間の整合性（例: `TRANSLATION_LANGUAGES ⊂ ALLOWED_LANGUAGES`）
- モジュール間の再エクスポート一致
- エージェント間連携（output_key / プレースホルダーの静的検証）
- 耐障害性（外部サービス障害がメインプロセスを停止させないこと）
- 各スキーマの happy path（`test_valid_*`）— 契約ドキュメントとして 1 つ維持

### テストすべきでないもの（フレームワーク / 標準ライブラリの再テスト）

- Pydantic の標準動作: 必須フィールド検証、Enum 検証、Optional デフォルト、`default_factory`、`use_enum_values` config
- Enum 値の羅列チェック（値が変われば happy path テストも壊れる）
- ハードコード定数の値アサーション（設定値の変更 = テスト修正の二重管理）
- Python 標準機能: `frozen=True` dataclass の不変性、`isinstance` 型チェック

## モックよりフェイクを優先する

- 同じモック設定が 3 箇所以上で重複する場合は、フェイクオブジェクト（`tests/fakes.py`）を作成する
- フェイクは実際の API サーフェスのみ実装し、テストが何を検証しているか明確にする
- `AsyncMock` のチェーン（`mock.attr.attr = AsyncMock(return_value=...)`）が 3 段以上になる場合はフェイクに置き換えを検討する

## テスト肥大化防止ルール

- **1:1 マッピング**: 1つのソースモジュールにつきテストファイルは最大1つ。同一ソースモジュールに対する複数テストファイルが存在する場合は統合する
- **追加前に重複チェック**: `pytest tests/ -v --collect-only -k "function_name"` で同じ振る舞いのテストが既にないか確認してから追加する
- **インフラ制約で通らないテストは削除**: MagicMock 等の制約で意味のあるアサーションができないテストは保持しない（例: conftest が LlmAgent を MagicMock に置換する環境でのモデル名比較）
- **カバレッジ重複は統合**: 同一の振る舞いを検証する複数テストは1つに統合する
- **フレームワーク信頼の原則**: Pydantic / dataclass / Enum 等の標準動作はテスト不要。プロジェクト固有のカスタムバリデーションのみテストする

## テスト不要のケース

- ドキュメントのみの変更
- コメントの追加・修正
- 型ヒントの追加（ロジック変更なし）
- 設定ファイルの軽微な調整
- エージェントのモデル割当変更（ファクトリ関数の呼び出しテストでカバー済み、モデル名文字列の定数テストは不要）

## テスト命名規則

- **クラス名**: `TestFunctionNamePascalCase`（例: `TestPublishMystery`, `TestSanitizePrompt`）
- **メソッド名**: `test_function_name_scenario`（例: `test_publish_mystery_success`, `test_publish_mystery_invalid_json`）
- **docstring**: `"""Should <期待される振る舞い> when <条件>."""`

## テストファイル配置規則（1:1 マッピング）

| 対象コード | テストファイル |
|---|---|
| `mystery_agents/schemas/*.py` | `tests/unit/test_schemas.py` |
| `mystery_agents/tools/theme_analyzer_tools.py` | `tests/unit/test_theme_analyzer.py` |
| `mystery_agents/tools/debate_tools.py` | `tests/unit/test_debate_tools.py` |
| `mystery_agents/tools/scholar_tools.py` | `tests/unit/test_scholar_tools.py` |
| `mystery_agents/tools/publisher_tools.py` | `tests/unit/test_publisher_tools.py` |
| `mystery_agents/tools/illustrator_tools.py` | `tests/unit/test_illustrator_tools.py` |
| `mystery_agents/tools/search_utils.py` | `tests/unit/test_search_utils.py` |
| `mystery_agents/tools/link_validator.py` | `tests/unit/test_link_validator.py` |
| `mystery_agents/tools/bilingual_search.py` | `tests/unit/test_bilingual_search.py` |
| `mystery_agents/tools/ddb.py` | `tests/unit/test_ddb.py` |
| `mystery_agents/agents/illustrator.py`（callback） | `tests/unit/test_illustrator_callback.py` |
| `mystery_agents/agents/storyteller.py` | `tests/unit/test_storyteller.py` |
| `mystery_agents/agents/pipeline_gate.py` | `tests/unit/test_pipeline_gate.py` |
| `mystery_agents/agents/language_gate.py` | `tests/unit/test_language_gate.py` |
| `mystery_agents/utils/pipeline_logger.py` | `tests/unit/test_pipeline_logger.py` |
| `mystery_agents/agents/translator.py` | `tests/unit/test_translator_factory.py` |
| `shared/model_config.py` | `tests/unit/test_model_config.py` |
| `shared/pipeline_failure.py` | `tests/unit/test_pipeline_failure.py` |
| `shared/pipeline_run.py` | `tests/unit/test_pipeline_run.py` |
| `shared/orchestrator.py` | `tests/unit/test_orchestrator.py` |
| `services/pipeline_server.py` | `tests/unit/test_pipeline_server.py` |
| `services/curator.py` | `tests/unit/test_curator_server.py` |
| `podcast_agents/tools/script_tools.py`（save_podcast_script） | `tests/unit/test_script_tools.py` |
| `podcast_agents/tools/script_tools.py`（多段階生成ツール） | `tests/unit/test_script_planner_tools.py` |
| `podcast_agents/agents/script_planner.py` | `tests/unit/test_script_planner.py` |
| Publisher 多言語統合 | `tests/unit/test_publisher_multilingual.py` |
| テスト用フェイクオブジェクト | `tests/fakes.py` |
| エージェント間連携（統合） | `tests/integration/test_agent_handover.py` |
| Publisher ツール（統合） | `tests/integration/test_publisher_tools.py` |
| エージェント品質（eval） | `tests/eval/eval_sets/*.json` |

## リファレンス

- 依存別モックパターンの詳細は [mock-patterns.md](mock-patterns.md) を参照
- 既存テストの模範:
  - `tests/unit/test_illustrator_tools.py`（genai モック、リトライ、JSON アサーション）
  - `tests/integration/test_publisher_tools.py`（Firestore モック、emulator skip）
