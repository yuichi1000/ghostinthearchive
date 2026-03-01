---
name: adk
description: "ADK（Agent Development Kit）関連のコード変更・設計判断時に参照。公式ドキュメント確認 + ベストプラクティス適用"
disable-model-invocation: false
allowed-tools: Read, Glob, Grep, WebFetch, WebSearch
---

# /adk — ADK 設計判断ガイド

ADK（Agent Development Kit）関連のコード変更・設計判断を行う。
Google のシニアプログラマの視点でコードレビュー・設計判断を行い、ADK 公式ドキュメントに基づくベストプラクティスを適用する。

## ワークフロー

### Step 1: 公式ドキュメント参照

ADK 公式ドキュメントを WebFetch で確認し、最新の API・パターンを把握する。

主要な参照先:

| トピック | URL |
|---------|-----|
| エージェント概要 | https://google.github.io/adk-docs/agents/ |
| Custom Agent | https://google.github.io/adk-docs/agents/custom-agents/ |
| LLM Agent | https://google.github.io/adk-docs/agents/llm-agents/ |
| ワークフローエージェント | https://google.github.io/adk-docs/agents/workflow-agents/ |
| ツール | https://google.github.io/adk-docs/tools/ |
| セッション・状態管理 | https://google.github.io/adk-docs/sessions/ |
| 評価 | https://google.github.io/adk-docs/evaluate/ |

`$ARGUMENTS` に具体的なトピック（例: `custom agent`, `session state`, `callback`）が指定された場合は、該当ページを優先的に確認する。

### Step 2: プロジェクト規約確認

1. `CLAUDE.md` の「ADK 規約・ベストプラクティス」セクションを確認する
2. `.claude/skills/gen-eval/agent-catalog.md` でエージェント一覧・プロパティを確認する

### Step 3: 設計判断

以下のベストプラクティスに基づいて、質問への回答またはコードレビューを行う。

## エージェント種別の使い分け

| 種別 | 用途 | LLM 使用 |
|------|------|----------|
| `LlmAgent` | LLM の判断が必要なタスク（分析、生成、翻訳等） | Yes |
| `BaseAgent`（Custom Agent） | 決定的実行（DB 書き込み、外部 API 呼び出し等） | No |
| `SequentialAgent` | 子エージェントを順番に実行 | No |
| `ParallelAgent` | 子エージェントを並列実行 | No |
| `LoopAgent` | 子エージェントをループ実行（討論等） | No |

### Custom Agent を選ぶべきケース

- LLM の判断が不要で、入力→処理→出力が決定的なタスク
- LlmAgent がツール呼び出しをスキップするリスクを排除したいケース
- 外部サービスへの直接書き込み（Firestore、Cloud Storage 等）
- セッション状態の加工・変換のみで完結するタスク

## セッション状態の読み書きパターン

### LlmAgent（ToolContext 経由）

```python
def my_tool(input: str, tool_context: ToolContext) -> str:
    data = tool_context.state.get("key")
    tool_context.state["output_key"] = result
    return result
```

### Custom Agent（InvocationContext + EventActions.state_delta）

```python
class MyAgent(BaseAgent):
    async def _run_async_impl(self, ctx: InvocationContext) -> AsyncGenerator[Event, None]:
        data = ctx.session.state.get("key")
        yield Event(
            invocation_id=ctx.invocation_id,
            author=self.name,
            branch=ctx.branch,
            content=types.Content(role="model", parts=[types.Part(text=result)]),
            actions=EventActions(state_delta={"output_key": result}),
        )
```

Custom Agent では `ctx.session.state` に直接書き込まず、`EventActions.state_delta` で状態変更を伝播する。

## before_agent_callback / after_agent_callback パターン

- `return False` → エージェントをスキップ
- `return None` → デフォルト動作（続行）
- 本プロジェクトでは `mystery_agents/agents/pipeline_gate.py` に集約
