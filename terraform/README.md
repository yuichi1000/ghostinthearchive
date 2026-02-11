# Terraform - Ghost in the Archive

## 初回セットアップ

### 1. Terraform state バケット作成（初回のみ）

```bash
gcloud storage buckets create gs://ghostinthearchive-terraform-state \
  --project=ghostinthearchive \
  --location=asia-northeast1 \
  --uniform-bucket-level-access
```

### 2. Docker イメージのビルド・プッシュ

Terraform apply 前に、Cloud Run で使用する Docker イメージを Artifact Registry にプッシュする必要がある。

```bash
# プロジェクトルートから実行

# pipelines イメージ（blog-pipeline / translate-pipeline / podcast-pipeline 共通）
gcloud builds submit --config cloudbuild-pipelines.yaml .

# web-admin イメージ
gcloud builds submit \
  --tag asia-northeast1-docker.pkg.dev/ghostinthearchive/ghostinthearchive/web-admin:latest \
  web-admin/
```

### 3. GitHub リポジトリの接続（Cloud Build Trigger 用）

Cloud Build コンソールで GitHub リポジトリを接続する：

https://console.cloud.google.com/cloud-build/triggers;region=global/connect?project=ghostinthearchive

### 4. Terraform 実行

```bash
cd terraform
terraform init
terraform apply
```

### 5. Spaceship ネームサーバー設定

`terraform apply` 完了後に出力される `nameservers` を確認し：

1. Spaceship にログイン → Domains → `ghostinthearchive.ai`
2. Nameservers → Custom nameservers に切り替え
3. 出力された4つの NS レコードを入力して保存

```bash
# NS レコード反映確認（数分〜最大48時間）
dig NS ghostinthearchive.ai
```

### 6. Secret 値の設定

```bash
echo -n "YOUR_VALUE" | gcloud secrets versions add nextauth-secret --data-file=-
echo -n "YOUR_VALUE" | gcloud secrets versions add google-oauth-client-id --data-file=-
echo -n "YOUR_VALUE" | gcloud secrets versions add google-oauth-client-secret --data-file=-
echo -n "YOUR_VALUE" | gcloud secrets versions add dpla-api-key --data-file=-
echo -n "YOUR_VALUE" | gcloud secrets versions add nypl-api-token --data-file=-
```
