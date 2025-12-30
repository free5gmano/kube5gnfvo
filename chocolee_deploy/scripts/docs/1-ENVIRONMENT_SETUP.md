# 1. 環境部署指南

本文檔說明如何從零開始部署 Kube5GNfvo 的運行環境。

## 📋 前置條件

### 系統要求
- Linux 系統（Ubuntu 20.04 LTS 或更高版本）
- 至少 4 核 CPU
- 至少 8GB RAM
- 至少 50GB 磁碟空間

### 必要工具
- `curl` - 用於下載和 API 測試
- `git` - 版本控制
- `docker` - 容器運行時（可選，如果使用本地開發）

---

## 🚀 第一步：安裝 Kubernetes

### 1.1 安裝 kubectl

```bash
# 下載最新版本的 kubectl
curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"

# 安裝 kubectl
sudo install -o root -g root -m 0755 kubectl /usr/local/bin/kubectl

# 驗證安裝
kubectl version --client
```

### 1.2 安裝 Kubernetes 叢集

#### 選項 A：使用 kubeadm（推薦用於生產環境）

```bash
# 1. 安裝容器運行時（Docker）
sudo apt-get update
sudo apt-get install -y docker.io
sudo systemctl start docker
sudo systemctl enable docker

# 2. 安裝 kubeadm、kubelet 和 kubectl
sudo apt-get update
sudo apt-get install -y apt-transport-https ca-certificates curl
sudo curl -fsSLo /usr/share/keyrings/kubernetes-archive-keyring.gpg https://packages.cloud.google.com/apt/doc/apt-key.gpg
echo "deb [signed-by=/usr/share/keyrings/kubernetes-archive-keyring.gpg] https://apt.kubernetes.io/ kubernetes-xenial main" | sudo tee /etc/apt/sources.list.d/kubernetes.list
sudo apt-get update
sudo apt-get install -y kubelet=1.32.0-00 kubeadm=1.32.0-00 kubectl=1.32.0-00
sudo apt-mark hold kubelet kubeadm kubectl

# 3. 初始化 Kubernetes 主節點
sudo kubeadm init --pod-network-cidr=10.244.0.0/16

# 4. 配置 kubectl
mkdir -p $HOME/.kube
sudo cp -i /etc/kubernetes/admin.conf $HOME/.kube/config
sudo chown $(id -u):$(id -g) $HOME/.kube/config

# 5. 安裝網路外掛（Flannel）
kubectl apply -f https://raw.githubusercontent.com/coreos/flannel/master/Documentation/kube-flannel.yml

# 6. 允許主節點運行 Pod（開發環境）
kubectl taint nodes --all node-role.kubernetes.io/control-plane-
```

#### 選項 B：使用 Minikube（推薦用於開發環境）

```bash
# 1. 下載 Minikube
curl -LO https://github.com/kubernetes/minikube/releases/latest/download/minikube-linux-amd64
sudo install minikube-linux-amd64 /usr/local/bin/minikube

# 2. 啟動 Minikube
minikube start --cpus=4 --memory=8192 --disk-size=50g

# 3. 驗證安裝
kubectl cluster-info
```

### 1.3 驗證 Kubernetes 安裝

```bash
# 檢查節點狀態
kubectl get nodes

# 檢查系統 Pod
kubectl get pods -n kube-system

# 預期輸出：所有節點應為 Ready 狀態
```

---

## 🔧 第二步：安裝必要的 Kubernetes 外掛

### 2.1 安裝 Metrics Server（用於資源監控）

```bash
# 部署 Metrics Server
kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml

# 驗證安裝
kubectl get deployment metrics-server -n kube-system
```

### 2.2 安裝 Multus CNI（用於多網路支援）

```bash
# 部署 Multus
kubectl apply -f https://raw.githubusercontent.com/intel/multus-cni/master/deployments/multus-daemonset-thick.yml

# 驗證安裝
kubectl get daemonset -n kube-system | grep multus
```

### 2.3 安裝 OVS CNI（用於 OpenFlow 網路）

```bash
# 部署 OVS CNI
kubectl apply -f https://raw.githubusercontent.com/kubevirt/ovs-cni/main/examples/ovs-cni.yaml

# 驗證安裝
kubectl get daemonset -n kube-system | grep ovs
```

### 2.4 安裝 KubeVirt（用於虛擬機支援）

