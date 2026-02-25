# モックパターンカタログ

`/tdd` スキルが参照する、依存別モックパターンの詳細リファレンス。

## conftest.py フィクスチャ一覧

`tests/conftest.py` で定義済みのフィクスチャ。テスト関数の引数に追加するだけで利用可能。

### モックフィクスチャ

| フィクスチャ名 | 型 | 用途 |
|--------------|---|------|
| `mock_firestore_client` | `MagicMock` | Firestore クライアント（collection/document/set/get チェーン設定済み） |
| `mock_storage_bucket` | `MagicMock` | Storage バケット（blob/upload/make_public 設定済み、`public_url` プロパティあり） |
| `patch_firestore` | `MagicMock` | `shared.firestore.get_firestore_client` を自動パッチ（yields mock_firestore_client） |
| `patch_storage` | `MagicMock` | `shared.firestore.get_storage_bucket` を自動パッチ（yields mock_storage_bucket） |
| `frozen_time` | `datetime` | 固定時刻 `2024-01-15T12:00:00Z` |

### サンプルデータフィクスチャ

| フィクスチャ名 | 用途 |
|--------------|------|
| `sample_archive_document_data` | ArchiveDocument の辞書データ |
| `sample_evidence_data` | Evidence の辞書データ |
| `sample_historical_context_data` | HistoricalContext の辞書データ |
| `sample_mystery_report_data` | MysteryReport の辞書データ（evidence, historical_context 含む） |
| `sample_search_results_data` | SearchResults の辞書データ |
| `load_fixture` | `tests/fixtures/` から JSON ファイルを読み込むファクトリ |

### conftest.py の sys.modules パッチ

`conftest.py` で以下のモジュールが `sys.modules` に事前パッチされている。テストファイルで追加のパッチは不要:

- `google.adk`, `google.adk.agents`, `google.adk.tools`
- `google.genai`, `google.genai.types`
- `firebase_admin`, `firebase_admin.credentials`, `firebase_admin.firestore`, `firebase_admin.storage`
- `google.cloud.firestore`, `google.cloud.storage`

## 依存別モックパターン

### 1. Firestore 依存

`shared.firestore.get_firestore_client` を使用する関数向け。

#### パターン A: conftest フィクスチャ使用（推奨）

```python
def test_function_success(self, mock_firestore_client):
    """conftest の mock_firestore_client を引数で受け取る。"""
    with patch(
        "<package>.tools.<module>.get_firestore_client",
        return_value=mock_firestore_client,
    ):
        from <package>.tools.<module> import target_function

        result = json.loads(target_function("test-id"))
        assert result["status"] == "success"
        mock_firestore_client.collection.assert_called_with("mysteries")
```

#### パターン B: Firestore 書き込みデータをキャプチャ

```python
def test_function_sets_data(self, mock_firestore_client):
    """Firestore に書き込まれたデータを検証する。"""
    captured_data = {}

    def capture_set(data):
        captured_data.update(data)

    mock_doc = MagicMock()
    mock_doc.set.side_effect = capture_set
    mock_firestore_client.collection.return_value.document.return_value = mock_doc

    with patch(
        "<package>.tools.<module>.get_firestore_client",
        return_value=mock_firestore_client,
    ):
        from <package>.tools.<module> import target_function
        target_function(...)

    assert "createdAt" in captured_data
    assert captured_data["status"] == "pending"
```

#### パターン C: Firestore 読み取りモック

```python
def test_load_existing_document(self, mock_firestore_client):
    """Firestore からデータを読み取る関数のテスト。"""
    mock_doc = MagicMock()
    mock_doc.exists = True
    mock_doc.to_dict.return_value = {
        "title": "Test Mystery",
        "summary": "Test summary",
        "narrative_content": "Test content",
    }
    mock_firestore_client.collection.return_value.document.return_value.get.return_value = mock_doc

    with patch(
        "<package>.tools.<module>.get_firestore_client",
        return_value=mock_firestore_client,
    ):
        from <package>.tools.<module> import target_function
        result = target_function("test-id")

    assert result is not None
    assert result["title"] == "Test Mystery"
```

#### パターン D: Firestore ドキュメント未存在

```python
def test_load_nonexistent_document(self, mock_firestore_client):
    """存在しないドキュメントのテスト。"""
    mock_doc = MagicMock()
    mock_doc.exists = False
    mock_firestore_client.collection.return_value.document.return_value.get.return_value = mock_doc

    with patch(
        "<package>.tools.<module>.get_firestore_client",
        return_value=mock_firestore_client,
    ):
        from <package>.tools.<module> import target_function
        result = target_function("nonexistent-id")

    assert result is None
```

#### パターン E: Firestore update モック

```python
def test_update_document(self, mock_firestore_client):
    """Firestore の update 呼び出しを検証する。"""
    captured_data = {}

    def capture_update(data):
        captured_data.update(data)

    mock_doc = MagicMock()
    mock_doc.update.side_effect = capture_update
    mock_firestore_client.collection.return_value.document.return_value = mock_doc

    with patch(
        "<package>.tools.<module>.get_firestore_client",
        return_value=mock_firestore_client,
    ):
        from <package>.tools.<module> import target_function
        target_function("test-id", ...)

    assert captured_data["status"] == "published"
    mock_doc.update.assert_called_once()
```

