# 2. Kube5GNfvo 應用部署指南

本文檔說明如何在已部署的 Kubernetes 環境中部署 Kube5GNfvo 應用。

## 📋 前置條件

- Kubernetes 環境已部署完成（參考 `1-ENVIRONMENT_SETUP.md`）
- kubectl 已配置並可訪問叢集
- 所有節點狀態為 Ready
- 至少 20GB 可用磁碟空間

---

## 🚀 第一步：準備部署環境

### 1.1 建立命名空間和儲存目錄

```bash
# 建立儲存目錄
sudo mkdir -p /mnt/kube5gnfvo
sudo mkdir -p /mnt/kube5gnfvo-mysql
sudo chmod 777 /mnt/kube5gnfvo
sudo chmod 777 /mnt/kube5gnfvo-mysql

# 驗證目錄
ls -la /mnt/ | grep kube5gnfvo
```

### 1.2 載入環境變數

```bash
# 從 .env 檔案載入環境變數
if [ -f .env ]; then
    export $(cat .env | grep -v '#' | xargs)
else
    echo "警告：.env 檔案不存在，使用預設值"
    export NAMESPACE=kube5gnfvo
    export MYSQL_ROOT_PASSWORD=password
    export MYSQL_DATABASE=kube5gnfvo
    export APP_PORT=8000
    export APP_NODE_PORT=30888
fi

echo "部署配置："
echo "  命名空間: $NAMESPACE"
echo "  MySQL 密碼: $MYSQL_ROOT_PASSWORD"
echo "  應用端口: $APP_PORT"
echo "  NodePort: $APP_NODE_PORT"
```

---

## 🗄️ 第二步：部署 MySQL 資料庫

### 2.1 部署 MySQL

```bash
# 部署 MySQL
kubectl apply -f kubernetes/mysql/kube5gnfvo-mysql-simple.yaml

# 驗證部署
kubectl get pods -n kube5gnfvo -l app=kube5gnfvo-mysql
```

### 2.2 等待 MySQL 啟動

```bash
# 等待 MySQL Pod 就緒（最多 120 秒）
kubectl wait --for=condition=ready pod \
  -l app=kube5gnfvo-mysql \
  -n kube5gnfvo \
  --timeout=120s

echo "✅ MySQL 已啟動"
```

### 2.3 驗證 MySQL 連接

```bash
# 獲取 MySQL Pod 名稱
MYSQL_POD=$(kubectl get pod -n kube5gnfvo -l app=kube5gnfvo-mysql -o jsonpath='{.items[0].metadata.name}')

# 測試 MySQL 連接
kubectl exec -n kube5gnfvo $MYSQL_POD -- \
  mysql -u root -p$MYSQL_ROOT_PASSWORD -e "SHOW DATABASES;"

# 預期輸出應包含 kube5gnfvo 和 os_ma_nfvo 資料庫
```

### 2.4 檢查 MySQL 日誌

```bash
# 查看 MySQL 啟動日誌
kubectl logs -n kube5gnfvo -l app=kube5gnfvo-mysql --tail=50
```

---

## 🚀 第三步：部署 Kube5GNfvo 應用

### 3.1 部署應用

```bash
# 部署 Kube5GNfvo 應用
kubectl apply -f kubernetes/app/kube5gnfvo-app-deploy.yaml

# 驗證部署
kubectl get pods -n kube5gnfvo -l app=kube5gnfvo
```

### 3.2 等待應用啟動

```bash
# 等待應用 Pod 就緒（最多 180 秒）
kubectl wait --for=condition=ready pod \
  -l app=kube5gnfvo \
  -n kube5gnfvo \
  --timeout=180s

echo "✅ Kube5GNfvo 應用已啟動"
```

### 3.3 檢查應用日誌

```bash
# 獲取應用 Pod 名稱
APP_POD=$(kubectl get pod -n kube5gnfvo -l app=kube5gnfvo -o jsonpath='{.items[0].metadata.name}')

# 查看應用啟動日誌
kubectl logs -n kube5gnfvo $APP_POD --tail=100

# 實時監控日誌
kubectl logs -n kube5gnfvo $APP_POD -f
```

