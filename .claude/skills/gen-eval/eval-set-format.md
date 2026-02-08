# ADK Eval Set JSON フォーマット仕様

ADK 評価フレームワーク（`adk eval`）で使用する Golden Dataset JSON の正確なフォーマット定義。

## ファイル配置

```
tests/eval/eval_sets/{agent_name}_eval.json
```

## トップレベル構造

```json
{
  "eval_set_id": "{agent_name}_eval_v1",
  "name": "{Agent Name} Agent Evaluation",
  "description": "{Agent Name} の{機能}を full pipeline 経由でテスト",
  "eval_cases": [...]
}
```

| フィールド | 形式 | 例 |
|-----------|------|-----|
| `eval_set_id` | `{agent_name}_eval_v1` | `scholar_eval_v1` |
| `name` | `{Agent Name} Agent Evaluation` | `Scholar Agent Evaluation` |
| `description` | テスト範囲を説明する自由テキスト | `"Tests Scholar's interdisciplinary analysis capabilities via full pipeline execution"` |
| `eval_cases` | eval case オブジェクトの配列 | 下記参照 |

## Eval Case 構造

`eval_cases` の各要素:

```json
{
  "eval_id": "{agent_name}_{scenario_snake_case}",
  "conversation": [
    {
      "invocation_id": "inv_{NNN}",
      "user_content": {
        "role": "user",
        "parts": [
          {
            "text": "日本語のプロンプト"
          }
        ]
      },
      "intermediate_data": {
        "tool_uses": [],
        "intermediate_responses": []
      },
      "final_response": {
        "role": "model",
        "parts": [
          {
            "text": "output_key keyword1 keyword2"
          }
        ]
      }
    }
  ]
}
```

## フィールド仕様

### eval_id

形式: `{agent_name}_{scenario_snake_case}`

例:
- `scholar_fact_based_analysis`
- `librarian_no_results`
- `publisher_full_workflow`

### invocation_id

eval_set 内で連番: `inv_001`, `inv_002`, `inv_003`, ...

### user_content

- `role`: 常に `"user"`
- `parts[0].text`: **必ず日本語で記述する。** パイプラインが受け取るタスクを記述する。対象エージェントの特定の動作をトリガーする現実的な調査・分析リクエストを書く。

良い例:
```
"1842年3月のボストン港におけるスペイン船サンタマリア号の記録を分析してください。"
"ニューイングランドの漁村で1850年代に複数の漁師が同じ場所で不可解な現象を報告しています。"
```

失敗・エッジケースシナリオでは、明らかに不可能なリクエストを使用:
```
"2099年の火星植民地における歴史的事件について分析してください。"
```

### intermediate_data.tool_uses

期待されるツール呼び出しの配列。各ツールは名前のみ指定 — `args` は常に空の `{}`:

```json
"tool_uses": [
  {"name": "search_newspapers", "args": {}},
  {"name": "search_archives", "args": {}}
]
```

- **ツールなし**のエージェントの場合: `"tool_uses": []`
- **失敗シナリオ**の場合（ツールを持つエージェントでも）: `"tool_uses": []`
- `intermediate_responses`: 常に `[]`

### final_response

- `role`: 常に `"model"`
- `parts[0].text`: スペース区切りのキーワード。ROUGE-1 スコアリングで評価される（閾値: `test_config.json` の 0.5）。

**キーワード選択ルール:**

| シナリオ種別 | 含めるキーワード |
|-------------|----------------|
| 成功（通常） | `output_key` + ドメイン固有キーワード + `Firestore`（データ保存する場合） |
| 成功（ツール使用） | `output_key` + ツール関連の結果キーワード |
| 失敗（マーカー） | 失敗マーカーのみ（例: `NO_DOCUMENTS_FOUND`, `INSUFFICIENT_DATA NO_CONTENT`） |

