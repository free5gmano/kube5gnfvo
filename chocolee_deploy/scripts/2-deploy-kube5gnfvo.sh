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

# 檢查 kubectl 是否可用
check_kubectl() {
    if ! command -v kubectl &> /dev/null; then
        log_error "kubectl 未安裝或不在 PATH 中"
        exit 1
    fi

    if ! kubectl cluster-info &>/dev/null; then
        log_error "無法連接到 Kubernetes 叢集"
        exit 1
    fi

    log_success "kubectl 已連接到叢集"
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

# 建立儲存目錄
create_storage_directories() {
    log_info "建立儲存目錄..."

    mkdir -p /mnt/kube5gnfvo 2>/dev/null || true
    mkdir -p /mnt/kube5gnfvo-mysql 2>/dev/null || true
    chmod 777 /mnt/kube5gnfvo 2>/dev/null || true
    chmod 777 /mnt/kube5gnfvo-mysql 2>/dev/null || true

    log_success "儲存目錄建立完成"
}

# 修改 etcd 證書文件權限
fix_etcd_certificate_permissions() {
    log_info "修改 etcd 證書文件權限..."

    if [ -d "/etc/kubernetes/pki/etcd" ]; then
        sudo chmod 644 /etc/kubernetes/pki/etcd/server.key 2>/dev/null || true
        sudo chmod 644 /etc/kubernetes/pki/etcd/healthcheck-client.key 2>/dev/null || true
        sudo chmod 644 /etc/kubernetes/pki/etcd/server.crt 2>/dev/null || true
        sudo chmod 644 /etc/kubernetes/pki/etcd/ca.crt 2>/dev/null || true
        log_success "etcd 證書文件權限已修改"
    else
        log_warning "etcd 證書目錄不存在，跳過"
    fi
}

# 部署 MySQL
deploy_mysql() {
    log_info "部署 MySQL 資料庫..."

    # 獲取腳本所在目錄，然後往上一層到 chocolee_deploy
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    DEPLOY_DIR="$(dirname "$SCRIPT_DIR")"
    MYSQL_FILE="$DEPLOY_DIR/kubernetes/mysql/kube5gnfvo-mysql-simple.yaml"

    if [ ! -f "$MYSQL_FILE" ]; then
        log_error "找不到 MySQL 配置文件: $MYSQL_FILE"
        exit 1
    fi

    log_info "部署 MySQL 配置文件："
    echo "  $MYSQL_FILE"
    echo ""

    kubectl apply -f "$MYSQL_FILE"

    # 等待 MySQL Pod 就緒
    log_info "等待 MySQL Pod 就緒（最多 120 秒）..."
    if kubectl wait --for=condition=ready pod \
        -l app=kube5gnfvo-mysql \
        -n kube5gnfvo \
        --timeout=120s 2>/dev/null; then
        log_success "MySQL 已啟動"
    else
        log_warning "MySQL 啟動超時，但繼續進行..."
    fi
}


# 部署應用（直接執行 Python）
deploy_application() {
    log_info "準備啟動 Kube5GNfvo 應用..."

    # 獲取項目根目錄
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    PROJECT_DIR="$(dirname "$(dirname "$SCRIPT_DIR")")"

    echo ""
    echo "執行以下命令啟動應用："
    echo "  cd $PROJECT_DIR"
    echo "  python3 manage.py runserver 0.0.0.0:8000"
    echo "  第一次時請先轉移資料庫"
    echo "  python3 manage.py migrate"
    echo ""
}

# 驗證部署
verify_deployment() {
    log_info "部署配置已準備完成"
}

# 測試 API 連接
test_api_connection() {
    log_info "應用啟動後，可以測試 API 連接"
}

# 顯示部署信息
show_deployment_info() {
    log_info "部署信息..."

    echo ""
    echo "╔════════════════════════════════════════════════════════════════╗"
    echo "║     部署配置已準備完成！                                       ║"
    echo "╚════════════════════════════════════════════════════════════════╝"
    echo ""
}

# 主函數
main() {
    echo ""
    echo "╔════════════════════════════════════════════════════════════════╗"
    echo "║     Kube5GNfvo 應用部署腳本                                     ║"
    echo "╚════════════════════════════════════════════════════════════════╝"
    echo ""

    # 檢查 kubectl
    check_kubectl

    # 載入環境變數
    load_env

    # 建立儲存目錄
    create_storage_directories

    # 修改 etcd 證書文件權限
    fix_etcd_certificate_permissions

    # 部署 MySQL
    deploy_mysql

    # 部署應用
    deploy_application

    # 驗證部署
    verify_deployment

    # 測試 API 連接
    test_api_connection

    # 顯示部署信息
    show_deployment_info

    echo ""
    echo "╔════════════════════════════════════════════════════════════════╗"
    echo "║     應用部署配置準備完成！                                       ║"
    echo "║     下一步：部署 MySQL 並直接執行 Python 啟動應用                 ║"
    echo "╚════════════════════════════════════════════════════════════════╝"
    echo ""
}

# 運行主函數
main "$@"