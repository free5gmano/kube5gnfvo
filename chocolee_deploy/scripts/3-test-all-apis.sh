#!/bin/bash

################################################################################
# Kube5GNfvo API 完整功能測試腳本
# 功能：測試所有 API 端點的功能
################################################################################

set -e

# 顏色定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# 計數器
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0

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

log_test() {
    echo -e "${CYAN}[TEST]${NC} $1"
}

# 檢查必要工具
check_tools() {
    log_info "檢查必要工具..."
    
    if ! command -v curl &> /dev/null; then
        log_error "curl 未安裝"
        exit 1
    fi
    
    if ! command -v jq &> /dev/null; then
        log_warning "jq 未安裝，某些功能可能受限"
    fi
    
    log_success "工具檢查完成"
}

# 獲取 API 基礎 URL
get_base_url() {
    log_info "獲取 API 基礎 URL..."
    
    # 獲取 Node IP
    NODE_IP=$(kubectl get nodes -o jsonpath='{.items[0].status.addresses[?(@.type=="InternalIP")].address}' 2>/dev/null)
    
    if [ -z "$NODE_IP" ]; then
        log_error "無法獲取 Node IP"
        exit 1
    fi
    
    export BASE_URL="http://$NODE_IP:30888"
    export API_VERSION="v1"
    
    log_success "API 基礎 URL: $BASE_URL"
}

# 測試端點函數
test_endpoint() {
    local method=$1
    local endpoint=$2
    local data=$3
    local expected_code=$4
    local description=$5
    
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    
    log_test "[$TOTAL_TESTS] $description"
    
    if [ -z "$data" ]; then
        response=$(curl -s -w "\n%{http_code}" -X $method \
            -H "Content-Type: application/json" \
            "$BASE_URL$endpoint" 2>/dev/null)
    else
        response=$(curl -s -w "\n%{http_code}" -X $method \
            -H "Content-Type: application/json" \
            -d "$data" \
            "$BASE_URL$endpoint" 2>/dev/null)
    fi
    
    http_code=$(echo "$response" | tail -n1)
    body=$(echo "$response" | head -n-1)
    
    if [ "$http_code" = "$expected_code" ]; then
        log_success "[$TOTAL_TESTS] $description (HTTP $http_code)"
        PASSED_TESTS=$((PASSED_TESTS + 1))
        
        # 如果有 jq，嘗試格式化 JSON 響應
        if command -v jq &> /dev/null && [ -n "$body" ]; then
            echo "$body" | jq '.' 2>/dev/null | head -5 || echo "$body" | head -c 100
        fi
    else
        log_error "[$TOTAL_TESTS] $description (期望: $expected_code, 實際: $http_code)"
        FAILED_TESTS=$((FAILED_TESTS + 1))
        
        # 顯示錯誤響應
        if [ -n "$body" ]; then
            echo "  響應: $body" | head -c 200
        fi
    fi
    
    echo ""
}

# 測試 NS Lifecycle Management API
test_ns_lifecycle_api() {
    echo ""
    echo "╔════════════════════════════════════════════════════════════════╗"
    echo "║     NS Lifecycle Management API 測試                          ║"
    echo "╚════════════════════════════════════════════════════════════════╝"
    echo ""
    
    # 1. 獲取 NS 實例列表
    test_endpoint "GET" "/nslcm/$API_VERSION/ns_instances/" "" "200" \
        "獲取 NS 實例列表"
    
    # 2. 建立 NS 實例
    NS_DATA='{
        "nsdId": "test-nsd-id",
        "nsName": "test-ns-instance",
        "nsDescription": "Test NS Instance"
    }'
    test_endpoint "POST" "/nslcm/$API_VERSION/ns_instances/" "$NS_DATA" "201" \
        "建立 NS 實例"
    
    # 3. 獲取訂閱列表
    test_endpoint "GET" "/nslcm/$API_VERSION/subscriptions/" "" "200" \
        "獲取訂閱列表"
}

# 測試 VNF Package Management API
test_vnf_package_api() {
    echo ""
    echo "╔════════════════════════════════════════════════════════════════╗"
    echo "║     VNF Package Management API 測試                           ║"
    echo "╚════════════════════════════════════════════════════════════════╝"
    echo ""
    
    # 1. 獲取 VNF 包列表
    test_endpoint "GET" "/vnfpkgm/$API_VERSION/vnf_packages/" "" "200" \
        "獲取 VNF 包列表"
    
    # 2. 建立 VNF 包
    VNF_DATA='{
        "userDefinedData": {
            "name": "test-vnf-package",
            "version": "1.0.0"
        }
    }'
    test_endpoint "POST" "/vnfpkgm/$API_VERSION/vnf_packages/" "$VNF_DATA" "201" \
        "建立 VNF 包"
}

# 測試 NSD Management API
test_nsd_api() {
    echo ""
    echo "╔════════════════════════════════════════════════════════════════╗"
    echo "║     NSD Management API 測試                                   ║"
    echo "╚════════════════════════════════════════════════════════════════╝"
    echo ""
    
    # 1. 獲取 NSD 列表
    test_endpoint "GET" "/nsd/$API_VERSION/ns_descriptors/" "" "200" \
        "獲取 NSD 列表"
    
    # 2. 建立 NSD
    NSD_DATA='{
        "userDefinedData": {
            "name": "test-nsd",
            "version": "1.0.0"
        }
    }'
    test_endpoint "POST" "/nsd/$API_VERSION/ns_descriptors/" "$NSD_DATA" "201" \
        "建立 NSD"
}

