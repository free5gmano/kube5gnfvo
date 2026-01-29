#!/bin/bash

################################################################################
# 獲取 Worker Node 加入令牌腳本
# 功能：在 Master 節點上生成加入令牌供 Worker Node 使用
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

# 檢查是否在 Master 節點
check_master_node() {
    if [ ! -f /etc/kubernetes/admin.conf ]; then
        log_error "此腳本必須在 Master 節點上執行"
        exit 1
    fi
    log_success "確認為 Master 節點"
}

# 獲取加入令牌
get_join_command() {
    log_info "生成加入令牌..."
    echo ""
    
    # 執行 kubeadm token create --print-join-command
    JOIN_COMMAND=$(sudo kubeadm token create --print-join-command)
    
    log_success "加入令牌已生成"
    echo ""
    echo "╔════════════════════════════════════════════════════════════════╗"
    echo "║     在 Worker Node 上執行以下命令加入叢集：                      ║"
    echo "╚════════════════════════════════════════════════════════════════╝"
    echo ""
    echo "$JOIN_COMMAND"
    echo ""
    
    # 提取令牌和 CA 證書雜湊
    TOKEN=$(echo "$JOIN_COMMAND" | awk '{print $5}')
    CA_CERT_HASH=$(echo "$JOIN_COMMAND" | awk '{print $7}')
    MASTER_IP=$(echo "$JOIN_COMMAND" | awk '{print $3}' | cut -d: -f1)
    
    echo "或者使用以下參數執行 3-add-worker-node.sh："
    echo ""
    echo "  bash 3-add-worker-node.sh \\"
    echo "    --master-ip $MASTER_IP \\"
    echo "    --token $TOKEN \\"
    echo "    --ca-cert-hash $CA_CERT_HASH"
    echo ""
}

# 顯示現有節點
show_nodes() {
    log_info "現有叢集節點："
    echo ""
    kubectl get nodes -o wide
    echo ""
}

# 主函數
main() {
    echo ""
    echo "╔════════════════════════════════════════════════════════════════╗"
    echo "║     獲取 Worker Node 加入令牌                                   ║"
    echo "╚════════════════════════════════════════════════════════════════╝"
    echo ""
    
    check_master_node
    show_nodes
    get_join_command
    
    log_success "令牌生成完成！"
}

main "$@"
