#!/bin/bash
#
# Ghost in the Archive - 本番デプロイスクリプト
# 全コンポーネントのビルド・デプロイを一元管理
#

set -euo pipefail

# スクリプトのディレクトリを取得
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# 定数
PROJECT_ID="ghostinthearchive"
REGION="asia-northeast1"
REGISTRY="${REGION}-docker.pkg.dev/${PROJECT_ID}/ghostinthearchive"

# オプション
AUTO_YES=false

# カラー出力用
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# ログ関数
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_step() {
    echo -e "${CYAN}[STEP]${NC} $1"
}

# ヘッダー表示
show_header() {
    echo ""
    echo "========================================"
    echo "  Ghost in the Archive - Deploy"
    echo "========================================"
    echo ""
}

# 確認プロンプト（--yes 時スキップ）
confirm() {
    local message="${1:-続行しますか？}"
    if [ "$AUTO_YES" = true ]; then
        return 0
    fi
    echo ""
    read -r -p "$(echo -e "${YELLOW}${message} [y/N]${NC} ")" response
    case "$response" in
        [yY][eE][sS]|[yY])
            return 0
            ;;
        *)
            log_info "キャンセルしました"
            exit 0
            ;;
    esac
}

# .env.production から Cloud Build 置換変数を構築
# KEY=value → _KEY=value 形式に変換し、カンマ区切りで結合
build_substitutions() {
    local env_file="${PROJECT_ROOT}/$1"
    if [ ! -f "$env_file" ]; then
        log_error "$env_file が見つかりません。.env.example を参考に作成してください。"
        exit 1
    fi
    local subs=""
    while IFS='=' read -r key value; do
        # 空行・コメント行をスキップ
        [[ -z "$key" || "$key" =~ ^# ]] && continue
        if [ -z "$subs" ]; then
            subs="_${key}=${value}"
        else
            subs="${subs},_${key}=${value}"
        fi
    done < "$env_file"
    echo "$subs"
}

# 前提条件チェック
check_prerequisites() {
    local target="$1"
    local has_error=false

    log_step "前提条件を確認中..."

    # gcloud CLI チェック
    if ! command -v gcloud &> /dev/null; then
        log_error "gcloud CLI がインストールされていません"
        log_info "https://cloud.google.com/sdk/docs/install を参照してください"
        has_error=true
    else
        # 認証チェック
        if ! gcloud auth print-access-token &> /dev/null 2>&1; then
            log_error "gcloud 認証が設定されていません"
            log_info "gcloud auth login を実行してください"
            has_error=true
        fi

        # プロジェクト ID チェック
        local current_project
        current_project=$(gcloud config get-value project 2>/dev/null)
        if [ "$current_project" != "$PROJECT_ID" ]; then
            log_warn "現在の GCP プロジェクト: ${current_project}"
            log_warn "期待するプロジェクト: ${PROJECT_ID}"
            log_info "gcloud config set project ${PROJECT_ID} を実行してください"
            has_error=true
        fi
    fi

    # terraform チェック（infra ターゲット時のみ）
    if [ "$target" = "infra" ] || [ "$target" = "all" ]; then
        if ! command -v terraform &> /dev/null; then
            log_error "terraform がインストールされていません"
            log_info "https://developer.hashicorp.com/terraform/install を参照してください"
            has_error=true
        fi
    fi

    if [ "$has_error" = true ]; then
        exit 1
    fi

    log_success "前提条件 OK"
}

# デプロイ計画表示
show_deploy_plan() {
    local target="$1"

    echo ""
    echo "─────────────────────────────────────"
    echo "  デプロイ計画"
    echo "─────────────────────────────────────"

    case "$target" in
        "pipelines")
            echo "  1. Cloud Build: pipelines イメージビルド"
            echo "  2. Cloud Run 更新: curator"
            echo "  3. Cloud Run 更新: pipeline"
            ;;
        "web-admin")
            echo "  1. Cloud Build: web-admin イメージビルド"
            echo "  2. Cloud Run 更新: web-admin"
            ;;
        "web-public")
            echo "  1. Cloud Build: SSG ビルド + Firebase Hosting デプロイ"
            ;;
        "infra")
            echo "  1. Terraform init"
            echo "  2. Terraform plan"
            echo "  3. Terraform apply（確認後）"
            ;;
        "all")
            echo "  1. [infra]      Terraform apply"
            echo "  2. [pipelines]  Cloud Build → curator + pipeline 更新"
            echo "  3. [web-admin]  Cloud Build → web-admin 更新"
            echo "  4. [web-public] SSG ビルド → Firebase Hosting デプロイ"
            ;;
    esac

    echo "─────────────────────────────────────"
    echo ""
}

# pipelines デプロイ
deploy_pipelines() {
    log_step "=== pipelines デプロイ開始 ==="

    log_info "Cloud Build でイメージをビルド中..."
    gcloud builds submit \
        --config cloudbuild.yaml \
        --project "$PROJECT_ID" \
        "$PROJECT_ROOT"

    log_info "Cloud Run サービス 'curator' を更新中..."
    gcloud run services update curator \
        --image "${REGISTRY}/pipelines:latest" \
        --region "$REGION" \
        --project "$PROJECT_ID"

    log_info "Cloud Run サービス 'pipeline' を更新中..."
    gcloud run services update pipeline \
        --image "${REGISTRY}/pipelines:latest" \
        --region "$REGION" \
        --project "$PROJECT_ID"

    log_success "pipelines デプロイ完了"
}

