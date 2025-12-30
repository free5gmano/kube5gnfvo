# Kube5GNfvo 完整部署測試指南

## 環境檢查清單

### 1. 系統環境
```bash
# 檢查 Python
python3 --version  # 應該是 3.8+

# 檢查 Docker
docker --version

# 檢查 Kubernetes
kubectl version --client
kubectl cluster-info
```

### 2. 依賴套件檢查
```bash
# 檢查 Django 和相關套件
pip3 list | grep -E "Django|mysqlclient|kubernetes"

# 應該看到:
# Django==4.2.8
# mysqlclient==2.2.0
# kubernetes==32.0.0
```

### 3. Django 設定檢查
```bash
# 檢查 Django 設定
python3 manage.py check

# 應該看到: System check identified no issues (0 silenced).
```

---

## 部署步驟

### 步驟 1: 建立命名空間和 MySQL 容器

```bash
# 部署 MySQL
kubectl apply -f kubernetes/mysql/kube5gnfvo-mysql-simple.yaml

# 檢查部署狀態
kubectl get pods -n kube5gnfvo
kubectl get svc -n kube5gnfvo

# 等待 MySQL Pod 變成 Running 狀態
kubectl wait --for=condition=ready pod -l app=kube5gnfvo-mysql -n kube5gnfvo --timeout=300s
```

### 步驟 2: 驗證 MySQL 連接

```bash
# 進入 MySQL Pod
kubectl exec -it -n kube5gnfvo $(kubectl get pod -n kube5gnfvo -l app=kube5gnfvo-mysql -o jsonpath='{.items[0].metadata.name}') -- bash

# 在 Pod 內執行
mysql -u root -ppassword -e "SHOW DATABASES;"

# 應該看到 kube5gnfvo 和 os_ma_nfvo 資料庫
```

### 步驟 3: 部署 kube5gnfvo 應用

```bash
# 部署應用
kubectl apply -f kubernetes/app/kube5gnfvo-app-deploy.yaml

# 檢查部署狀態
kubectl get pods -n kube5gnfvo
kubectl get svc -n kube5gnfvo

# 等待應用 Pod 變成 Running 狀態
kubectl wait --for=condition=ready pod -l app=kube5gnfvo -n kube5gnfvo --timeout=300s
```

### 步驟 4: 檢查應用日誌

```bash
# 查看應用日誌
kubectl logs -n kube5gnfvo -l app=kube5gnfvo -f

# 應該看到:
# - Django migrations 執行
# - Django development server 啟動
# - "Starting development server at http://0:8000/"
```

---

## 功能測試

### 測試 1: 檢查 API 端點

```bash
# 獲取 Node IP
NODE_IP=$(kubectl get nodes -o jsonpath='{.items[0].status.addresses[?(@.type=="InternalIP")].address}')

# 測試 API
curl -X GET http://$NODE_IP:30888/nslcm/v1/ns_instances/

# 應該返回 200 OK 和 JSON 響應
```

### 測試 2: 測試 VNF Package API

```bash
# 建立 VNF Package
curl -X POST http://$NODE_IP:30888/vnfpkgm/v1/vnf_packages/ \
  -H "Content-Type: application/json" \
  -d '{}'

# 應該返回 201 Created 和 package ID
```

### 測試 3: 測試 NSD API

```bash
# 建立 NSD
curl -X POST http://$NODE_IP:30888/nsd/v1/ns_descriptors/ \
  -H "Content-Type: application/json" \
  -d '{}'

# 應該返回 201 Created 和 descriptor ID
```

### 測試 4: 測試 NS Lifecycle API

```bash
# 建立 NS Instance
curl -X POST http://$NODE_IP:30888/nslcm/v1/ns_instances/ \
  -H "Content-Type: application/json" \
  -d '{
    "nsdId": "test-nsd-id",
    "nsName": "test-ns",
    "nsDescription": "Test NS Instance"
  }'

# 應該返回 201 Created 和 instance ID
```

---

## 故障排除

### 問題 1: MySQL Pod 無法啟動

```bash
# 檢查 Pod 狀態
kubectl describe pod -n kube5gnfvo -l app=kube5gnfvo-mysql

# 檢查日誌
kubectl logs -n kube5gnfvo -l app=kube5gnfvo-mysql
```

### 問題 2: 應用無法連接 MySQL

```bash
# 檢查應用日誌
kubectl logs -n kube5gnfvo -l app=kube5gnfvo

# 檢查 DNS 解析
kubectl exec -it -n kube5gnfvo $(kubectl get pod -n kube5gnfvo -l app=kube5gnfvo -o jsonpath='{.items[0].metadata.name}') -- nslookup kube5gnfvo-mysql
```

### 問題 3: API 無法訪問

```bash
# 檢查 Service
kubectl get svc -n kube5gnfvo

# 檢查 NodePort
kubectl get svc -n kube5gnfvo kube5gnfvo -o jsonpath='{.spec.ports[0].nodePort}'

# 檢查 Node IP
kubectl get nodes -o wide

# 測試連接
curl -v http://<NODE_IP>:30888/
```

---

## 清理資源

```bash
# 刪除所有部署
kubectl delete namespace kube5gnfvo
```

---

## 檢查清單

- [ ] Python 3.8+ 已安裝
- [ ] Docker 已安裝
- [ ] Kubernetes 叢集正在運行
- [ ] 依賴套件已安裝
- [ ] Django 檢查通過
- [ ] MySQL 容器已部署並運行
- [ ] 應用容器已部署並運行
- [ ] API 端點可訪問
- [ ] 資料庫連接正常
- [ ] 基本 API 測試通過
