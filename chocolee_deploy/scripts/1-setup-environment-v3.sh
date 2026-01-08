#!/bin/bash

################################################################################
# Kube5GNfvo 環境部署腳本 (v3.1 - 直接使用 sudo 版本)
# 功能：從零開始部署 Kubernetes 環境和所有必要的外掛
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

# 檢查是否為 root (K8s 不建議直接以 root 執行，但需要有 sudo 權限)
check_root() {
    if [ "$EUID" -eq 0 ]; then
        log_warning "不建議直接以 root 身份運行此腳本"
        log_info "請以普通用戶身份運行，腳本會在需要時自動呼叫 sudo"
        exit 1
    fi
}

# 顯示使用說明
show_usage() {
    echo "使用方法: bash $0 [選項]"
    echo ""
    echo "選項:"
    echo "  --k8s-version VERSION    指定 Kubernetes 版本（預設: 1.32.0）"
    echo "  --help                   顯示此幫助信息"
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
    CPU_CORES=$(nproc)
    MEMORY_MB=$(free -m | awk 'NR==2{print $2}')
    DISK_GB=$(df / | awk 'NR==2{print $4/1024/1024}' | cut -d. -f1)

    [ "$CPU_CORES" -lt 4 ] && log_warning "CPU 少於 4 核" || log_success "CPU: $CPU_CORES 核"
    [ "$MEMORY_MB" -lt 8192 ] && log_warning "內存少於 8GB" || log_success "內存: ${MEMORY_MB}MB"
    [ "$DISK_GB" -lt 50 ] && log_warning "磁碟空間少於 50GB" || log_success "磁碟: ${DISK_GB}GB"
}

# 關閉 Swap
disable_swap() {
    log_info "關閉 Swap..."
    sudo swapoff -a
    sudo sed -i '/ swap / s/^\(.*\)$/#\1/g' /etc/fstab
    log_success "Swap 已關閉"
}

# 設定核心模組
setup_kernel_modules() {
    log_info "設定核心模組..."
    sudo bash -c 'cat > /etc/modules-load.d/k8s.conf <<EOF
overlay
br_netfilter
EOF'
    sudo modprobe overlay
    sudo modprobe br_netfilter
    log_success "核心模組設定完成"
}

# 設定 sysctl 參數
setup_sysctl() {
    log_info "設定 sysctl 參數..."
    sudo bash -c 'cat > /etc/sysctl.d/k8s.conf <<EOF
net.bridge.bridge-nf-call-iptables  = 1
net.bridge.bridge-nf-call-ip6tables = 1
net.ipv4.ip_forward                 = 1
EOF'
    sudo sysctl --system
    log_success "sysctl 參數設定完成"
}

# 安裝 Docker
install_docker() {
    log_info "安裝 Docker..."
    if command_exists docker; then
        log_success "Docker 已安裝"
        return
    fi
    
    log_info "準備環境..."
    sudo NEEDRESTART_MODE=a DEBIAN_FRONTEND=noninteractive apt-get update
    sudo NEEDRESTART_MODE=a DEBIAN_FRONTEND=noninteractive apt-get install -y ca-certificates curl gnupg lsb-release
    
    log_info "安裝 Docker..."
    sudo mkdir -m 755 -p /etc/apt/keyrings
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker.gpg
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
    
    sudo NEEDRESTART_MODE=a DEBIAN_FRONTEND=noninteractive apt-get update
    sudo NEEDRESTART_MODE=a DEBIAN_FRONTEND=noninteractive apt-get install -y containerd.io docker-ce docker-ce-cli docker-buildx-plugin docker-compose-plugin
    
    sudo groupadd docker 2>/dev/null || true
    sudo usermod -aG docker $USER
    
    log_info "配置 Containerd..."
    sudo mkdir -p /etc/containerd
    containerd config default | sudo tee /etc/containerd/config.toml > /dev/null
    sudo sed -i 's/SystemdCgroup = false/SystemdCgroup = true/g' /etc/containerd/config.toml
    
    log_info "配置 Docker daemon..."
    cat <<EOF | sudo tee /etc/docker/daemon.json > /dev/null
{
  "exec-opts": ["native.cgroupdriver=systemd"],
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "100m"
  },
  "storage-driver": "overlay2"
}
EOF
    
    sudo systemctl daemon-reload
    sudo systemctl enable --now containerd
    sudo systemctl enable --now docker
    
    systemctl status --no-pager containerd
    systemctl status --no-pager docker
    
    log_success "Docker 安裝完成"
}


