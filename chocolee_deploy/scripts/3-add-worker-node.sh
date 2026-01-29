#!/bin/bash

################################################################################
# Kube5GNfvo Worker Node 加入腳本
# 功能：將新的機器加入為 Kubernetes Worker Node
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
K8S_VERSION="${K8S_VERSION:-1.32}"

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

# 顯示使用說明
show_usage() {
    echo "使用方法: bash $0 [選項]"
    echo ""
    echo "選項:"
    echo "  --master-ip IP           Master 節點的 IP 地址（必需）"
    echo "  --token TOKEN            加入令牌（可選，如果不提供會自動生成）"
    echo "  --ca-cert-hash HASH      CA 證書雜湊（可選，如果不提供會自動生成）"
    echo "  --k8s-version VERSION    指定 Kubernetes 版本（預設: 1.32）"
    echo "  --node-name NAME         節點名稱（可選，預設為主機名）"
    echo "  --help                   顯示此幫助信息"
    echo ""
    echo "範例:"
    echo "  bash $0 --master-ip 192.168.1.100"
    echo "  bash $0 --master-ip 192.168.1.100 --node-name worker-1"
}

# 解析命令行參數
parse_arguments() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            --master-ip)
                MASTER_IP="$2"
                shift 2
                ;;
            --token)
                JOIN_TOKEN="$2"
                shift 2
                ;;
            --ca-cert-hash)
                CA_CERT_HASH="$2"
                shift 2
                ;;
            --k8s-version)
                K8S_VERSION="$2"
                shift 2
                ;;
            --node-name)
                NODE_NAME="$2"
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

# 驗證必需參數
validate_parameters() {
    if [ -z "$MASTER_IP" ]; then
        log_error "必須指定 Master 節點的 IP 地址"
        show_usage
        exit 1
    fi
    
    log_info "Master IP: $MASTER_IP"
    log_info "Kubernetes 版本: $K8S_VERSION"
}

# 檢查系統要求
check_system_requirements() {
    log_info "檢查系統要求..."
    CPU_CORES=$(nproc)
    MEMORY_MB=$(free -m | awk 'NR==2{print $2}')
    DISK_GB=$(df / | awk 'NR==2{print $4/1024/1024}' | cut -d. -f1)

    [ "$CPU_CORES" -lt 2 ] && log_warning "CPU 少於 2 核" || log_success "CPU: $CPU_CORES 核"
    [ "$MEMORY_MB" -lt 4096 ] && log_warning "內存少於 4GB" || log_success "內存: ${MEMORY_MB}MB"
    [ "$DISK_GB" -lt 20 ] && log_warning "磁碟空間少於 20GB" || log_success "磁碟: ${DISK_GB}GB"
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



# 加入 Worker Node
join_worker_node() {
    log_info "加入 Worker Node 到叢集..."
    
    if [ -z "$JOIN_TOKEN" ] || [ -z "$CA_CERT_HASH" ]; then
        log_error "缺少加入令牌或 CA 證書雜湊"
        exit 1
    fi
    
    log_info "執行 kubeadm join 命令..."
    sudo kubeadm join $MASTER_IP:6443 \
        --token $JOIN_TOKEN \
        --discovery-token-ca-cert-hash $CA_CERT_HASH \
        --cri-socket=unix:///run/containerd/containerd.sock \
        --node-name $NODE_NAME
    log_success "Worker Node 已加入叢集"
}

# 建立儲存目錄
create_storage_directories() {
    log_info "建立儲存目錄..."
    sudo mkdir -p /mnt/kube5gnfvo
    sudo chmod 777 /mnt/kube5gnfvo
    log_success "儲存目錄建立完成"
}

# 驗證加入
verify_join() {
    log_info "驗證 Worker Node 加入狀態..."
    sleep 5
    
    # 檢查 kubelet 狀態
    systemctl status --no-pager kubelet || true
}

# 主函數
main() {
    echo ""
    echo "╔════════════════════════════════════════════════════════════════╗"
    echo "║     Kube5GNfvo Worker Node 加入腳本                             ║"
    echo "╚════════════════════════════════════════════════════════════════╝"
    echo ""
    
    parse_arguments "$@"
    validate_parameters
    
    check_system_requirements
    disable_swap
    setup_kernel_modules
    setup_sysctl
    install_docker
    install_kubernetes_tools
    install_cni_plugins
    install_openvswitch
    
    join_worker_node
    
    create_storage_directories
    verify_join
    
    log_success "Worker Node 加入流程完成！"
    
    echo ""
    echo "╔════════════════════════════════════════════════════════════════╗"
    echo "║     Worker Node 已加入叢集！                                    ║"
    echo "║     請在 Master 節點執行以下命令驗證：                           ║"
    echo "║     kubectl get nodes                                          ║"
    echo "╚════════════════════════════════════════════════════════════════╝"
    echo ""
}

main "$@"