---

## 🔍 第四步：驗證部署

### 4.1 檢查所有資源

```bash
#!/bin/bash

echo "=========================================="
echo "Kube5GNfvo 部署驗證"
echo "=========================================="
echo ""

# 檢查命名空間
echo "✓ 命名空間:"
kubectl get namespace kube5gnfvo

# 檢查 Pod
echo ""
echo "✓ Pod 狀態:"
kubectl get pods -n kube5gnfvo

# 檢查 Service
echo ""
echo "✓ Service:"
kubectl get svc -n kube5gnfvo

# 檢查 PVC
echo ""
echo "✓ PersistentVolumeClaim:"
kubectl get pvc -n kube5gnfvo

# 檢查 PV
echo ""
echo "✓ PersistentVolume:"
kubectl get pv | grep kube5gnfvo

# 檢查 Deployment
echo ""
echo "✓ Deployment:"
kubectl get deployment -n kube5gnfvo

echo ""
echo "=========================================="
```

### 4.2 測試應用連接

```bash
# 獲取 Node IP
NODE_IP=$(kubectl get nodes -o jsonpath='{.items[0].status.addresses[?(@.type=="InternalIP")].address}')

# 如果是 Minikube，使用 minikube ip
if command -v minikube &> /dev/null; then
    NODE_IP=$(minikube ip)
fi

echo "Node IP: $NODE_IP"

# 測試 API 連接
echo ""
echo "測試 API 連接..."
curl -v http://$NODE_IP:30888/nslcm/v1/ns_instances/

# 預期：HTTP 200 或 401（如果需要認證）
```

### 4.3 檢查資料庫連接

```bash
# 進入應用 Pod
APP_POD=$(kubectl get pod -n kube5gnfvo -l app=kube5gnfvo -o jsonpath='{.items[0].metadata.name}')

# 測試資料庫連接
kubectl exec -n kube5gnfvo $APP_POD -- \
  python3 -c "
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'os_ma_nfvo.settings')
import django
django.setup()
from django.db import connection
try:
    with connection.cursor() as cursor:
        cursor.execute('SELECT 1')
    print('✅ 資料庫連接成功')
except Exception as e:
    print(f'❌ 資料庫連接失敗: {e}')
"
```

---

## 🔧 第五步：配置應用

### 5.1 執行資料庫遷移

```bash
# 獲取應用 Pod 名稱
APP_POD=$(kubectl get pod -n kube5gnfvo -l app=kube5gnfvo -o jsonpath='{.items[0].metadata.name}')

# 執行遷移
kubectl exec -n kube5gnfvo $APP_POD -- \
  python3 manage.py migrate

echo "✅ 資料庫遷移完成"
```

### 5.2 建立超級使用者（可選）

```bash
# 建立超級使用者
kubectl exec -it -n kube5gnfvo $APP_POD -- \
  python3 manage.py createsuperuser

# 按提示輸入使用者名稱、郵箱和密碼
```

### 5.3 收集靜態檔案（可選）

```bash
# 收集靜態檔案
kubectl exec -n kube5gnfvo $APP_POD -- \
  python3 manage.py collectstatic --noinput

echo "✅ 靜態檔案收集完成"
```

---

## 📊 第六步：監控部署

### 6.1 實時監控 Pod

```bash
# 監控 Pod 資源使用情況
kubectl top pods -n kube5gnfvo

# 監控節點資源使用情況
kubectl top nodes
```

### 6.2 查看事件日誌

```bash
# 查看命名空間事件
kubectl get events -n kube5gnfvo --sort-by='.lastTimestamp'

# 實時監控事件
kubectl get events -n kube5gnfvo -w
```

### 6.3 檢查 Pod 詳細信息

```bash
# 獲取 MySQL Pod 詳細信息
MYSQL_POD=$(kubectl get pod -n kube5gnfvo -l app=kube5gnfvo-mysql -o jsonpath='{.items[0].metadata.name}')
kubectl describe pod -n kube5gnfvo $MYSQL_POD

# 獲取應用 Pod 詳細信息
APP_POD=$(kubectl get pod -n kube5gnfvo -l app=kube5gnfvo -o jsonpath='{.items[0].metadata.name}')
kubectl describe pod -n kube5gnfvo $APP_POD
```

