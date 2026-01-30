#!/bin/bash

################################################################################
# Kubernetes 完全清理腳本
# 功能：完全移除 Kubernetes、Containerd 和所有相關組件
# 警告：此腳本會刪除所有 Kubernetes 數據和配置
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

# 檢查是否為 root
check_root() {
    if [ "$EUID" -ne 0 ]; then
        log_error "此腳本需要 root 權限，請使用 sudo 運行"
        exit 1
    fi
}

# 確認操作
confirm_cleanup() {
    echo ""
    echo "╔════════════════════════════════════════════════════════════════╗"
    echo "║                    警告：即將清理 Kubernetes                   ║"
    echo "║                                                                ║"
    echo "║  此操作將：                                                    ║"
    echo "║  1. 停止並移除所有 Kubernetes 組件                            ║"
    echo "║  2. 刪除所有 Kubernetes 配置和數據                            ║"
    echo "║  3. 移除 Docker、cri-dockerd 和 Containerd                    ║"
    echo "║  4. 清理網路配置                                              ║"
    echo "║                                                                ║"
    echo "║  此操作不可逆！請確保已備份重要數據                           ║"
    echo "╚════════════════════════════════════════════════════════════════╝"
    echo ""
    
    read -p "確認要繼續嗎？(yes/no): " confirm
    if [ "$confirm" != "yes" ]; then
        log_info "操作已取消"
        exit 0
    fi
}

# 重置 kubeadm
reset_kubeadm() {
    log_info "重置 kubeadm..."
    
    # 先強制殺死所有 Kubernetes 相關的進程
    pkill -9 kube-apiserver 2>/dev/null || true
    pkill -9 kube-controller-manager 2>/dev/null || true
    pkill -9 kube-scheduler 2>/dev/null || true
    pkill -9 kube-proxy 2>/dev/null || true
    pkill -9 kubelet 2>/dev/null || true
    pkill -9 etcd 2>/dev/null || true
    sleep 2
    
    if command -v kubeadm &>/dev/null; then
        # 嘗試使用 cri-dockerd socket
        kubeadm reset -f --cri-socket=unix:///var/run/cri-dockerd.sock 2>/dev/null || \
        # 如果失敗，嘗試使用 containerd socket
        kubeadm reset -f --cri-socket=unix:///run/containerd/containerd.sock 2>/dev/null || \
        # 最後嘗試不指定 socket
        kubeadm reset -f 2>/dev/null || true
        log_success "kubeadm 已重置"
    else
        log_warning "kubeadm 未安裝"
    fi
}

# 停止 kubelet
stop_kubelet() {
    log_info "停止 kubelet..."
    
    systemctl stop kubelet 2>/dev/null || true
    systemctl disable kubelet 2>/dev/null || true
    
    log_success "kubelet 已停止"
}

# 停止 Containerd
stop_containerd() {
    log_info "停止 Containerd..."
    
    # 先強制殺死所有 containerd 相關的進程
    pkill -9 containerd-shim 2>/dev/null || true
    pkill -9 containerd 2>/dev/null || true
    sleep 2
    
    systemctl stop containerd 2>/dev/null || true
    systemctl disable containerd 2>/dev/null || true
    
    log_success "Containerd 已停止"
}

# 停止 Docker
stop_docker() {
    log_info "停止 Docker..."
    
    systemctl stop docker 2>/dev/null || true
    systemctl disable docker 2>/dev/null || true
    
    log_success "Docker 已停止"
}

# 停止 cri-dockerd
stop_cri_dockerd() {
    log_info "停止 cri-dockerd..."
    
    systemctl stop cri-docker 2>/dev/null || true
    systemctl disable cri-docker 2>/dev/null || true
    
    log_success "cri-dockerd 已停止"
}

