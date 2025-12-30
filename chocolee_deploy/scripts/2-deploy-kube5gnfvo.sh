#!/bin/bash

################################################################################
# Kube5GNfvo 應用部署腳本
# 功能：在 Kubernetes 環境中部署 Kube5GNfvo 應用和 MySQL 資料庫
################################################################################

set -e

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
    
    if [ -f .env ]; then
        export $(cat .env | grep -v '#' | xargs)
        log_success ".env 檔案已載入"
    else
        log_warning ".env 檔案不存在，使用預設值"
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
    
    sudo mkdir -p /mnt/kube5gnfvo
    sudo mkdir -p /mnt/kube5gnfvo-mysql
    sudo chmod 777 /mnt/kube5gnfvo
    sudo chmod 777 /mnt/kube5gnfvo-mysql
    
    log_success "儲存目錄建立完成"
}

# 部署 MySQL
deploy_mysql() {
    log_info "部署 MySQL 資料庫..."
    
    # 部署 MySQL
    kubectl apply -f kubernetes/mysql/kube5gnfvo-mysql-simple.yaml
    
    # 等待 MySQL Pod 就緒
    log_info "等待 MySQL Pod 就緒（最多 120 秒）..."
    if kubectl wait --for=condition=ready pod \
        -l app=kube5gnfvo-mysql \
        -n kube5gnfvo \
        --timeout=120s 2>/dev/null; then
        log_success "MySQL 已啟動"
    else
        log_warning "MySQL 啟動超時，繼續進行..."
    fi
    
    # 驗證 MySQL 連接
    log_info "驗證 MySQL 連接..."
    MYSQL_POD=$(kubectl get pod -n kube5gnfvo -l app=kube5gnfvo-mysql -o jsonpath='{.items[0].metadata.name}' 2>/dev/null)
    
    if [ -n "$MYSQL_POD" ]; then
        if kubectl exec -n kube5gnfvo $MYSQL_POD -- \
            mysql -u root -p$MYSQL_ROOT_PASSWORD -e "SHOW DATABASES;" &>/dev/null; then
            log_success "MySQL 連接驗證成功"
        else
            log_warning "MySQL 連接驗證失敗，但繼續進行"
        fi
    fi
}

# 部署應用
deploy_application() {
    log_info "部署 Kube5GNfvo 應用..."
    
    # 部署應用
    kubectl apply -f kubernetes/app/kube5gnfvo-app-deploy.yaml
    
    # 等待應用 Pod 就緒
    log_info "等待應用 Pod 就緒（最多 180 秒）..."
    if kubectl wait --for=condition=ready pod \
        -l app=kube5gnfvo \
        -n kube5gnfvo \
        --timeout=180s 2>/dev/null; then
        log_success "應用已啟動"
    else
        log_warning "應用啟動超時，檢查日誌..."
        APP_POD=$(kubectl get pod -n kube5gnfvo -l app=kube5gnfvo -o jsonpath='{.items[0].metadata.name}' 2>/dev/null)
        if [ -n "$APP_POD" ]; then
            kubectl logs -n kube5gnfvo $APP_POD --tail=50
        fi
    fi
}

# 執行資料庫遷移
run_migrations() {
    log_info "執行資料庫遷移..."
    
    APP_POD=$(kubectl get pod -n kube5gnfvo -l app=kube5gnfvo -o jsonpath='{.items[0].metadata.name}' 2>/dev/null)
    
    if [ -z "$APP_POD" ]; then
        log_warning "無法找到應用 Pod，跳過遷移"
        return
    fi
    
    if kubectl exec -n kube5gnfvo $APP_POD -- \
        python3 manage.py migrate 2>/dev/null; then
        log_success "資料庫遷移完成"
    else
        log_warning "資料庫遷移失敗，但繼續進行"
    fi
}

# 驗證部署
verify_deployment() {
    log_info "驗證部署..."
    
    echo ""
    echo "=========================================="
    echo "Kube5GNfvo 部署驗證"
    echo "=========================================="
    echo ""
    
    # 檢查命名空間
    log_info "命名空間:"
    kubectl get namespace kube5gnfvo
    
    # 檢查 Pod
    echo ""
    log_info "Pod 狀態:"
    kubectl get pods -n kube5gnfvo
    
    # 檢查 Service
    echo ""
    log_info "Service:"
    kubectl get svc -n kube5gnfvo
    
    # 檢查 PVC
    echo ""
    log_info "PersistentVolumeClaim:"
    kubectl get pvc -n kube5gnfvo
    
    # 檢查 Deployment
    echo ""
    log_info "Deployment:"
    kubectl get deployment -n kube5gnfvo
    
    echo ""
    echo "=========================================="
}