---

## 🧪 第七步：基本功能測試

### 7.1 測試 API 端點

```bash
# 獲取 Node IP
NODE_IP=$(kubectl get nodes -o jsonpath='{.items[0].status.addresses[?(@.type=="InternalIP")].address}')
if command -v minikube &> /dev/null; then
    NODE_IP=$(minikube ip)
fi

BASE_URL="http://$NODE_IP:30888"

echo "=========================================="
echo "API 端點測試"
echo "=========================================="
echo ""

# 1. 測試 NS Lifecycle API
echo "[1/3] 測試 NS Lifecycle API..."
curl -s -w "HTTP %{http_code}\n" -X GET "$BASE_URL/nslcm/v1/ns_instances/" | head -1

# 2. 測試 VNF Package API
echo "[2/3] 測試 VNF Package API..."
curl -s -w "HTTP %{http_code}\n" -X GET "$BASE_URL/vnfpkgm/v1/vnf_packages/" | head -1

# 3. 測試 NSD API
echo "[3/3] 測試 NSD API..."
curl -s -w "HTTP %{http_code}\n" -X GET "$BASE_URL/nsd/v1/ns_descriptors/" | head -1

echo ""
echo "=========================================="
```

---

## 🧹 清理部署

### 完全清理

```bash
# 刪除所有 Kube5GNfvo 資源
kubectl delete namespace kube5gnfvo

# 刪除 PersistentVolume
kubectl delete pv kube5gnfvo-pv 2>/dev/null

# 刪除本地資料
sudo rm -rf /mnt/kube5gnfvo
sudo rm -rf /mnt/kube5gnfvo-mysql

echo "✅ 清理完成"
```

### 部分清理

```bash
# 只刪除應用，保留資料庫
kubectl delete deployment kube5gnfvo -n kube5gnfvo

# 只刪除資料庫，保留應用
kubectl delete deployment kube5gnfvo-mysql -n kube5gnfvo
```

---

## ✅ 部署檢查清單

- [ ] MySQL 部署完成並運行
- [ ] MySQL 資料庫已建立
- [ ] 應用部署完成並運行
- [ ] 應用 Pod 狀態為 Running
- [ ] Service 已建立並可訪問
- [ ] 資料庫遷移已執行
- [ ] API 端點可訪問
- [ ] 應用日誌無錯誤

---

## 🆘 故障排除

### 問題：MySQL Pod 無法啟動

```bash
# 檢查 Pod 詳細信息
kubectl describe pod -n kube5gnfvo -l app=kube5gnfvo-mysql

# 檢查日誌
kubectl logs -n kube5gnfvo -l app=kube5gnfvo-mysql

# 檢查儲存目錄權限
ls -la /mnt/kube5gnfvo-mysql
```

### 問題：應用無法連接 MySQL

```bash
# 檢查 DNS 解析
kubectl exec -it -n kube5gnfvo $(kubectl get pod -n kube5gnfvo -l app=kube5gnfvo -o jsonpath='{.items[0].metadata.name}') -- \
  nslookup kube5gnfvo-mysql

# 測試 TCP 連接
kubectl exec -it -n kube5gnfvo $(kubectl get pod -n kube5gnfvo -l app=kube5gnfvo -o jsonpath='{.items[0].metadata.name}') -- \
  nc -zv kube5gnfvo-mysql 3306
```

### 問題：API 無法訪問

```bash
# 檢查 Service
kubectl get svc -n kube5gnfvo

# 檢查 NodePort
kubectl get svc -n kube5gnfvo kube5gnfvo -o jsonpath='{.spec.ports[0].nodePort}'

# 測試 Pod 內部連接
kubectl exec -it -n kube5gnfvo $(kubectl get pod -n kube5gnfvo -l app=kube5gnfvo -o jsonpath='{.items[0].metadata.name}') -- \
  curl -v http://localhost:8000/nslcm/v1/ns_instances/
```

---

**下一步：** 應用部署完成後，請參考 `3-API_TESTING.md` 進行完整的 API 功能測試。