# 清理 Kubernetes 目錄
cleanup_kubernetes_dirs() {
    log_info "清理 Kubernetes 目錄..."
    
    rm -rf /etc/kubernetes/ 2>/dev/null || true
    rm -rf /var/lib/kubelet/ 2>/dev/null || true
    rm -rf /var/lib/etcd/ 2>/dev/null || true
    rm -rf /var/run/kubernetes/ 2>/dev/null || true
    rm -rf $HOME/.kube/ 2>/dev/null || true
    
    log_success "Kubernetes 目錄已清理"
}

# 清理 Containerd 目錄
cleanup_containerd_dirs() {
    log_info "清理 Containerd 目錄..."
    
    # 強制殺死所有 containerd 相關的進程
    pkill -9 containerd-shim 2>/dev/null || true
    pkill -9 containerd 2>/dev/null || true
    sleep 2
    
    rm -rf /etc/containerd/ 2>/dev/null || true
    rm -rf /var/lib/containerd/ 2>/dev/null || true
    rm -rf /run/containerd/ 2>/dev/null || true
    
    log_success "Containerd 目錄已清理"
}

# 清理 Docker 目錄
cleanup_docker_dirs() {
    log_info "清理 Docker 目錄..."
    
    rm -rf /etc/docker/ 2>/dev/null || true
    rm -rf /var/lib/docker/ 2>/dev/null || true
    rm -rf /var/run/docker* 2>/dev/null || true
    
    log_success "Docker 目錄已清理"
}

# 清理 cri-dockerd 目錄
cleanup_cri_dockerd_dirs() {
    log_info "清理 cri-dockerd 目錄..."
    
    rm -rf /var/lib/cri-dockerd/ 2>/dev/null || true
    rm -rf /var/run/cri-dockerd* 2>/dev/null || true
    
    log_success "cri-dockerd 目錄已清理"
}

# 清理 CNI 配置
cleanup_cni() {
    log_info "清理 CNI 配置..."
    
    rm -rf /etc/cni/net.d/ 2>/dev/null || true
    rm -rf /opt/cni/bin/ 2>/dev/null || true
    
    log_success "CNI 配置已清理"
}

cleanup_network_interfaces() {
    log_info "清理殘留的 CNI/OVS 網路介面..."

    # 常見 CNI bridge / flannel / vxlan / ovs
    ip link del cni0 2>/dev/null || true
    ip link del flannel.1 2>/dev/null || true
    ip link del cbr0 2>/dev/null || true
    ip link del docker0 2>/dev/null || true

    # 常見 calico/weave/cilium 殘留（你不一定有，但清掉不會成功也不會中斷）
    ip link del weave 2>/dev/null || true
    ip link del cilium_vxlan 2>/dev/null || true

    # OVS bridge（你腳本有裝 openvswitch，常見會留 br1）
    ovs-vsctl --if-exists del-br br1 2>/dev/null || true
    ovs-vsctl --if-exists del-br br-int 2>/dev/null || true

    log_success "網路介面清理完成"
}


# 清理 iptables 規則
cleanup_iptables() {
    log_info "清理 iptables 規則..."
    
    # 清理 Kubernetes 相關的 iptables 規則
    iptables -F 2>/dev/null || true
    iptables -X 2>/dev/null || true
    iptables -t nat -F 2>/dev/null || true
    iptables -t nat -X 2>/dev/null || true
    iptables -t mangle -F 2>/dev/null || true
    iptables -t mangle -X 2>/dev/null || true
    
    log_success "iptables 規則已清理"
}

# 清理 sysctl 配置
cleanup_sysctl() {
    log_info "清理 sysctl 配置..."
    
    rm -f /etc/sysctl.d/k8s.conf 2>/dev/null || true
    sysctl --system 2>/dev/null || true
    
    log_success "sysctl 配置已清理"
}