# 安裝 Kubernetes 工具
install_kubernetes_tools() {
    log_info "安裝 Kubernetes 工具 (版本: $K8S_VERSION)..."
    sudo NEEDRESTART_MODE=a DEBIAN_FRONTEND=noninteractive apt-get update
    sudo NEEDRESTART_MODE=a DEBIAN_FRONTEND=noninteractive apt-get install -y apt-transport-https ca-certificates curl gpg
    sudo mkdir -p /etc/apt/keyrings
    
    if curl -fsSL "https://pkgs.k8s.io/core:/stable:/v${K8S_VERSION}/deb/Release.key" | sudo gpg --dearmor --batch --yes -o /etc/apt/keyrings/kubernetes-apt-keyring.gpg; then
        sudo bash -c "echo 'deb [signed-by=/etc/apt/keyrings/kubernetes-apt-keyring.gpg] https://pkgs.k8s.io/core:/stable:/v${K8S_VERSION}/deb/ /' | tee /etc/apt/sources.list.d/kubernetes.list"
    else
        log_error "無法下載 Kubernetes 金鑰"
        exit 1
    fi

    sudo apt-get update
    sudo NEEDRESTART_MODE=a DEBIAN_FRONTEND=noninteractive apt-get install -y kubectl=${K8S_VERSION}* kubeadm=${K8S_VERSION}* kubelet=${K8S_VERSION}*
    sudo apt-mark hold kubelet kubeadm kubectl
    log_success "Kubernetes 工具安裝完成"
}

# 初始化 Kubernetes 主節點
init_kubernetes_master() {
    log_info "初始化 Kubernetes 主節點..."
    if [ -f /etc/kubernetes/admin.conf ]; then
        log_success "Kubernetes 已初始化"
        return
    fi

    KUBE_VERSION="${K8S_VERSION}"
    [[ ! "$KUBE_VERSION" =~ \.[0-9]+\.[0-9]+$ ]] && KUBE_VERSION="${KUBE_VERSION}.0"

    sudo kubeadm init \
        --pod-network-cidr=10.244.0.0/16 \
        --cri-socket=unix:///run/containerd/containerd.sock \
        --kubernetes-version=v${KUBE_VERSION}

    # 配置 kubectl
    mkdir -p $HOME/.kube
    sudo cp -f /etc/kubernetes/admin.conf $HOME/.kube/config
    sudo chown $(id -u):$(id -g) $HOME/.kube/config

    log_info "等待 API server 啟動..."
    for i in {1..30}; do
        kubectl cluster-info &>/dev/null && break || sleep 2
    done
    
    # 配置 kubeconfig 跳過 TLS 驗證
    log_info "配置 kubeconfig..."
    kubectl config set-cluster kubernetes=true
    
    log_success "Kubernetes 初始化完成"
}

# 安裝 CNI 插件
install_cni_plugins() {
    log_info "安裝 CNI 插件..."
    if [ ! -f /opt/cni/bin/loopback ]; then
        sudo mkdir -p /opt/cni/bin
        wget -q https://github.com/containernetworking/plugins/releases/download/v1.4.0/cni-plugins-linux-amd64-v1.4.0.tgz -O /tmp/cni-plugins.tgz
        sudo tar -xzf /tmp/cni-plugins.tgz -C /opt/cni/bin/
        rm /tmp/cni-plugins.tgz
        log_success "CNI 插件安裝完成"
    else
        log_success "CNI 插件已存在"
    fi
}

# 安裝網路外掛（Flannel）
install_flannel() {
    log_info "安裝 Flannel..."
    kubectl apply -f https://raw.githubusercontent.com/coreos/flannel/master/Documentation/kube-flannel.yml
    sleep 5
}

# 允許主節點運行 Pod
allow_master_pods() {
    log_info "移除 Master Taint..."
    kubectl taint nodes --all node-role.kubernetes.io/control-plane- 2>/dev/null || true
}

# 安裝 Metrics Server
install_metrics_server() {
    log_info "安裝 Metrics Server..."
    kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml
    sleep 5
    
    # 修復 Metrics Server TLS 證書驗證問題
    log_info "修復 Metrics Server TLS 配置..."
    kubectl patch deployment metrics-server -n kube-system --type='json' -p='[{"op": "add", "path": "/spec/template/spec/containers/0/args/-", "value":"--kubelet-insecure-tls"}]' 2>/dev/null || true
    sleep 5
}