# web-admin デプロイ
deploy_web_admin() {
    log_step "=== web-admin デプロイ開始 ==="

    local subs
    subs=$(build_substitutions "web-admin/.env.production")

    log_info "Cloud Build でイメージをビルド中..."
    gcloud builds submit \
        --config web-admin/cloudbuild.yaml \
        --substitutions "$subs" \
        --project "$PROJECT_ID" \
        "$PROJECT_ROOT"

    log_info "Cloud Run サービス 'web-admin' を更新中..."
    gcloud run services update web-admin \
        --image "${REGISTRY}/web-admin:latest" \
        --region "$REGION" \
        --project "$PROJECT_ID"

    log_success "web-admin デプロイ完了"
}

# web-public デプロイ
deploy_web_public() {
    log_step "=== web-public デプロイ開始 ==="

    local subs
    subs=$(build_substitutions "web-public/.env.production")

    log_info "Cloud Build で SSG ビルド + Firebase Hosting デプロイ中..."
    gcloud builds submit \
        --config web-public/cloudbuild.yaml \
        --substitutions "$subs" \
        --project "$PROJECT_ID" \
        "$PROJECT_ROOT"

    log_success "web-public デプロイ完了"
}

# infra デプロイ
deploy_infra() {
    log_step "=== infra デプロイ開始 ==="

    log_info "Terraform init..."
    terraform -chdir="${PROJECT_ROOT}/terraform" init -input=false

    log_info "Terraform plan..."
    terraform -chdir="${PROJECT_ROOT}/terraform" plan -out=tfplan

    confirm "Terraform apply を実行しますか？"

    log_info "Terraform apply..."
    terraform -chdir="${PROJECT_ROOT}/terraform" apply tfplan

    # plan ファイルを削除
    rm -f "${PROJECT_ROOT}/terraform/tfplan"

    log_success "infra デプロイ完了"
}

# 全ターゲットを順次デプロイ
deploy_all() {
    log_step "=== 全コンポーネントデプロイ開始 ==="
    echo ""

    deploy_infra
    echo ""
    deploy_pipelines
    echo ""
    deploy_web_admin
    echo ""
    deploy_web_public
    echo ""

    log_success "全コンポーネントのデプロイが完了しました"
}

# ステータス表示
show_status() {
    log_step "デプロイ状況を確認中..."
    echo ""

    echo "─────────────────────────────────────"
    echo "  Cloud Run サービス"
    echo "─────────────────────────────────────"

    for service in curator pipeline web-admin; do
        echo ""
        log_info "${service}:"
        gcloud run services describe "$service" \
            --region "$REGION" \
            --project "$PROJECT_ID" \
            --format="table(status.traffic.revisionName,status.traffic.percent,status.url)" \
            2>/dev/null || log_warn "  サービス '${service}' が見つかりません"
    done

    echo ""
    echo "─────────────────────────────────────"
    echo "  Artifact Registry イメージ"
    echo "─────────────────────────────────────"
    echo ""

    for image in pipelines web-admin; do
        log_info "${image}:"
        gcloud artifacts docker images list \
            "${REGISTRY}/${image}" \
            --project "$PROJECT_ID" \
            --sort-by="~UPDATE_TIME" \
            --limit=3 \
            --format="table(package,version,updateTime)" \
            2>/dev/null || log_warn "  イメージ '${image}' が見つかりません"
        echo ""
    done
}

# ヘルプ表示
show_usage() {
    echo "Usage: $0 <target> [options]"
    echo ""
    echo "Targets:"
    echo "  pipelines  - pipelines イメージビルド + curator/pipeline Cloud Run 更新"
    echo "  web-admin  - web-admin イメージビルド + Cloud Run 更新"
    echo "  web-public - SSG ビルド + Firebase Hosting デプロイ"
    echo "  infra      - Terraform plan + apply"
    echo "  all        - 全コンポーネントを順次デプロイ（infra → pipelines → web-admin → web-public）"
    echo "  status     - 全サービスのデプロイ状況表示"
    echo "  help       - このヘルプを表示"
    echo ""
    echo "Options:"
    echo "  --yes, -y  - 確認プロンプトをスキップ"
    echo ""
    echo "Examples:"
    echo "  $0 pipelines          # pipelines のみデプロイ"
    echo "  $0 web-admin --yes    # web-admin を確認なしでデプロイ"
    echo "  $0 all                # 全コンポーネントを順次デプロイ"
    echo "  $0 status             # デプロイ状況を確認"
    echo ""
}

# メイン処理

# 引数が空ならヘルプ表示
if [ $# -eq 0 ]; then
    show_header
    show_usage
    exit 0
fi

# 引数解析
TARGET=""
for arg in "$@"; do
    case "$arg" in
        --yes|-y)
            AUTO_YES=true
            ;;
        *)
            if [ -z "$TARGET" ]; then
                TARGET="$arg"
            fi
            ;;
    esac
done

# ターゲット分岐
case "$TARGET" in
    "pipelines"|"web-admin"|"web-public"|"infra"|"all")
        show_header
        check_prerequisites "$TARGET"
        show_deploy_plan "$TARGET"
        confirm "デプロイを開始しますか？"
        echo ""

        case "$TARGET" in
            "pipelines")  deploy_pipelines ;;
            "web-admin")  deploy_web_admin ;;
            "web-public") deploy_web_public ;;
            "infra")      deploy_infra ;;
            "all")        deploy_all ;;
        esac
        ;;

    "status")
        show_header
        check_prerequisites "status"
        show_status
        ;;

    "help"|"-h"|"--help")
        show_header
        show_usage
        ;;

    *)
        log_error "不明なターゲット: $TARGET"
        echo ""
        show_usage
        exit 1
        ;;
esac