例:
```json
// Scholar 成功
"text": "mystery_report DATE_MISMATCH EVENT_OUTCOME 仮説 Firestore"

// Scholar 民俗学
"text": "Folkloric Context RECURRING_PATTERN LOCAL_TABOO Firestore"

// Scholar 失敗
"text": "INSUFFICIENT_DATA NO_DOCUMENTS_FOUND"

// Librarian（ツール使用）
"text": "collected_documents total_found"

// Publisher（ツール使用）
"text": "published_episode Firestore mystery_id"
```

## Annotated Example（Scholar）

```json
{
  // eval_set_id は {agent}_eval_v1 規約に従う
  "eval_set_id": "scholar_eval_v1",
  "name": "Scholar Agent Evaluation",
  "description": "Tests Scholar's interdisciplinary analysis capabilities via full pipeline execution",
  "eval_cases": [
    {
      // eval_id: {agent}_{scenario}
      "eval_id": "scholar_fact_based_analysis",
      "conversation": [
        {
          // 連番の invocation ID
          "invocation_id": "inv_001",
          "user_content": {
            "role": "user",
            "parts": [
              {
                // 必ず日本語 — 現実的な分析リクエスト
                "text": "1842年3月のボストン港におけるスペイン船サンタマリア号の記録を分析してください。英語の新聞記事では船が消失したと報じていますが、スペイン語の記録では同じ船が2週間後にハバナに到着したと記載されています。"
              }
            ]
          },
          "intermediate_data": {
            // Scholar はツールなし — 空配列
            "tool_uses": [],
            "intermediate_responses": []
          },
          "final_response": {
            "role": "model",
            "parts": [
              {
                // output_key（mystery_report）+ ドメインキーワード
                "text": "mystery_report DATE_MISMATCH EVENT_OUTCOME 仮説 Firestore"
              }
            ]
          }
        }
      ]
    },
    {
      // 失敗シナリオ — エージェントはデータ不足を検出すべき
      "eval_id": "scholar_insufficient_data",
      "conversation": [
        {
          "invocation_id": "inv_004",
          "user_content": {
            "role": "user",
            "parts": [
              {
                // 不可能なリクエストで失敗パスをトリガー
                "text": "2099年の火星植民地における歴史的事件について分析してください。"
              }
            ]
          },
          "intermediate_data": {
            // 失敗シナリオではツール呼び出しなし
            "tool_uses": [],
            "intermediate_responses": []
          },
          "final_response": {
            "role": "model",
            "parts": [
              {
                // 失敗マーカーのみをキーワードとする
                "text": "INSUFFICIENT_DATA NO_DOCUMENTS_FOUND"
              }
            ]
          }
        }
      ]
    }
  ]
}
```

## 評価メトリクス

`tests/eval/test_config.json` より:

| メトリクス | 閾値 | 方式 | 説明 |
|-----------|------|------|------|
| `tool_trajectory_avg_score` | 0.7 | `IN_ORDER` | ツール呼び出しが期待される順序に一致するか |
| `response_match_score` | 0.5 | `ROUGE_1` | レスポンスに期待されるキーワードが含まれるか |

## チェックリスト

eval_set JSON を確定する前の確認事項:

- [ ] `eval_set_id` が `{agent_name}_eval_v1` 形式であること
- [ ] 全 `eval_id` が `{agent_name}_{scenario}` 形式であること
- [ ] 全 `user_content` のテキストが日本語であること
- [ ] `tool_uses` の各ツールが `"args": {}` を持つこと
- [ ] 失敗シナリオは `"tool_uses": []` であること
- [ ] 成功シナリオの `final_response` テキストにエージェントの `output_key` が含まれること
- [ ] 失敗シナリオの `final_response` テキストに失敗マーカーキーワードが含まれること
- [ ] `invocation_id` が連番（`inv_001`, `inv_002`, ...）であること
- [ ] JSON が有効であること（`python -m json.tool` で確認）