# 安裝 OpenvSwitch
install_openvswitch() {
    log_info "安裝 OpenvSwitch..."
    if command_exists ovs-vsctl; then
        log_success "OpenvSwitch 已存在"
        return
    fi
    sudo NEEDRESTART_MODE=a DEBIAN_FRONTEND=noninteractive apt-get update
    sudo NEEDRESTART_MODE=a DEBIAN_FRONTEND=noninteractive apt-get install -y openvswitch-switch
    sudo ovs-vsctl add-br br1 2>/dev/null || true
    sudo systemctl enable openvswitch-switch
    sudo systemctl restart openvswitch-switch
}

# 安裝 Multus CNI
install_multus() {
    log_info "安裝 Multus CNI..."
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    MULTUS_FILE="$SCRIPT_DIR/../../chocolee_deploy/kubernetes/multus-daemonset.yml"
    
    if [ -f "$MULTUS_FILE" ]; then
        kubectl apply -f "$MULTUS_FILE"
    else
        log_warning "找不到 Multus 配置文件，跳過"
    fi
}

# 安裝 OVS CNI
install_ovs_cni() {
    log_info "安裝 OVS CNI..."
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    OVS_CNI_FILE="$SCRIPT_DIR/../../chocolee_deploy/kubernetes/ovs-cni.yaml"
    OVS_NET_FILE="$SCRIPT_DIR/../../chocolee_deploy/kubernetes/ovs-net-crd.yaml"
    
    if [ -f "$OVS_CNI_FILE" ]; then
        kubectl apply -f "$OVS_CNI_FILE"
        [ -f "$OVS_NET_FILE" ] && kubectl apply -f "$OVS_NET_FILE"
    fi
}

# 安裝 KubeVirt
install_kubevirt() {
    log_info "安裝 KubeVirt..."
    if kubectl get namespace kubevirt &>/dev/null; then
        log_success "KubeVirt 已存在"
        return
    fi
    kubectl apply -f https://github.com/kubevirt/kubevirt/releases/download/v1.0.0/kubevirt-operator.yaml
    sleep 5
    kubectl apply -f https://github.com/kubevirt/kubevirt/releases/download/v1.0.0/kubevirt-cr.yaml
}

# 安裝 etcd 集群
install_etcd() {
    log_info "安裝 etcd 集群..."
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    ETCD_RBAC_FILE="$SCRIPT_DIR/../../chocolee_deploy/kubernetes/etcd-operator-rbac.yaml"
    ETCD_DEPLOY_FILE="$SCRIPT_DIR/../../chocolee_deploy/kubernetes/etcd-operator-deployment.yaml"
    
    if [ ! -f "$ETCD_RBAC_FILE" ] || [ ! -f "$ETCD_DEPLOY_FILE" ]; then
        log_error "找不到 etcd 配置文件"
        return 1
    fi
    
    log_info "應用 etcd RBAC 配置..."
    kubectl apply -f "$ETCD_RBAC_FILE"
    
    log_info "應用 etcd Deployment..."
    kubectl apply -f "$ETCD_DEPLOY_FILE"
    
    log_info "等待 etcd Pod 啟動..."
    for i in {1..60}; do
        if kubectl get pod -l app=etcd -o jsonpath='{.items[0].status.phase}' 2>/dev/null | grep -q "Running"; then
            log_success "etcd 已啟動"
            sleep 5
            return 0
        fi
        sleep 2
    done
    
    log_warning "etcd 啟動超時，請手動檢查"
}

# 建立儲存目錄
create_storage_directories() {
    log_info "建立儲存目錄..."
    sudo mkdir -p /mnt/kube5gnfvo /mnt/kube5gnfvo-mysql
    sudo chmod 777 /mnt/kube5gnfvo /mnt/kube5gnfvo-mysql
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

# 驗證環境
verify_environment() {
    log_info "驗證環境狀態..."
    kubectl get nodes
    kubectl get pods -A | head -n 10
}

# 主函數
main() {
    parse_arguments "$@"
    check_root
    check_system_requirements
    
    disable_swap
    setup_kernel_modules
    setup_sysctl
    install_docker
    install_kubernetes_tools
    init_kubernetes_master
    
    install_cni_plugins
    install_flannel
    allow_master_pods
    install_metrics_server
    install_openvswitch
    install_multus
    install_ovs_cni
    install_kubevirt
    install_etcd
    
    create_storage_directories
    fix_etcd_certificate_permissions
    verify_environment
    
    log_success "Kube5GNfvo 環境基礎部署完成！"
}

main "$@"