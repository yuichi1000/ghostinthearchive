# ADK Eval Set JSON Format Specification

This document defines the exact format for Golden Dataset JSON files used by the ADK evaluation framework (`adk eval`).

## File Location

```
tests/eval/eval_sets/{agent_name}_eval.json
```

## Top-Level Structure

```json
{
  "eval_set_id": "{agent_name}_eval_v1",
  "name": "{Agent Name} Agent Evaluation",
  "description": "Tests {Agent Name}'s {capability description} via full pipeline execution",
  "eval_cases": [...]
}
```

| Field | Format | Example |
|-------|--------|---------|
| `eval_set_id` | `{agent_name}_eval_v1` | `scholar_eval_v1` |
| `name` | `{Agent Name} Agent Evaluation` | `Scholar Agent Evaluation` |
| `description` | Free text describing test scope | `"Tests Scholar's interdisciplinary analysis capabilities via full pipeline execution"` |
| `eval_cases` | Array of eval case objects | See below |

## Eval Case Structure

Each item in `eval_cases`:

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

## Field Specifications

### eval_id

Format: `{agent_name}_{scenario_snake_case}`

Examples:
- `scholar_fact_based_analysis`
- `librarian_no_results`
- `publisher_full_workflow`

### invocation_id

Sequential within the eval_set: `inv_001`, `inv_002`, `inv_003`, ...

### user_content

- `role`: Always `"user"`
- `parts[0].text`: **Must be in Japanese.** Describe the task the pipeline receives. Write a realistic research/analysis request that triggers the target agent's specific behavior.

Good examples:
```
"1842年3月のボストン港におけるスペイン船サンタマリア号の記録を分析してください。"
"ニューイングランドの漁村で1850年代に複数の漁師が同じ場所で不可解な現象を報告しています。"
```

For failure/edge-case scenarios, use obviously impossible requests:
```
"2099年の火星植民地における歴史的事件について分析してください。"
```

### intermediate_data.tool_uses

Array of expected tool calls. Each tool is specified with name only — `args` is always empty `{}`:

```json
"tool_uses": [
  {"name": "search_newspapers", "args": {}},
  {"name": "search_archives", "args": {}}
]
```

- For agents **without tools**: `"tool_uses": []`
- For **failure scenarios** (even if agent has tools): `"tool_uses": []`
- `intermediate_responses`: Always `[]`

### final_response

- `role`: Always `"model"`
- `parts[0].text`: Space-separated keywords that the response should contain. Evaluated using ROUGE-1 scoring (threshold: 0.5 as per `test_config.json`).

**Keyword selection rules:**

| Scenario Type | Keywords to Include |
|--------------|-------------------|
| Success (normal) | `output_key` + domain-specific keywords + `Firestore` (if data is stored) |
| Success (tool-using) | `output_key` + tool-related outcome keywords |
| Failure (marker) | Failure marker(s) only (e.g., `NO_DOCUMENTS_FOUND`, `INSUFFICIENT_DATA NO_CONTENT`) |

Examples:
```json
// Scholar success
"text": "mystery_report DATE_MISMATCH EVENT_OUTCOME 仮説 Firestore"

// Scholar folklore
"text": "Folkloric Context RECURRING_PATTERN LOCAL_TABOO Firestore"

// Scholar failure
"text": "INSUFFICIENT_DATA NO_DOCUMENTS_FOUND"

// Librarian with tools
"text": "collected_documents total_found"

// Publisher with tools
"text": "published_episode Firestore mystery_id"
```

## Annotated Example (Scholar)

```json
{
  // eval_set_id follows {agent}_eval_v1 convention
  "eval_set_id": "scholar_eval_v1",
  "name": "Scholar Agent Evaluation",
  "description": "Tests Scholar's interdisciplinary analysis capabilities via full pipeline execution",
  "eval_cases": [
    {
      // eval_id: {agent}_{scenario}
      "eval_id": "scholar_fact_based_analysis",
      "conversation": [
        {
          // Sequential invocation ID
          "invocation_id": "inv_001",
          "user_content": {
            "role": "user",
            "parts": [
              {
                // MUST be Japanese — realistic analysis request
                "text": "1842年3月のボストン港におけるスペイン船サンタマリア号の記録を分析してください。英語の新聞記事では船が消失したと報じていますが、スペイン語の記録では同じ船が2週間後にハバナに到着したと記載されています。"
              }
            ]
          },
          "intermediate_data": {
            // Scholar has no tools — empty array
            "tool_uses": [],
            "intermediate_responses": []
          },
          "final_response": {
            "role": "model",
            "parts": [
              {
                // output_key (mystery_report) + domain keywords
                "text": "mystery_report DATE_MISMATCH EVENT_OUTCOME 仮説 Firestore"
              }
            ]
          }
        }
      ]
    },
    {
      // Failure scenario — agent should detect insufficient data
      "eval_id": "scholar_insufficient_data",
      "conversation": [
        {
          "invocation_id": "inv_004",
          "user_content": {
            "role": "user",
            "parts": [
              {
                // Impossible request triggers failure path
                "text": "2099年の火星植民地における歴史的事件について分析してください。"
              }
            ]
          },
          "intermediate_data": {
            // No tools called in failure scenario
            "tool_uses": [],
            "intermediate_responses": []
          },
          "final_response": {
            "role": "model",
            "parts": [
              {
                // Only failure markers as keywords
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

## Evaluation Metrics

From `tests/eval/test_config.json`:

| Metric | Threshold | Method | Description |
|--------|-----------|--------|-------------|
| `tool_trajectory_avg_score` | 0.7 | `IN_ORDER` | Tool calls match expected sequence |
| `response_match_score` | 0.5 | `ROUGE_1` | Response contains expected keywords |

## Checklist

Before finalizing an eval_set JSON:

- [ ] `eval_set_id` follows `{agent_name}_eval_v1` format
- [ ] All `eval_id` values follow `{agent_name}_{scenario}` format
- [ ] All `user_content` text is in Japanese
- [ ] `tool_uses` has `"args": {}` for each tool entry
- [ ] Failure scenarios have `"tool_uses": []`
- [ ] `final_response` text includes the agent's `output_key` for success scenarios
- [ ] `final_response` text includes failure marker keywords for failure scenarios
- [ ] `invocation_id` values are sequential (`inv_001`, `inv_002`, ...)
- [ ] JSON is valid (run through `python -m json.tool`)