# 清理 apt 儲存庫
cleanup_apt_repos() {
    log_info "清理 apt 儲存庫..."
    
    rm -f /etc/apt/sources.list.d/kubernetes.list 2>/dev/null || true
    rm -f /etc/apt/sources.list.d/docker.list 2>/dev/null || true
    rm -f /etc/apt/keyrings/kubernetes-apt-keyring.gpg 2>/dev/null || true
    rm -f /etc/apt/keyrings/docker.gpg 2>/dev/null || true
    rm -f /usr/share/keyrings/docker.gpg 2>/dev/null || true
    rm -f /usr/share/keyrings/docker-archive-keyring.gpg 2>/dev/null || true
    
    log_success "apt 儲存庫已清理"
}

# 卸載 Kubernetes 工具
uninstall_kubernetes_tools() {
    log_info "卸載 Kubernetes 工具..."
    
    apt-get remove -y kubelet kubeadm kubectl 2>/dev/null || true
    apt-mark unhold kubelet kubeadm kubectl 2>/dev/null || true
    
    log_success "Kubernetes 工具已卸載"
}

# 卸載 Containerd
uninstall_containerd() {
    log_info "卸載 Containerd..."
    
    apt-get remove -y containerd 2>/dev/null || true
    
    log_success "Containerd 已卸載"
}

# 卸載 Docker
uninstall_docker() {
    log_info "卸載 Docker..."
    
    apt-get remove -y docker-ce docker-ce-cli docker-buildx-plugin docker-compose-plugin containerd.io 2>/dev/null || true
    
    log_success "Docker 已卸載"
}

# 卸載 cri-dockerd
uninstall_cri_dockerd() {
    log_info "卸載 cri-dockerd..."
    
    apt-get remove -y cri-dockerd 2>/dev/null || true
    
    log_success "cri-dockerd 已卸載"
}

# 卸載 OpenvSwitch
uninstall_openvswitch() {
    log_info "卸載 OpenvSwitch..."
    
    apt-get remove -y openvswitch-switch 2>/dev/null || true
    
    log_success "OpenvSwitch 已卸載"
}

# 重新啟用 Swap
enable_swap() {
    log_info "重新啟用 Swap..."
    
    sed -i '/ swap / s/^#//' /etc/fstab 2>/dev/null || true
    swapon -a 2>/dev/null || true
    
    log_success "Swap 已重新啟用"
}

# 清理儲存目錄
cleanup_storage() {
    log_info "清理儲存目錄..."
    
    rm -rf /mnt/kube5gnfvo 2>/dev/null || true
    rm -rf /mnt/kube5gnfvo-mysql 2>/dev/null || true
    
    log_success "儲存目錄已清理"
}

# 主函數
main() {
    echo ""
    echo "╔════════════════════════════════════════════════════════════════╗"
    echo "║           Kubernetes 完全清理腳本                              ║"
    echo "║           此腳本將完全移除 Kubernetes 環境                     ║"
    echo "╚════════════════════════════════════════════════════════════════╝"
    echo ""
    
    # 檢查 root 權限
    check_root
    
    # 確認操作
    confirm_cleanup
    
    # 執行清理
    log_info "開始清理 Kubernetes..."
    echo ""
    
    reset_kubeadm
    stop_kubelet
    stop_cri_dockerd
    stop_docker
    stop_containerd
    cleanup_kubernetes_dirs
    cleanup_cri_dockerd_dirs
    cleanup_docker_dirs
    cleanup_containerd_dirs
    cleanup_cni
    cleanup_network_interfaces
    cleanup_iptables
    cleanup_sysctl
    cleanup_apt_repos
    uninstall_kubernetes_tools
    uninstall_cri_dockerd
    uninstall_docker
    uninstall_containerd
    uninstall_openvswitch
    enable_swap
    cleanup_storage
    
    echo ""
    echo "╔════════════════════════════════════════════════════════════════╗"
    echo "║     Kubernetes 清理完成！                                      ║"
    echo "║     系統已恢復到初始狀態                                       ║"
    echo "║     可以重新運行部署腳本：                                     ║"
    echo "║     sudo bash chocolee_deploy/scripts/1-setup-environment-v3.sh║"
    echo "╚════════════════════════════════════════════════════════════════╝"
    echo ""
}

# 運行主函數
main "$@"
