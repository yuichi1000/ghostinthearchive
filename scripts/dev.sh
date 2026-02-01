#!/bin/bash
#
# Ghost in the Archive - 開発環境起動スクリプト
# Firebase エミュレータ、Next.js開発サーバー、Pythonエージェントを起動
#

set -e

# スクリプトのディレクトリを取得
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# カラー出力用
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
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

# 終了時のクリーンアップ
cleanup() {
    log_info "プロセスを終了しています..."
    # バックグラウンドプロセスを終了
    jobs -p | xargs -r kill 2>/dev/null || true
    exit 0
}

trap cleanup SIGINT SIGTERM

# ヘッダー表示
echo ""
echo "========================================"
echo "  Ghost in the Archive - Dev Server"
echo "========================================"
echo ""

# プロジェクトルートに移動
cd "$PROJECT_ROOT"

# Firebase エミュレータを起動する関数
start_emulator() {
    if ! command -v firebase &> /dev/null; then
        log_error "firebase-tools がインストールされていません"
        log_info "npm install -g firebase-tools でインストールしてください"
        exit 1
    fi

    log_info "Firebase エミュレータを起動中..."
    firebase emulators:start --project ghostinthearchive &
    EMULATOR_PID=$!

    # エミュレータ起動を待つ
    sleep 5
    log_success "Firebase エミュレータが起動しました"
    echo "  - Emulator UI: http://localhost:4000"
    echo "  - Firestore:   localhost:8080"
    echo "  - Storage:     localhost:9199"
    echo ""
}

# 引数処理
MODE="${1:-all}"

case "$MODE" in
    "emulator")
        start_emulator
        wait $EMULATOR_PID
        ;;

    "web")
        log_info "Next.js開発サーバーを起動します..."
        cd web
        npm run dev
        ;;

    "agent")
        log_info "Pythonエージェントを起動します..."
        # uvがインストールされているか確認
        if command -v uv &> /dev/null; then
            uv run python main.py "${@:2}"
        else
            python main.py "${@:2}"
        fi
        ;;

    "all")
        log_info "Firebase エミュレータ + Next.js を同時起動します..."

        # Firebase エミュレータをバックグラウンドで起動
        start_emulator

        # Next.js開発サーバーをバックグラウンドで起動
        log_info "Next.js開発サーバーを起動中..."
        (cd web && npm run dev) &
        NEXTJS_PID=$!

        # 起動を待つ
        sleep 3

        log_success "開発環境が起動しました"
        echo ""
        echo "  - Emulator UI: http://localhost:4000"
        echo "  - Next.js:     http://localhost:3000"
        echo "  - Admin:       http://localhost:3000/admin"
        echo ""
        echo "パイプラインを実行するには別ターミナルで:"
        echo "  ./scripts/dev.sh agent \"調査クエリ\""
        echo ""
        echo "終了するには Ctrl+C を押してください"
        echo ""

        # プロセスを監視
        wait $NEXTJS_PID
        ;;

    "help"|"-h"|"--help")
        echo "Usage: $0 [mode] [args...]"
        echo ""
        echo "Modes:"
        echo "  all      - Firebase エミュレータ + Next.js を同時起動（デフォルト）"
        echo "  emulator - Firebase エミュレータのみ起動"
        echo "  web      - Next.js開発サーバーのみ起動"
        echo "  agent    - Pythonエージェントを実行（引数でクエリ指定可）"
        echo "  help     - このヘルプを表示"
        echo ""
        echo "Examples:"
        echo "  $0 all"
        echo "  $0 agent \"1840年代のボストンの歴史的矛盾を調査せよ\""
        echo ""
        ;;

    *)
        log_error "不明なモード: $MODE"
        echo "使用方法: $0 [all|emulator|web|agent|help]"
        exit 1
        ;;
esac
