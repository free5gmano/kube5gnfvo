#!/bin/bash

################################################################################
# Kube5GNfvo 環境部署腳本 (v3 - 支持自訂 K8s 版本)
# 功能：從零開始部署 Kubernetes 環境和所有必要的外掛
# 改進：支持自訂 Kubernetes 版本，合併 kubectl/kubeadm/kubelet 安裝
################################################################################

set -e

# 顏色定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 預設 Kubernetes 版本
K8S_VERSION="${K8S_VERSION:-1.32.0}"

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

# 檢查命令是否存在
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# 檢查是否為 root
check_root() {
    if [ "$EUID" -ne 0 ]; then
        log_error "此腳本需要 root 權限，請使用 sudo 運行"
        exit 1
    fi
}

# 顯示使用說明
show_usage() {
    echo "使用方法: sudo bash $0 [選項]"
    echo ""
    echo "選項:"
    echo "  --k8s-version VERSION    指定 Kubernetes 版本（預設: 1.32.0）"
    echo "  --help                   顯示此幫助信息"
    echo ""
    echo "示例:"
    echo "  sudo bash $0                              # 使用預設版本 1.32.0"
    echo "  sudo bash $0 --k8s-version 1.31.0        # 使用版本 1.31.0"
    echo "  sudo bash $0 --k8s-version 1.30.0        # 使用版本 1.30.0"
    echo ""
    echo "支持的版本: 1.28.0, 1.29.0, 1.30.0, 1.31.0, 1.32.0 等"
}

# 解析命令行參數
parse_arguments() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            --k8s-version)
                K8S_VERSION="$2"
                shift 2
                ;;
            --help)
                show_usage
                exit 0
                ;;
            *)
                log_error "未知的選項: $1"
                show_usage
                exit 1
                ;;
        esac
    done
}

# 檢查系統要求
check_system_requirements() {
    log_info "檢查系統要求..."
    
    # 檢查 CPU 核心數
    CPU_CORES=$(nproc)
    if [ "$CPU_CORES" -lt 4 ]; then
        log_warning "CPU 核心數少於 4 個（當前: $CPU_CORES），建議至少 4 個"
    else
        log_success "CPU 核心數: $CPU_CORES"
    fi
    
    # 檢查內存
    MEMORY_MB=$(free -m | awk 'NR==2{print $2}')
    if [ "$MEMORY_MB" -lt 8192 ]; then
        log_warning "內存少於 8GB（當前: ${MEMORY_MB}MB），建議至少 8GB"
    else
        log_success "內存: ${MEMORY_MB}MB"
    fi
    
    # 檢查磁碟空間
    DISK_GB=$(df / | awk 'NR==2{print $4/1024/1024}' | cut -d. -f1)
    if [ "$DISK_GB" -lt 50 ]; then
        log_warning "磁碟空間少於 50GB（當前: ${DISK_GB}GB），建議至少 50GB"
    else
        log_success "磁碟空間: ${DISK_GB}GB"
    fi
}

# 安裝基礎工具
# install_basic_tools() {
#     log_info "安裝基礎工具..."
    
#     apt-get update
#     apt-get install -y \
#         curl \
#         wget \
#         git \
#         vim \
#         jq \
#         net-tools \
#         htop \
#         apt-transport-https \
#         ca-certificates \
#         gnupg \
#         lsb-release
    
#     log_success "基礎工具安裝完成"
# }

# 關閉 Swap
disable_swap() {
    log_info "關閉 Swap..."
    
    swapoff -a
    sed -i '/ swap / s/^\(.*\)$/#\1/g' /etc/fstab
    
    log_success "Swap 已關閉"
}

# 設定核心模組
setup_kernel_modules() {
    log_info "設定核心模組..."
    
    # 載入必要的核心模組
    cat <<'EOF' | tee /etc/modules-load.d/k8s.conf >/dev/null
overlay
br_netfilter
EOF
    
    modprobe overlay
    modprobe br_netfilter
    
    log_success "核心模組設定完成"
}

