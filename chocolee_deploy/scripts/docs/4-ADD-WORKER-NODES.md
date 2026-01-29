# 添加 Worker Node 到 Kubernetes 叢集

本文檔說明如何將新的機器添加為 Worker Node 到現有的 Kube5GNfvo Kubernetes 叢集。

## 前置要求

- 已有一個運行中的 Master Node（已執行 `1-setup-environment-v3.sh`）
- 新機器已安裝 Ubuntu 20.04 或更高版本
- 新機器與 Master Node 網路連通
- 新機器有 sudo 權限

## 步驟 1：在 Master 節點上生成加入令牌

在 Master 節點上執行以下命令獲取加入令牌：

```bash
cd /home/ubuntu/kube5gnfvo/chocolee_deploy/scripts
bash get-join-token.sh
```

這個腳本會輸出類似以下的加入命令：

```
kubeadm join 192.168.1.100:6443 --token abc123.xyz789 --discovery-token-ca-cert-hash sha256:abcdef123456...
```

記下以下信息：
- **Master IP**: 192.168.1.100
- **Token**: abc123.xyz789
- **CA Cert Hash**: sha256:abcdef123456...

## 步驟 2：在 Worker Node 上執行加入腳本

將 `3-add-worker-node.sh` 複製到新機器，然後執行：

### 方式 1：使用 Master IP（自動生成令牌）

```bash
bash 3-add-worker-node.sh --master-ip 192.168.1.100
```

**注意**：此方式需要新機器能夠連接到 Master Node 的 API Server。

### 方式 2：使用完整的加入參數（推薦）

```bash
bash 3-add-worker-node.sh \
  --master-ip 192.168.1.100 \
  --token abc123.xyz789 \
  --ca-cert-hash sha256:abcdef123456...
```

### 方式 3：指定節點名稱

```bash
bash 3-add-worker-node.sh \
  --master-ip 192.168.1.100 \
  --token abc123.xyz789 \
  --ca-cert-hash sha256:abcdef123456... \
  --node-name worker-1
```

### 方式 4：指定 Kubernetes 版本

```bash
bash 3-add-worker-node.sh \
  --master-ip 192.168.1.100 \
  --token abc123.xyz789 \
  --ca-cert-hash sha256:abcdef123456... \
  --k8s-version 1.32
```

## 步驟 3：驗證 Worker Node 加入

在 Master 節點上執行以下命令驗證 Worker Node 是否成功加入：

```bash
kubectl get nodes
```

輸出應該類似：

```
NAME      STATUS   ROLES           AGE   VERSION
master    Ready    control-plane   2d    v1.32.0
worker-1  Ready    <none>          5m    v1.32.0
```

查看詳細信息：

```bash
kubectl get nodes -o wide
```

## 故障排除

### 1. Worker Node 狀態為 NotReady

檢查 kubelet 日誌：

```bash
sudo journalctl -u kubelet -n 50 -f
```

常見原因：
- CNI 插件未正確安裝
- 網路連接問題
- 資源不足

### 2. 加入命令失敗

檢查以下項目：

```bash
# 檢查 kubelet 狀態
sudo systemctl status kubelet

# 檢查 Docker 狀態
sudo systemctl status docker

# 檢查 containerd 狀態
sudo systemctl status containerd

# 查看 kubelet 日誌
sudo journalctl -u kubelet -n 100
```

### 3. 令牌過期

令牌默認有效期為 24 小時。如果過期，需要在 Master 節點重新生成：

```bash
bash get-join-token.sh
```

### 4. 網路連接問題

確保 Worker Node 能夠連接到 Master Node：

```bash
# 測試連接
ping <master-ip>

# 測試 API Server 端口
nc -zv <master-ip> 6443
```

## 添加多個 Worker Node

重複步驟 1-3 即可添加多個 Worker Node。每個 Worker Node 都需要執行一次加入腳本。

## 移除 Worker Node

如果需要移除 Worker Node，在 Master 節點執行：

```bash
# 驅逐 Pod
kubectl drain <node-name> --ignore-daemonsets --delete-emptydir-data

# 刪除節點
kubectl delete node <node-name>
```

在 Worker Node 上執行：

```bash
# 重置 kubeadm
sudo kubeadm reset -f
```

## 常用命令

```bash
# 查看所有節點
kubectl get nodes

# 查看節點詳細信息
kubectl get nodes -o wide

# 查看節點資源使用情況
kubectl top nodes

# 查看節點標籤
kubectl get nodes --show-labels

# 為節點添加標籤
kubectl label nodes <node-name> <key>=<value>

# 查看節點上的 Pod
kubectl get pods -o wide --all-namespaces | grep <node-name>

# 查看節點事件
kubectl describe node <node-name>
```

## 配置 Worker Node 標籤

為了更好地管理 Pod 調度，可以為 Worker Node 添加標籤：

```bash
# 標記為計算節點
kubectl label nodes worker-1 node-type=compute

# 標記為存儲節點
kubectl label nodes worker-2 node-type=storage

# 標記為邊緣節點
kubectl label nodes worker-3 node-type=edge
```

然後在 Pod 部署時使用 nodeSelector 或 affinity 規則進行調度。

## 性能優化建議

1. **禁用 Swap**：腳本已自動執行
2. **調整 kubelet 參數**：根據節點資源調整
3. **配置 Pod 優先級**：為關鍵 Pod 設置優先級
4. **使用 DaemonSet**：在所有節點上運行必要的服務

## 相關文檔

- [1-ENVIRONMENT_SETUP.md](1-ENVIRONMENT_SETUP.md) - 環境設置說明
- [2-KUBE5GNFVO_DEPLOYMENT.md](2-KUBE5GNFVO_DEPLOYMENT.md) - 應用部署說明
- [3-API_TESTING.md](3-API_TESTING.md) - API 測試說明
