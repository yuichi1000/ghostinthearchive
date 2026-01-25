#!/bin/bash
#
# Ghost in the Archive - 開発環境起動スクリプト
# Next.js開発サーバーとPythonエージェントを同時起動
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

# 引数処理
MODE="${1:-all}"

case "$MODE" in
    "web")
        log_info "Next.js開発サーバーを起動します..."
        cd web
        npm run dev
        ;;

    "agent")
        log_info "Pythonエージェントを起動します..."
        # uvがインストールされているか確認
        if command -v uv &> /dev/null; then
            uv run python main.py
        else
            python main.py
        fi
        ;;

    "all")
        log_info "Next.jsとPythonエージェントを同時起動します..."

        # Next.js開発サーバーをバックグラウンドで起動
        log_info "Next.js開発サーバーを起動中..."
        (cd web && npm run dev) &
        NEXTJS_PID=$!

        # 起動を待つ
        sleep 3

        log_success "開発環境が起動しました"
        echo ""
        echo "  - Next.js: http://localhost:3000"
        echo "  - Admin:   http://localhost:3000/admin"
        echo ""
        echo "終了するには Ctrl+C を押してください"
        echo ""

        # Next.jsプロセスを監視
        wait $NEXTJS_PID
        ;;

    "help"|"-h"|"--help")
        echo "Usage: $0 [mode]"
        echo ""
        echo "Modes:"
        echo "  all    - Next.jsとPythonエージェントを同時起動（デフォルト）"
        echo "  web    - Next.js開発サーバーのみ起動"
        echo "  agent  - Pythonエージェントのみ起動"
        echo "  help   - このヘルプを表示"
        echo ""
        ;;

    *)
        log_error "不明なモード: $MODE"
        echo "使用方法: $0 [all|web|agent|help]"
        exit 1
        ;;
esac