# 設定 sysctl 參數
setup_sysctl() {
    log_info "設定 sysctl 參數..."
    
    # 設定網路參數
    cat <<'EOF' | tee /etc/sysctl.d/k8s.conf >/dev/null
net.bridge.bridge-nf-call-iptables  = 1
net.bridge.bridge-nf-call-ip6tables = 1
net.ipv4.ip_forward                 = 1
EOF
    
    sysctl --system
    
    log_success "sysctl 參數設定完成"
}

# 安裝 Containerd
install_containerd() {
    log_info "安裝 Containerd..."
    
    if command_exists containerd; then
        log_success "Containerd 已安裝: $(containerd --version)"
        return
    fi
    
    # 安裝 Containerd
    apt-get update
    apt-get install -y containerd
    
    # 配置 Containerd
    mkdir -p /etc/containerd
    containerd config default | tee /etc/containerd/config.toml >/dev/null
    
    # 啟用 SystemdCgroup
    sed -i 's/SystemdCgroup = false/SystemdCgroup = true/' /etc/containerd/config.toml
    
    # 重啟 Containerd
    systemctl restart containerd
    systemctl enable containerd
    
    log_success "Containerd 安裝完成: $(containerd --version)"
}

# 安裝 Kubernetes 工具（kubectl、kubeadm、kubelet）
install_kubernetes_tools() {
    log_info "安裝 Kubernetes 工具 (版本: $K8S_VERSION)..."
    
    # 檢查是否已安裝
    if command_exists kubeadm && command_exists kubelet && command_exists kubectl; then
        INSTALLED_VERSION=$(kubeadm version -o short | cut -d'v' -f2)
        if [ "$INSTALLED_VERSION" = "$K8S_VERSION" ]; then
            log_success "Kubernetes 工具已安裝 (版本: $K8S_VERSION)"
            return
        fi
    fi
    
    # 更新apt套件並安裝使用 Kubernetesapt儲存庫所需的套件
    log_info "更新apt套件並安裝使用 Kubernetesapt儲存庫所需的套件..."
    apt-get update
    apt-get install -y apt-transport-https ca-certificates curl gpg

    # 載 Kubernetes 套件儲存庫的公共簽署金鑰
    log_info "載 Kubernetes 套件儲存庫的公共簽署金鑰..."
    curl -fsSL https://pkgs.k8s.io/core:/stable:/${K8S_VERSION}/deb/Release.key | gpg --dearmor -o /etc/apt/keyrings/kubernetes-apt-keyring.gpg
    
    # 載 Kubernetes 套件儲存庫的公共簽署金鑰
    log_info "載 Kubernetes 套件儲存庫的公共簽署金鑰..."
    echo "deb [signed-by=/etc/apt/keyrings/kubernetes-apt-keyring.gpg] https://pkgs.k8s.io/core:/stable:/${K8S_VERSION}/deb/ /" | tee /etc/apt/sources.list.d/kubernetes.list

    # 更新包列表
    apt-get update
    
    # 安裝指定版本的 Kubernetes 工具
    log_info "安裝 kubectl、kubeadm、kubelet (版本: ${K8S_VERSION})..."
    apt-get install -y \
        kubectl=${K8S_VERSION}* \
        kubeadm=${K8S_VERSION}* \
        kubelet=${K8S_VERSION}*
    
    # 鎖定版本，防止自動升級
    apt-mark hold kubelet kubeadm kubectl
    
    log_success "Kubernetes 工具安裝完成"
    log_info "  kubectl: $(kubectl version --client --short)"
    log_info "  kubeadm: $(kubeadm version -o short)"
    log_info "  kubelet: $(kubelet --version)"
}

