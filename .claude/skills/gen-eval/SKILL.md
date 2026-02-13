---
name: gen-eval
description: "ADK エージェントの評価テストを生成。Golden Dataset・eval 検証テスト・handover テストを自動生成"
argument-hint: "[agent_module_path]"
disable-model-invocation: true
allowed-tools: Read, Glob, Grep, Bash, Write, Edit
---

# /gen-eval — ADK エージェント評価テスト自動生成

対象エージェントモジュールのパスを `$ARGUMENTS` で受け取り、以下の3つを生成する:

1. **Golden Dataset** — `tests/eval/eval_sets/{agent}_eval.json`
2. **Eval コンテンツ検証テスト** — `tests/eval/test_adk_eval.py` の `TestEvalSetContent` にメソッド追加
3. **Agent Handover テスト** — `tests/integration/test_agent_handover.py` にメソッド追加

## ワークフロー

`$ARGUMENTS` が空の場合は、エージェントモジュールパス（例: `mystery_agents/agents/scholar.py`）の指定を求める。

### Step 1: エージェントモジュール解析

`$ARGUMENTS` のファイルを読み取り、以下を抽出する:

- **name**: エージェント変数名（例: `scholar_agent`）
- **model**: モデル文字列（例: `gemini-3-pro-preview`）
- **output_key**: セッション状態の出力キー（例: `mystery_report`）
- **tools**: ツール関数のリスト（`tools=[]` パラメータから取得）
- **instruction**: instruction 文字列全体（`{placeholder}` パターンを探す）
- **failure_markers_checked**: 上流データでチェックする失敗マーカー（例: `NO_DOCUMENTS_FOUND`）
- **failure_markers_emitted**: 失敗時に出力するマーカー（例: `INSUFFICIENT_DATA`）

### Step 2: パイプラインコンテキスト決定

ファイルパスのプレフィックスからパイプラインを特定する:

| パスプレフィックス | パイプライン | コマンダー |
|-------------------|------------|-----------|
| `mystery_agents/` | mystery（ブログ） | `ghost_commander` |
| `podcast_agents/` | podcast | `podcast_commander` |

このスキルのディレクトリにある `agent-catalog.md` と照合し、以下を把握する:
- 前段エージェントとその `output_key`（このエージェントが読み取るセッション状態キー）
- 後段エージェント（存在する場合）
- このエージェントに期待される eval シナリオ

### Step 3: 既存テスト確認

重複を避けるため、既存テストをスキャンする:

1. **Eval set JSON**: `tests/eval/eval_sets/{agent_name}_eval.json` の存在確認
2. **Eval コンテンツテスト**: `tests/eval/test_adk_eval.py` 内の `test_{agent_name}_eval_covers` を検索
3. **Handover テスト**: `tests/integration/test_agent_handover.py` 内の `test_{agent_name}_output_key` を検索

何が存在し、何を生成する必要があるか報告する。

### Step 4: Golden Dataset 生成

`tests/eval/eval_sets/{agent_name}_eval.json` を作成または更新する。

このスキルのディレクトリにある `eval-set-format.md` で ADK eval_set JSON の正確なフォーマット仕様を確認する。`agent-catalog.md` でこのエージェントに期待される eval シナリオを確認する。

**ルール:**
- `eval_set_id`: `{agent_name}_eval_v1`
- `eval_id`: `{agent_name}_{scenario_snake_case}`
- `user_content.parts[0].text`: 必ず日本語で記述
- `intermediate_data.tool_uses`: 期待されるツールを `"args": {}`（空）で列挙。ツールなしのエージェントまたは失敗シナリオでは `[]`
- `final_response.parts[0].text`: `output_key` 名 + 期待キーワード（スペース区切り）。失敗シナリオでは失敗マーカーキーワード

ファイルが既に存在する場合は、既存の `eval_id` を `agent-catalog.md` の期待シナリオと比較し、不足シナリオのみ追加する。

### Step 5: Eval コンテンツ検証テスト生成

`tests/eval/test_adk_eval.py` の `TestEvalSetContent` クラスにメソッドを追加する。

**生成するテストメソッド**（既に存在する場合はスキップ）:

1. `test_{agent_name}_eval_covers_key_scenarios` — eval_set に期待されるシナリオの eval_id が含まれることを検証。`any("keyword" in eid.lower() for eid in eval_ids)` パターンで既存テストスタイルに合わせる
2. ツールを持つエージェントの場合: `intermediate_data.tool_uses` に期待されるツール名が含まれることを検証（`test_publisher_eval_covers_tool_usage` パターンに従う）
3. 失敗マーカーを出力するエージェントの場合: eval_set に失敗シナリオが存在することを検証

`TestEvalSetContent` の既存メソッドのコードスタイルに厳密に従う。追加 import は不要 — クラスのスコープで `json`, `Path`, `EVAL_SETS_DIR` が利用可能。

### Step 6: Agent Handover テスト生成

`tests/integration/test_agent_handover.py` の適切なクラスにメソッドを追加する。

**生成するテストメソッド**（既に存在する場合はスキップ）:

1. `test_{agent_name}_output_key` — `agent.output_key == "expected_key"` を検証（`TestSessionStateKeys` または `TestPodcastSessionStateKeys` に追加）
2. `test_{agent_name}_references_{predecessor_key}` — `"{predecessor_key}" in agent.instruction` を検証（`TestInstructionPlaceholders` または `TestPodcastInstructionPlaceholders` に追加）
3. `test_{agent_name}_checks_upstream_failure` — エージェントの instruction に上流の失敗マーカー文字列が含まれることを検証（`TestFailureMarkers` に追加。既にカバーされている場合はスキップ）
4. `test_{agent_name}_uses_correct_model` — `agent.model == "gemini-3-pro-preview"` を検証（`TestAgentModels` に追加）

既存テストメソッドの import パターンとアサーションパターンに厳密に従う。

### Step 7: 検証

生成したファイルが有効であることを構造テストで確認する:

```bash
pytest tests/eval/test_adk_eval.py::TestADKEvaluationSetup -v
pytest tests/eval/test_adk_eval.py::TestEvalSetContent -v
pytest tests/integration/test_agent_handover.py -v
```

結果を報告する。テストが失敗した場合は修正して再実行する。

## リファレンス

このスキルのディレクトリにある以下のファイルで詳細仕様を確認:

- **`agent-catalog.md`** — 全エージェント定義カタログ: プロパティ、パイプライン上の位置、期待される eval シナリオ
- **`eval-set-format.md`** — ADK eval_set JSON フォーマット仕様（annotated example 付き）