# 測試 API 連接
test_api_connection() {
    log_info "測試 API 連接..."
    
    # 獲取 Node IP
    NODE_IP=$(kubectl get nodes -o jsonpath='{.items[0].status.addresses[?(@.type=="InternalIP")].address}' 2>/dev/null)
    
    if [ -z "$NODE_IP" ]; then
        log_warning "無法獲取 Node IP"
        return
    fi
    
    BASE_URL="http://$NODE_IP:30888"
    
    echo ""
    echo "API 基礎 URL: $BASE_URL"
    echo ""
    
    # 測試 NS Lifecycle API
    log_info "測試 NS Lifecycle API..."
    if curl -s -w "HTTP %{http_code}\n" -X GET "$BASE_URL/nslcm/v1/ns_instances/" | grep -q "HTTP 200"; then
        log_success "NS Lifecycle API 可訪問"
    else
        log_warning "NS Lifecycle API 無法訪問"
    fi
    
    # 測試 VNF Package API
    log_info "測試 VNF Package API..."
    if curl -s -w "HTTP %{http_code}\n" -X GET "$BASE_URL/vnfpkgm/v1/vnf_packages/" | grep -q "HTTP 200"; then
        log_success "VNF Package API 可訪問"
    else
        log_warning "VNF Package API 無法訪問"
    fi
    
    # 測試 NSD API
    log_info "測試 NSD API..."
    if curl -s -w "HTTP %{http_code}\n" -X GET "$BASE_URL/nsd/v1/ns_descriptors/" | grep -q "HTTP 200"; then
        log_success "NSD API 可訪問"
    else
        log_warning "NSD API 無法訪問"
    fi
}

# 顯示部署信息
show_deployment_info() {
    log_info "部署信息..."
    
    echo ""
    echo "=========================================="
    echo "部署完成！"
    echo "=========================================="
    echo ""
    
    # 獲取 Node IP
    NODE_IP=$(kubectl get nodes -o jsonpath='{.items[0].status.addresses[?(@.type=="InternalIP")].address}' 2>/dev/null)
    
    if [ -n "$NODE_IP" ]; then
        echo "API 基礎 URL: http://$NODE_IP:30888"
        echo ""
        echo "常用命令："
        echo "  查看 Pod 日誌:"
        echo "    kubectl logs -n kube5gnfvo -l app=kube5gnfvo -f"
        echo ""
        echo "  進入應用 Pod:"
        echo "    kubectl exec -it -n kube5gnfvo \$(kubectl get pod -n kube5gnfvo -l app=kube5gnfvo -o jsonpath='{.items[0].metadata.name}') -- bash"
        echo ""
        echo "  進入 MySQL Pod:"
        echo "    kubectl exec -it -n kube5gnfvo \$(kubectl get pod -n kube5gnfvo -l app=kube5gnfvo-mysql -o jsonpath='{.items[0].metadata.name}') -- bash"
        echo ""
        echo "  查看資源使用情況:"
        echo "    kubectl top pods -n kube5gnfvo"
        echo ""
    fi
    
    echo "=========================================="
}

# 主函數
main() {
    echo ""
    echo "╔════════════════════════════════════════════════════════════════╗"
    echo "║     Kube5GNfvo 應用部署腳本                                    ║"
    echo "║     此腳本將部署 MySQL 和 Kube5GNfvo 應用                      ║"
    echo "╚════════════════════════════════════════════════════════════════╝"
    echo ""
    
    # 檢查 kubectl
    check_kubectl
    
    # 載入環境變數
    load_env
    
    # 建立儲存目錄
    create_storage_directories
    
    # 部署 MySQL
    deploy_mysql
    
    # 部署應用
    deploy_application
    
    # 執行資料庫遷移
    run_migrations
    
    # 驗證部署
    verify_deployment
    
    # 測試 API 連接
    test_api_connection
    
    # 顯示部署信息
    show_deployment_info
    
    echo ""
    echo "╔════════════════════════════════════════════════════════════════╗"
    echo "║     應用部署完成！                                             ║"
    echo "║     下一步：運行 3-test-all-apis.sh 進行 API 功能測試          ║"
    echo "╚════════════════════════════════════════════════════════════════╝"
    echo ""
}

# 運行主函數
main "$@"