# 初始化 Kubernetes 主節點
init_kubernetes_master() {
    log_info "初始化 Kubernetes 主節點..."
    
    # 檢查是否已初始化
    if [ -f /etc/kubernetes/admin.conf ]; then
        log_success "Kubernetes 已初始化"
        return
    fi
    
    # 初始化主節點
    log_info "執行 kubeadm init..."
    kubeadm init \
        --pod-network-cidr=10.244.0.0/16 \
        --cri-socket=unix:///run/containerd/containerd.sock \
        --kubernetes-version=v${K8S_VERSION}
    
    # 配置 kubectl
    log_info "配置 kubectl..."
    mkdir -p $HOME/.kube
    cp -i /etc/kubernetes/admin.conf $HOME/.kube/config
    chown $(id -u):$(id -g) $HOME/.kube/config
    
    log_success "Kubernetes 主節點初始化完成"
}

# 安裝網路外掛（Flannel）
install_flannel() {
    log_info "安裝 Flannel 網路外掛..."
    
    # 檢查是否已安裝
    if kubectl get daemonset -n kube-flannel flannel-ds-amd64 &>/dev/null 2>&1; then
        log_success "Flannel 已安裝"
        return
    fi
    
    # 安裝 Flannel
    kubectl apply -f https://raw.githubusercontent.com/coreos/flannel/master/Documentation/kube-flannel.yml
    
    # 等待 Flannel 啟動
    log_info "等待 Flannel 啟動..."
    sleep 10
    
    log_success "Flannel 安裝完成"
}

# 允許主節點運行 Pod
allow_master_pods() {
    log_info "配置主節點允許運行 Pod..."
    
    kubectl taint nodes --all node-role.kubernetes.io/control-plane- 2>/dev/null || true
    
    log_success "主節點配置完成"
}

# 安裝 Metrics Server
install_metrics_server() {
    log_info "安裝 Metrics Server..."
    
    # 檢查是否已安裝
    if kubectl get deployment metrics-server -n kube-system &>/dev/null 2>&1; then
        log_success "Metrics Server 已安裝"
        return
    fi
    
    # 安裝 Metrics Server
    kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml
    
    # 等待 Metrics Server 啟動
    log_info "等待 Metrics Server 啟動..."
    sleep 10
    
    log_success "Metrics Server 安裝完成"
}

# 安裝 Multus CNI
install_multus() {
    log_info "安裝 Multus CNI..."
    
    # 檢查是否已安裝
    if kubectl get daemonset -n kube-system kube-multus-ds-amd64 &>/dev/null 2>&1; then
        log_success "Multus CNI 已安裝"
        return
    fi
    
    # 安裝 Multus
    kubectl apply -f https://raw.githubusercontent.com/intel/multus-cni/master/deployments/multus-daemonset-thick.yml
    
    # 等待 Multus 啟動
    log_info "等待 Multus 啟動..."
    sleep 10
    
    log_success "Multus CNI 安裝完成"
}

# 安裝 OVS CNI
install_ovs_cni() {
    log_info "安裝 OVS CNI..."
    
    # 檢查是否已安裝
    if kubectl get daemonset -n kube-system ovs-cni-amd64 &>/dev/null 2>&1; then
        log_success "OVS CNI 已安裝"
        return
    fi
    
    # 安裝 OVS CNI
    kubectl apply -f https://raw.githubusercontent.com/kubevirt/ovs-cni/main/examples/ovs-cni.yaml
    
    # 等待 OVS CNI 啟動
    log_info "等待 OVS CNI 啟動..."
    sleep 10
    
    log_success "OVS CNI 安裝完成"
}

# 安裝 KubeVirt
install_kubevirt() {
    log_info "安裝 KubeVirt..."
    
    # 檢查是否已安裝
    if kubectl get namespace kubevirt &>/dev/null 2>&1; then
        log_success "KubeVirt 已安裝"
        return
    fi
    
    # 部署 KubeVirt Operator
    kubectl apply -f https://github.com/kubevirt/kubevirt/releases/download/v1.0.0/kubevirt-operator.yaml
    
    # 等待 Operator 啟動
    log_info "等待 KubeVirt Operator 啟動..."
    sleep 30
    
    # 部署 KubeVirt CR
    kubectl apply -f https://github.com/kubevirt/kubevirt/releases/download/v1.0.0/kubevirt-cr.yaml
    
    # 等待 KubeVirt 啟動
    log_info "等待 KubeVirt 啟動..."
    sleep 30
    
    log_success "KubeVirt 安裝完成"
}

