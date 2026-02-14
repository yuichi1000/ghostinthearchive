---
name: tdd
description: "TDD ワークフロー・テスト配置規則・テスト肥大化防止ルール。コード修正・テスト追加時に参照"
disable-model-invocation: false
---

# /tdd — TDD ワークフロー・テスト配置規則

コード修正・テスト追加時に遵守すべきルールの全量。

## コード修正時のワークフロー（必須手順、順序遵守）

1. **コード変更前に既存テストを確認**
   - `pytest tests/ -v --collect-only -k "keyword"` で関連テストを特定
   - 既存テストがある場合は、まず実行して現状のパス/フェイルを把握

2. **テスト必要性の判断**（決定木）
   - 既存テストが要件をカバーしている → **テスト追加不要**
   - 新規関数/クラス → 失敗するテストを先に書く（Red）
   - バグ修正 → バグを再現するリグレッションテストを先に書く（Red）
   - 振る舞い変更 → 既存テストを新仕様に更新（Red）
   - リファクタリング（振る舞い変更なし） → 既存テスト実行のみ、新規テスト不要

3. **Red-Green-Refactor サイクル**
   ```
   Red:      テストが失敗することを確認
   Green:    テストが通る最小限のコードを実装
   Refactor: テストが通り続けることを確認しつつ整理
   ```

4. **最終確認**: `pytest tests/unit/ -v --tb=short`

## 量より質 — テストで検証すべきもの / すべきでないもの

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
