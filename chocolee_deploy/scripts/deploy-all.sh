#!/bin/bash

################################################################################
# Kube5GNfvo 完整部署和測試主控腳本
# 功能：協調執行環境部署、應用部署和 API 測試
################################################################################

set -e

# 顏色定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
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

log_section() {
    echo ""
    echo "╔════════════════════════════════════════════════════════════════╗"
    echo "║     $1"
    echo "╚════════════════════════════════════════════════════════════════╝"
    echo ""
}

# 顯示使用說明
show_usage() {
    echo "使用方法: $0 [選項]"
    echo ""
    echo "選項:"
    echo "  all          執行完整部署流程（環境 + 應用 + 測試）"
    echo "  env          只執行環境部署"
    echo "  app          只執行應用部署"
    echo "  test         只執行 API 測試"
    echo "  help         顯示此幫助信息"
    echo ""
    echo "示例:"
    echo "  $0 all       # 執行完整部署"
    echo "  $0 env       # 只部署環境"
    echo "  $0 app       # 只部署應用"
    echo "  $0 test      # 只執行測試"
}

# 檢查腳本是否存在
check_scripts() {
    log_info "檢查部署腳本..."
    
    local scripts=(
        "1-setup-environment.sh"
        "2-deploy-kube5gnfvo.sh"
        "3-test-all-apis.sh"
    )
    
    for script in "${scripts[@]}"; do
        if [ ! -f "$script" ]; then
            log_error "腳本 $script 不存在"
            exit 1
        fi
    done
    
    log_success "所有腳本檢查完成"
}

# 設定腳本權限
set_script_permissions() {
    log_info "設定腳本權限..."
    
    chmod +x 1-setup-environment.sh
    chmod +x 2-deploy-kube5gnfvo.sh
    chmod +x 3-test-all-apis.sh
    
    log_success "腳本權限設定完成"
}

# 執行環境部署
run_environment_setup() {
    log_section "第 1 步：環境部署"
    
    log_info "開始執行環境部署腳本..."
    
    if sudo bash 1-setup-environment.sh; then
        log_success "環境部署完成"
        return 0
    else
        log_error "環境部署失敗"
        return 1
    fi
}

# 執行應用部署
run_application_deployment() {
    log_section "第 2 步：應用部署"
    
    log_info "開始執行應用部署腳本..."
    
    if bash 2-deploy-kube5gnfvo.sh; then
        log_success "應用部署完成"
        return 0
    else
        log_error "應用部署失敗"
        return 1
    fi
}

# 執行 API 測試
run_api_testing() {
    log_section "第 3 步：API 功能測試"
    
    log_info "開始執行 API 測試腳本..."
    
    if bash 3-test-all-apis.sh; then
        log_success "API 測試完成"
        return 0
    else
        log_warning "API 測試有失敗項目"
        return 1
    fi
}

# 執行完整部署流程
run_full_deployment() {
    log_section "Kube5GNfvo 完整部署流程"
    
    local start_time=$(date +%s)
    
    # 執行環境部署
    if ! run_environment_setup; then
        log_error "環境部署失敗，中止部署"
        exit 1
    fi
    
    # 執行應用部署
    if ! run_application_deployment; then
        log_error "應用部署失敗，中止部署"
        exit 1
    fi
    
    # 執行 API 測試
    if ! run_api_testing; then
        log_warning "API 測試有失敗項目，但部署已完成"
    fi
    
    local end_time=$(date +%s)
    local duration=$((end_time - start_time))
    
    log_section "部署完成"
    
    echo "部署耗時: $((duration / 60)) 分 $((duration % 60)) 秒"
    echo ""
    log_success "Kube5GNfvo 部署完成！"
}

# 主函數
main() {
    local action="${1:-all}"
    
    echo ""
    echo "╔════════════════════════════════════════════════════════════════╗"
    echo "║     Kube5GNfvo 部署和測試主控腳本                             ║"
    echo "╚════════════════════════════════════════════════════════════════╝"
    echo ""
    
    # 檢查腳本
    check_scripts
    
    # 設定腳本權限
    set_script_permissions
    
    case "$action" in
        all)
            run_full_deployment
            ;;
        env)
            run_environment_setup
            ;;
        app)
            run_application_deployment
            ;;
        test)
            run_api_testing
            ;;
        help)
            show_usage
            ;;
        *)
            log_error "未知的選項: $action"
            show_usage
            exit 1
            ;;
    esac
}

# 運行主函數
main "$@"