### 2. Cloud Storage 依存

`shared.firestore.get_storage_bucket` を使用する関数向け。

```python
def test_upload_success(self, mock_storage_bucket):
    """Storage へのアップロードテスト。"""
    with patch(
        "<package>.tools.<module>.get_storage_bucket",
        return_value=mock_storage_bucket,
    ):
        from <package>.tools.<module> import upload_function

        result = json.loads(upload_function("test-id", json.dumps(["/tmp/test.png"])))

    assert result["status"] == "success"
    mock_storage_bucket.blob.assert_called()
```

### 3. genai (Imagen) 依存

`google.genai.Client` を使用する画像生成関数向け。

```python
@patch("<package>.tools.<module>._get_client")
def test_image_generation_success(self, mock_get_client):
    """Imagen API 呼び出しの成功テスト。"""
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client

    mock_image = MagicMock()
    mock_response = MagicMock()
    mock_response.generated_images = [MagicMock(image=mock_image)]
    mock_client.models.generate_images.return_value = mock_response

    from <package>.tools.<module> import generate_function

    result = json.loads(generate_function("test prompt"))
    assert result["status"] == "success"
    assert mock_client.models.generate_images.call_count == 1
```

#### Safety filter / リトライのテスト

```python
@patch("<package>.tools.<module>._get_client")
def test_retry_on_safety_filter(self, mock_get_client):
    """Safety filter で空レスポンス → リトライのテスト。"""
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client

    mock_image = MagicMock()
    mock_client.models.generate_images.side_effect = [
        MagicMock(generated_images=[]),  # 1回目: Safety filter
        MagicMock(generated_images=[MagicMock(image=mock_image)]),  # 2回目: 成功
    ]

    result = json.loads(generate_function("ghost ship"))
    assert result["status"] == "success"
    assert result["prompt_sanitized"] is True
```

### 4. HTTP (requests) 依存

`requests` ライブラリを使用する関数向け。`responses` ライブラリでモックする。

```python
import responses

@responses.activate
def test_api_call_success(self):
    """外部 API 呼び出しの成功テスト。"""
    responses.add(
        responses.GET,
        "https://api.example.com/search",
        json={"results": [{"title": "Test"}]},
        status=200,
    )

    from <package>.tools.<module> import search_function
    result = search_function("test query")
    assert len(result["documents"]) > 0
```

#### API エラーのテスト

```python
@responses.activate
def test_api_error(self):
    """API エラー時の graceful エラーハンドリング。"""
    responses.add(
        responses.GET,
        "https://api.example.com/search",
        json={"error": "rate limited"},
        status=429,
    )

    result = search_function("test query")
    assert result.get("error") is not None
```

### 5. ファイル I/O 依存

`open`, `Path`, `os` を使用するファイル操作関数向け。

```python
import tempfile

def test_load_file_success(self):
    """ファイル読み込みの成功テスト。"""
    test_data = {"theme": "test", "results": {"documents": []}}

    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".json", delete=False
    ) as f:
        json.dump(test_data, f)
        temp_path = f.name

    try:
        result = json.loads(load_function(temp_path))
        assert result["status"] == "success"
    finally:
        os.unlink(temp_path)
```

```python
def test_load_file_not_found(self):
    """存在しないファイルの読み込みテスト。"""
    result = json.loads(load_function("/nonexistent/path.json"))
    assert "error" in result
```

### 6. 時刻依存

タイムスタンプを生成する関数は `freezegun` でテストする。

```python
from freezegun import freeze_time

@freeze_time("2024-01-15 12:00:00")
def test_timestamp_generation(self):
    """タイムスタンプが正しく生成されるテスト。"""
    result = generate_with_timestamp(...)
    assert "20240115" in result["filename"]
```

## 既存テストの模範コード

### test_illustrator_tools.py（genai モック + リトライ + JSON アサーション）

```python
# テストクラス構成の例
class TestSanitizePrompt:         # ヘルパー関数のテスト
class TestGenerateImageRetry:     # リトライメカニズムのテスト
class TestGenerateImageFallback:  # フォールバックのテスト
class TestGenerateImageStyles:    # パラメータバリエーション
class TestGenerateImageOutput:    # 出力フォーマット検証
```

### test_publisher_tools.py（Firestore モック + emulator skip）

```python
# Unit テスト: mock_firestore_client を with patch で注入
class TestPublishMystery:
    def test_publish_mystery_success(self, mock_firestore_client, sample_mystery_report_data):
        with patch("...get_firestore_client", return_value=mock_firestore_client):
            ...

# Integration テスト: @pytest.mark.integration + emulator チェック
@pytest.mark.integration
class TestPublisherToolsWithEmulator:
    @pytest.fixture(autouse=True)
    def check_emulator(self):
        if not os.environ.get("FIRESTORE_EMULATOR_HOST"):
            pytest.skip("Firebase Emulator not running")
```