```bash
# 部署 KubeVirt Operator
kubectl apply -f https://github.com/kubevirt/kubevirt/releases/download/v1.0.0/kubevirt-operator.yaml

# 等待 Operator 啟動
kubectl wait --for=condition=Available --timeout=300s deployment/virt-operator -n kubevirt

# 部署 KubeVirt CR
kubectl apply -f https://github.com/kubevirt/kubevirt/releases/download/v1.0.0/kubevirt-cr.yaml

# 驗證安裝
kubectl get pods -n kubevirt
```

---

## 📦 第三步：驗證環境

### 3.1 檢查所有必要元件

```bash
#!/bin/bash

echo "=========================================="
echo "Kubernetes 環境檢查"
echo "=========================================="
echo ""

# 檢查 Kubernetes 版本
echo "✓ Kubernetes 版本:"
kubectl version --short

# 檢查節點
echo ""
echo "✓ 節點狀態:"
kubectl get nodes

# 檢查系統 Pod
echo ""
echo "✓ 系統 Pod:"
kubectl get pods -n kube-system | head -10

# 檢查 Metrics Server
echo ""
echo "✓ Metrics Server:"
kubectl get deployment metrics-server -n kube-system

# 檢查 Multus
echo ""
echo "✓ Multus CNI:"
kubectl get daemonset -n kube-system | grep multus

# 檢查 OVS CNI
echo ""
echo "✓ OVS CNI:"
kubectl get daemonset -n kube-system | grep ovs

# 檢查 KubeVirt
echo ""
echo "✓ KubeVirt:"
kubectl get pods -n kubevirt

echo ""
echo "=========================================="
echo "環境檢查完成"
echo "=========================================="
```

### 3.2 運行檢查

```bash
# 保存上面的腳本為 check-environment.sh
chmod +x check-environment.sh
./check-environment.sh
```

---

## 🧹 清理環境（如需重新開始）

```bash
# 刪除所有 Kube5GNfvo 資源
kubectl delete namespace kube5gnfvo

# 刪除 PersistentVolume
kubectl delete pv kube5gnfvo-pv 2>/dev/null

# 刪除本地資料
sudo rm -rf /mnt/kube5gnfvo
sudo rm -rf /mnt/kube5gnfvo-mysql

# 如果使用 Minikube，可以完全重置
minikube delete
```

---

## 📝 環境變數配置

建立 `.env` 檔案用於後續部署：

```bash
# Kubernetes 配置
KUBERNETES_VERSION=1.32.0
NAMESPACE=kube5gnfvo

# MySQL 配置
MYSQL_ROOT_PASSWORD=password
MYSQL_DATABASE=kube5gnfvo
MYSQL_USER=root
MYSQL_PORT=3306

# 應用配置
APP_PORT=8000
APP_NODE_PORT=30888
APP_REPLICAS=1

# 儲存配置
STORAGE_SIZE=20Gi
STORAGE_PATH=/mnt/kube5gnfvo
```

---

## ✅ 環境部署檢查清單

- [ ] Kubernetes 叢集已安裝並運行
- [ ] kubectl 已配置並可訪問叢集
- [ ] 所有節點狀態為 Ready
- [ ] Metrics Server 已部署
- [ ] Multus CNI 已部署
- [ ] OVS CNI 已部署
- [ ] KubeVirt 已部署
- [ ] 所有系統 Pod 運行正常
- [ ] 儲存路徑已建立（`/mnt/kube5gnfvo`）
- [ ] `.env` 檔案已建立

---

## 🆘 故障排除

### 問題：節點狀態為 NotReady

```bash
# 檢查節點詳細信息
kubectl describe node <node-name>

# 檢查 kubelet 日誌
sudo journalctl -u kubelet -n 50
```

### 問題：Pod 無法啟動

```bash
# 檢查 Pod 詳細信息
kubectl describe pod <pod-name> -n <namespace>

# 查看 Pod 日誌
kubectl logs <pod-name> -n <namespace>
```

### 問題：網路連接問題

```bash
# 測試 Pod 間通信
kubectl run -it --rm debug --image=busybox --restart=Never -- sh

# 在 Pod 中測試 DNS
nslookup kubernetes.default
```

---

**下一步：** 環境部署完成後，請參考 `2-KUBE5GNFVO_DEPLOYMENT.md` 部署 Kube5GNfvo 應用。
