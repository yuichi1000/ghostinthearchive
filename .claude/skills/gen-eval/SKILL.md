---
name: gen-eval
description: "This skill should be used when the user asks to '/gen-eval', 'generate eval tests', 'create evaluation tests for agent', 'add golden dataset', 'generate ADK eval', or needs to create ADK agent-level evaluation tests including Golden Datasets, eval content verification tests, and agent handover tests."
argument-hint: "[agent_module_path]"
---

# ADK Agent Evaluation Test Generator

Generate ADK agent-level evaluation tests: Golden Dataset (eval_set JSON), eval content verification tests, and agent handover tests.

## Workflow

Follow these 7 steps in order when `$ARGUMENTS` is provided. If `$ARGUMENTS` is empty, ask the user to specify an agent module path (e.g., `archive_agents/agents/scholar.py`).

### Step 1: Parse Agent Module

Read the agent module file at `$ARGUMENTS` and extract:

- **name**: Agent variable name (e.g., `scholar_agent`)
- **model**: Model string (e.g., `gemini-3-pro-preview`)
- **output_key**: Session state output key (e.g., `mystery_report`)
- **tools**: List of tool functions (from `tools=[]` parameter)
- **instruction**: Full instruction string (look for `{placeholder}` patterns)
- **failure_markers_checked**: Markers the agent checks in upstream data (e.g., `NO_DOCUMENTS_FOUND`)
- **failure_markers_emitted**: Markers the agent emits on failure (e.g., `INSUFFICIENT_DATA`)

### Step 2: Determine Pipeline Context

Identify the pipeline from the file path prefix:

| Path Prefix | Pipeline | Commander |
|-------------|----------|-----------|
| `archive_agents/` | archive (blog) | `ghost_commander` |
| `podcast_agents/` | podcast | `podcast_commander` |
| `translator_agents/` | translator | `translator_commander` |

Cross-reference with `agent-catalog.md` (in this skill's directory) to determine:
- Predecessor agent and its `output_key` (the session state key this agent reads)
- Successor agent (if any)
- Expected eval scenarios for this agent

### Step 3: Check Existing Tests

Scan for existing tests to avoid duplication:

1. **Eval set JSON**: Check `tests/eval/eval_sets/{agent_name}_eval.json`
2. **Eval content tests**: Grep `tests/eval/test_adk_eval.py` for `test_{agent_name}_eval_covers`
3. **Handover tests**: Grep `tests/integration/test_agent_handover.py` for `test_{agent_name}_output_key`

Report what exists and what needs to be generated.

### Step 4: Generate Golden Dataset

Create or update `tests/eval/eval_sets/{agent_name}_eval.json`.

Consult `eval-set-format.md` (in this skill's directory) for the exact ADK eval_set JSON format specification. Consult `agent-catalog.md` for the expected eval scenarios for this agent.

**Rules:**
- `eval_set_id`: `{agent_name}_eval_v1`
- `eval_id`: `{agent_name}_{scenario_snake_case}`
- `user_content.parts[0].text`: Always in Japanese
- `intermediate_data.tool_uses`: List expected tools with `"args": {}` (empty args). Set to `[]` for agents without tools or for failure scenarios
- `final_response.parts[0].text`: Include `output_key` name + expected keywords (space-separated). For failure scenarios, include the failure marker keyword

If the file already exists, compare existing `eval_id` values against the expected scenarios from `agent-catalog.md`. Only add missing scenarios.

### Step 5: Generate Eval Content Verification Tests

Add methods to `TestEvalSetContent` class in `tests/eval/test_adk_eval.py`.

**Generate these test methods** (skip if already present):

1. `test_{agent_name}_eval_covers_key_scenarios` — Verify eval_set contains expected scenario eval_ids. Use `any("keyword" in eid.lower() for eid in eval_ids)` pattern matching the existing test style
2. For agents with tools: A test verifying `intermediate_data.tool_uses` contains expected tool names (follow `test_publisher_eval_covers_tool_usage` pattern)
3. For agents that emit failure markers: Verify a failure scenario exists in the eval_set

Follow the exact code style of existing methods in `TestEvalSetContent`. Import nothing extra — the class already has `json`, `Path`, `EVAL_SETS_DIR` available.

### Step 6: Generate Agent Handover Tests

Add methods to the appropriate class in `tests/integration/test_agent_handover.py`.

**Generate these test methods** (skip if already present):

1. `test_{agent_name}_output_key` — Verify `agent.output_key == "expected_key"` (add to `TestSessionStateKeys` or `TestPodcastSessionStateKeys`)
2. `test_{agent_name}_references_{predecessor_key}` — Verify `"{predecessor_key}" in agent.instruction` (add to `TestInstructionPlaceholders` or `TestPodcastInstructionPlaceholders`)
3. `test_{agent_name}_checks_upstream_failure` — Verify the agent's instruction contains the upstream failure marker string (add to `TestFailureMarkers` if not already covered)
4. `test_{agent_name}_uses_correct_model` — Verify `agent.model == "gemini-3-pro-preview"` (add to `TestAgentModels`)

Follow the exact import and assertion patterns of existing test methods.

### Step 7: Verify

Run structural tests to confirm generated files are valid:

```bash
pytest tests/eval/test_adk_eval.py::TestADKEvaluationSetup -v
pytest tests/eval/test_adk_eval.py::TestEvalSetContent -v
pytest tests/integration/test_agent_handover.py -v
```

Report results. If any test fails, fix and re-run.

## Reference Files

Consult these files in this skill's directory for detailed specifications:

- **`agent-catalog.md`** — Full agent definitions catalog: properties, pipeline positions, expected eval scenarios
- **`eval-set-format.md`** — ADK eval_set JSON format specification with annotated examples
