#!/bin/bash

################################################################################
# Kube5GNfvo 應用部署腳本
# 功能：準備 Kube5GNfvo 應用和 MySQL 資料庫配置（不自動啟動 Pod）
################################################################################

set -e

# 設置環境變數以避免互動式提示
export NEEDRESTART_MODE=a
export DEBIAN_FRONTEND=noninteractive

# 顏色定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日誌函數
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[✓]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[⚠]${NC} $1"
}

log_error() {
    echo -e "${RED}[✗]${NC} $1"
}


# 載入環境變數
load_env() {
    log_info "載入環境變數..."

    # 獲取腳本所在目錄，然後往上一層到 chocolee_deploy
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    DEPLOY_DIR="$(dirname "$(dirname "$SCRIPT_DIR")")"
    ENV_FILE="$DEPLOY_DIR/.env"

   if [ -f "$ENV_FILE" ]; then
    set -a
    # shellcheck disable=SC1090
    source "$ENV_FILE"
    set +a
    log_success ".env 檔案已載入 ($ENV_FILE)"
    else
        log_warning ".env 檔案不存在 ($ENV_FILE)，使用預設值"
        export NAMESPACE=kube5gnfvo
        export MYSQL_ROOT_PASSWORD=password
        export MYSQL_DATABASE=kube5gnfvo
        export APP_PORT=8000
        export APP_NODE_PORT=30888
    fi

    echo ""
    echo "部署配置："
    echo "  命名空間: $NAMESPACE"
    echo "  MySQL 密碼: $MYSQL_ROOT_PASSWORD"
    echo "  MySQL 資料庫: $MYSQL_DATABASE"
    echo "  應用端口: $APP_PORT"
    echo "  NodePort: $APP_NODE_PORT"
    echo ""
}

# 建立資料庫
setup_database() {
    echo -e "${BLUE}[6/8] 設定資料庫...${NC}"

    # 檢查資料庫連線
    if ! MYSQL_PWD="$KUBE5GNFVO_MYSQL_PASSWORD" \
        mysql -h "$KUBE5GNFVO_MYSQL_HOST" -P "$KUBE5GNFVO_MYSQL_PORT" \
        -u "$KUBE5GNFVO_MYSQL_USER" -e "SELECT 1" &> /dev/null; then
        echo -e "${RED}無法連線到 MySQL 伺服器${NC}"
        echo "請檢查以下設定:"
        echo "  Host: $KUBE5GNFVO_MYSQL_HOST"
        echo "  Port: $KUBE5GNFVO_MYSQL_PORT"
        echo "  User: $KUBE5GNFVO_MYSQL_USER"
        exit 1
    fi

    MYSQL_PWD="$KUBE5GNFVO_MYSQL_PASSWORD" \
          mysql -h "$KUBE5GNFVO_MYSQL_HOST" -P "$KUBE5GNFVO_MYSQL_PORT" \
          -u "$KUBE5GNFVO_MYSQL_USER" -e "CREATE DATABASE IF NOT EXISTS \`$KUBE5GNFVO_DB_NAME\`;" || true

    echo -e "${GREEN}✓ 資料庫設定完成${NC}"
}


# 主函數
main() {
    load_env
    setup_database
}

# 運行主函數
main "$@"