# 測試 VNF Lifecycle Management API
test_vnf_lifecycle_api() {
    echo ""
    echo "╔════════════════════════════════════════════════════════════════╗"
    echo "║     VNF Lifecycle Management API 測試                         ║"
    echo "╚════════════════════════════════════════════════════════════════╝"
    echo ""
    
    # 1. 獲取 VNF 實例列表
    test_endpoint "GET" "/vnflcm/$API_VERSION/vnf_instances/" "" "200" \
        "獲取 VNF 實例列表"
}

# 測試 Fault Management API
test_fault_management_api() {
    echo ""
    echo "╔════════════════════════════════════════════════════════════════╗"
    echo "║     Fault Management API 測試                                 ║"
    echo "╚════════════════════════════════════════════════════════════════╝"
    echo ""
    
    # 1. 獲取告警列表
    test_endpoint "GET" "/nsfm/$API_VERSION/alarms/" "" "200" \
        "獲取告警列表" || true
}

# 測試 Performance Management API
test_performance_management_api() {
    echo ""
    echo "╔════════════════════════════════════════════════════════════════╗"
    echo "║     Performance Management API 測試                           ║"
    echo "╚════════════════════════════════════════════════════════════════╝"
    echo ""
    
    # 1. 獲取性能指標列表
    test_endpoint "GET" "/nspm/$API_VERSION/performance_metrics/" "" "200" \
        "獲取性能指標列表" || true
}

# 測試 VIM Management API
test_vim_management_api() {
    echo ""
    echo "╔════════════════════════════════════════════════════════════════╗"
    echo "║     VIM Management API 測試                                   ║"
    echo "╚════════════════════════════════════════════════════════════════╝"
    echo ""
    
    # 1. 獲取 VIM 列表
    test_endpoint "GET" "/vimm/$API_VERSION/vims/" "" "200" \
        "獲取 VIM 列表" || true
}

# 測試 VNF Package Subscription API
test_vnf_package_subscription_api() {
    echo ""
    echo "╔════════════════════════════════════════════════════════════════╗"
    echo "║     VNF Package Subscription API 測試                         ║"
    echo "╚════════════════════════════════════════════════════════════════╝"
    echo ""
    
    # 1. 獲取 VNF 包訂閱列表
    test_endpoint "GET" "/vnfpkgm/$API_VERSION/subscriptions/" "" "200" \
        "獲取 VNF 包訂閱列表" || true
}

# 測試 NSD Subscription API
test_nsd_subscription_api() {
    echo ""
    echo "╔════════════════════════════════════════════════════════════════╗"
    echo "║     NSD Subscription API 測試                                 ║"
    echo "╚════════════════════════════════════════════════════════════════╝"
    echo ""
    
    # 1. 獲取 NSD 訂閱列表
    test_endpoint "GET" "/nsd/$API_VERSION/subscriptions/" "" "200" \
        "獲取 NSD 訂閱列表" || true
}

# 測試應用健康狀態
test_application_health() {
    echo ""
    echo "╔════════════════════════════════════════════════════════════════╗"
    echo "║     應用健康狀態檢查                                           ║"
    echo "╚════════════════════════════════════════════════════════════════╝"
    echo ""
    
    log_info "檢查應用 Pod 狀態..."
    kubectl get pods -n kube5gnfvo -l app=kube5gnfvo
    
    echo ""
    log_info "檢查 MySQL Pod 狀態..."
    kubectl get pods -n kube5gnfvo -l app=kube5gnfvo-mysql
    
    echo ""
    log_info "檢查應用資源使用情況..."
    kubectl top pods -n kube5gnfvo 2>/dev/null || log_warning "無法獲取資源使用情況"
}

# 生成測試報告
generate_report() {
    echo ""
    echo "╔════════════════════════════════════════════════════════════════╗"
    echo "║     API 功能測試報告                                           ║"
    echo "╚════════════════════════════════════════════════════════════════╝"
    echo ""
    
    echo "測試統計："
    echo "  總測試數: $TOTAL_TESTS"
    echo -e "  ${GREEN}通過: $PASSED_TESTS${NC}"
    echo -e "  ${RED}失敗: $FAILED_TESTS${NC}"
    echo ""
    
    if [ $TOTAL_TESTS -gt 0 ]; then
        PASS_RATE=$((PASSED_TESTS * 100 / TOTAL_TESTS))
        echo "  通過率: $PASS_RATE%"
    fi
    
    echo ""
    
    if [ $FAILED_TESTS -eq 0 ]; then
        echo -e "${GREEN}✓ 所有測試通過！${NC}"
    else
        echo -e "${RED}✗ 有 $FAILED_TESTS 個測試失敗${NC}"
    fi
    
    echo ""
    echo "╔════════════════════════════════════════════════════════════════╗"
    echo "║     測試完成                                                   ║"
    echo "╚════════════════════════════════════════════════════════════════╝"
    echo ""
}

# 主函數
main() {
    echo ""
    echo "╔════════════════════════════════════════════════════════════════╗"
    echo "║     Kube5GNfvo API 完整功能測試                               ║"
    echo "║     此腳本將測試所有 API 端點                                 ║"
    echo "╚════════════════════════════════════════════════════════════════╝"
    echo ""
    
    # 檢查工具
    check_tools
    
    # 獲取 API 基礎 URL
    get_base_url
    
    # 測試各個 API
    test_ns_lifecycle_api
    test_vnf_package_api
    test_nsd_api
    test_vnf_lifecycle_api
    test_fault_management_api
    test_performance_management_api
    test_vim_management_api
    test_vnf_package_subscription_api
    test_nsd_subscription_api
    
    # 測試應用健康狀態
    test_application_health
    
    # 生成報告
    generate_report
    
    # 返回適當的退出碼
    if [ $FAILED_TESTS -eq 0 ]; then
        exit 0
    else
        exit 1
    fi
}

# 運行主函數
main "$@"