# 驗證環境
verify_environment() {
    log_info "驗證環境..."
    
    echo ""
    echo "=========================================="
    echo "Kubernetes 環境驗證"
    echo "=========================================="
    echo ""
    
    # 檢查 Kubernetes 版本
    log_info "Kubernetes 版本:"
    kubectl version --short
    
    # 檢查節點
    echo ""
    log_info "節點狀態:"
    kubectl get nodes
    
    # 檢查系統 Pod
    echo ""
    log_info "系統 Pod:"
    kubectl get pods -n kube-system | head -15
    
    # 檢查 Metrics Server
    echo ""
    log_info "Metrics Server:"
    kubectl get deployment metrics-server -n kube-system 2>/dev/null || log_warning "Metrics Server 未安裝"
    
    # 檢查 Multus
    echo ""
    log_info "Multus CNI:"
    kubectl get daemonset -n kube-system | grep multus || log_warning "Multus 未安裝"
    
    # 檢查 OVS CNI
    echo ""
    log_info "OVS CNI:"
    kubectl get daemonset -n kube-system | grep ovs || log_warning "OVS CNI 未安裝"
    
    # 檢查 KubeVirt
    echo ""
    log_info "KubeVirt:"
    kubectl get pods -n kubevirt 2>/dev/null || log_warning "KubeVirt 未安裝"
    
    echo ""
    echo "=========================================="
    log_success "環境驗證完成"
    echo "=========================================="
}

# 建立儲存目錄
create_storage_directories() {
    log_info "建立儲存目錄..."
    
    mkdir -p /mnt/kube5gnfvo
    mkdir -p /mnt/kube5gnfvo-mysql
    chmod 777 /mnt/kube5gnfvo
    chmod 777 /mnt/kube5gnfvo-mysql
    
    log_success "儲存目錄建立完成"
}

# 主函數
main() {
    echo ""
    echo "╔════════════════════════════════════════════════════════════════╗"
    echo "║     Kube5GNfvo 環境部署腳本 (v3 - 支持自訂 K8s 版本)          ║"
    echo "║     此腳本將部署完整的 Kubernetes 環境                         ║"
    echo "╚════════════════════════════════════════════════════════════════╝"
    echo ""
    
    # 解析命令行參數
    parse_arguments "$@"
    
    # 檢查 root 權限
    check_root
    
    # 顯示配置信息
    echo "部署配置："
    echo "  Kubernetes 版本: $K8S_VERSION"
    echo "  容器運行時: Containerd"
    echo ""
    
    # 檢查系統要求
    check_system_requirements
    
    # 安裝基礎工具（已在 Kubernetes 安裝時安裝，此處跳過）
    # install_basic_tools
    
    # 關閉 Swap
    disable_swap
    
    # 設定核心模組
    setup_kernel_modules
    
    # 設定 sysctl 參數
    setup_sysctl
    
    # 安裝 Containerd
    install_containerd
    
    # 安裝 Kubernetes 工具
    install_kubernetes_tools
    
    # 初始化 Kubernetes 主節點
    init_kubernetes_master
    
    # 安裝 Flannel 網路外掛
    install_flannel
    
    # 允許主節點運行 Pod
    allow_master_pods
    
    # 安裝 Metrics Server
    install_metrics_server
    
    # 安裝 Multus CNI
    install_multus
    
    # 安裝 OVS CNI
    install_ovs_cni
    
    # 安裝 KubeVirt
    install_kubevirt
    
    # 建立儲存目錄
    create_storage_directories
    
    # 驗證環境
    verify_environment
    
    echo ""
    echo "╔════════════════════════════════════════════════════════════════╗"
    echo "║     環境部署完成！                                             ║"
    echo "║     Kubernetes 版本: $K8S_VERSION"
    echo "║     下一步：運行 2-deploy-kube5gnfvo.sh 部署應用               ║"
    echo "╚════════════════════════════════════════════════════════════════╝"
    echo ""
}

# 運行主函數
main "$@"
