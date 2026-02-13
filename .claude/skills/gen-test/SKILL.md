---
name: gen-test
description: "ADK ツール関数の TDD テストを生成。conftest.py モック・テスト配置規則・Red-Green-Refactor に準拠"
argument-hint: "[tool_module_path]"
disable-model-invocation: true
allowed-tools: Read, Glob, Grep, Bash, Write, Edit
---

# /gen-test — ADK ツール関数のテスト自動生成

対象ツールモジュールのパスを `$ARGUMENTS` で受け取り、プロジェクト規約に完全準拠したテストファイルを生成する。

## ワークフロー

### Step 1: ツールモジュール分析

対象ファイル `$ARGUMENTS` を読み取り、以下を抽出する:

1. **公開関数の一覧**: `def function_name(...)` のシグネチャ、引数、デフォルト値
2. **外部依存**: import 文から依存先を特定
   - `shared.firestore` → Firestore/Storage 依存
   - `google.genai` → genai 依存
   - `requests` → HTTP 依存
   - ファイル I/O（`open`, `Path`）→ ファイルシステム依存
3. **返り値フォーマット**: JSON 文字列（`json.dumps`）か、dict/None か
4. **エラーハンドリング**: try/except パターン、エラー時の返り値
5. **内部ヘルパー**: `_` プレフィックスのプライベート関数（テスト可能なものは含める）

### Step 2: テスト配置決定

CLAUDE.md のテスト配置規則に従い、テストファイルパスを決定する:

| 対象コード | テストファイル |
|-----------|---------------|
| `mystery_agents/tools/*.py` | `tests/unit/test_<module_name>.py` |
| `podcast_agents/tools/*.py` | `tests/unit/test_podcast_<module_name>.py` |
| `mystery_agents/utils/*.py` | `tests/unit/test_<module_name>.py` |
| `mystery_agents/schemas/*.py` | `tests/unit/test_schemas.py`（既存に追記） |

**Firestore/Storage に直接依存する関数**がある場合、Integration テストも検討:
- `tests/integration/test_<module_name>.py`

### Step 3: 既存テスト確認

```bash
# 既存テストとの重複チェック
pytest tests/ -v --collect-only -k "<module_name>"
```

既存テストがある場合:
- 重複するテストは生成しない
- 不足しているケースのみ追加する
- 既存テストのスタイル（クラス名、命名規則）に合わせる

### Step 4: Unit テスト生成

[mock-patterns.md](mock-patterns.md) のモックパターンカタログを参照し、テストを生成する。

#### テスト構造テンプレート

```python
"""Unit tests for <module_name>."""

import json
from unittest.mock import MagicMock, patch

import pytest

from <package>.tools.<module_name> import (
    function_a,
    function_b,
    _helper_if_testable,
)


class TestFunctionAPascalCase:
    """Tests for function_a."""

    def test_function_a_success(self):
        """Should <expected behavior> when <condition>."""
        # Arrange
        ...
        # Act
        result = function_a(...)
        # Assert
        ...

    def test_function_a_error_case(self):
        """Should <expected error behavior> when <error condition>."""
        ...
```

#### テスト網羅性チェックリスト

各公開関数に対して、以下のカテゴリを検討する:

- [ ] **正常系**: 期待される入力で正しい出力を返すか
- [ ] **入力バリデーション**: 不正な入力（空文字、None、型不一致）でエラーを返すか
- [ ] **JSON パース**: JSON 文字列入力の場合、不正な JSON でエラーを返すか
- [ ] **外部依存エラー**: Firestore/API/ファイルI/O の例外時に graceful にエラーを返すか
- [ ] **エッジケース**: 空リスト、存在しないファイル、大量データ等
- [ ] **返り値フォーマット**: JSON 文字列の場合、必須フィールドが含まれるか

全カテゴリを網羅する必要はない。対象関数のロジックに応じて、意味のあるテストのみ生成する。

### Step 5: Integration テスト生成（Firestore/Storage 依存がある場合のみ）

Firestore/Storage に直接依存する関数がある場合のみ、Integration テストを生成する。

```python
"""Integration tests for <module_name>.

These tests require Firebase Emulator to be running:
    firebase emulators:start --only firestore,storage

Run with:
    pytest tests/integration/test_<module_name>.py -v -m integration
"""

import json
import os
from unittest.mock import patch

import pytest


@pytest.mark.integration
class TestModuleNameWithEmulator:
    """Integration tests requiring Firebase Emulator."""

    @pytest.fixture(autouse=True)
    def check_emulator(self):
        """Skip if emulator is not running."""
        if not os.environ.get("FIRESTORE_EMULATOR_HOST"):
            pytest.skip("Firebase Emulator not running")

    def test_end_to_end(self):
        ...
```

### Step 6: Red フェーズ確認

生成したテストを実行し、結果を確認する:

```bash
# Unit テスト実行
pytest tests/unit/test_<module_name>.py -v

# 既存テストが壊れていないことを確認
pytest tests/unit/ -v --tb=short
```

**期待される結果:**
- テストが実行可能であること（import エラーなし）
- テストが PASS するか、実装の問題で FAIL するか（Red フェーズ）
- 既存テストが影響を受けていないこと

## テスト命名規則

- **クラス名**: `TestFunctionNamePascalCase`（例: `TestPublishMystery`, `TestSanitizePrompt`）
- **メソッド名**: `test_function_name_scenario`（例: `test_publish_mystery_success`, `test_publish_mystery_invalid_json`）
- **docstring**: `"""Should <期待される振る舞い> when <条件>."""`

## リファレンス

- 依存別モックパターンの詳細は [mock-patterns.md](mock-patterns.md) を参照
- テスト配置規則・TDD ワークフローは `/tdd` スキルを参照
- 既存テストの模範:
  - `tests/unit/test_illustrator_tools.py`（genai モック、リトライ、JSON アサーション）
  - `tests/integration/test_publisher_tools.py`（Firestore モック、emulator skip）
