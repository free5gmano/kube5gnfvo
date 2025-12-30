# 3. API 功能測試指南

本文檔說明如何對 Kube5GNfvo 的所有 API 進行完整的功能測試。

## 📋 前置條件

- Kube5GNfvo 應用已部署完成（參考 `2-KUBE5GNFVO_DEPLOYMENT.md`）
- 應用 API 可訪問
- 已安裝 `curl` 和 `jq`（用於 JSON 解析）

---

## 🔧 第一步：準備測試環境

### 1.1 安裝測試工具

```bash
# 安裝 jq（JSON 解析工具）
sudo apt-get install -y jq

# 安裝 httpie（可選，更友好的 HTTP 客戶端）
sudo apt-get install -y httpie

# 驗證安裝
jq --version
```

### 1.2 設定 API 基礎 URL

```bash
# 獲取 Node IP
NODE_IP=$(kubectl get nodes -o jsonpath='{.items[0].status.addresses[?(@.type=="InternalIP")].address}')

# 如果是 Minikube，使用 minikube ip
if command -v minikube &> /dev/null; then
    NODE_IP=$(minikube ip)
fi

# 設定基礎 URL
export BASE_URL="http://$NODE_IP:30888"
export API_VERSION="v1"

echo "API 基礎 URL: $BASE_URL"
```

### 1.3 建立測試函數

```bash
# 建立測試函數
test_api() {
    local method=$1
    local endpoint=$2
    local data=$3
    local description=$4
    
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "測試: $description"
    echo "方法: $method"
    echo "端點: $endpoint"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    
    if [ -z "$data" ]; then
        curl -s -w "\nHTTP 狀態碼: %{http_code}\n" \
            -X $method \
            -H "Content-Type: application/json" \
            "$BASE_URL$endpoint"
    else
        curl -s -w "\nHTTP 狀態碼: %{http_code}\n" \
            -X $method \
            -H "Content-Type: application/json" \
            -d "$data" \
            "$BASE_URL$endpoint"
    fi
}
```

---

## 🧪 第二步：NS Lifecycle Management API 測試

### 2.1 獲取 NS 實例列表

```bash
test_api "GET" "/nslcm/$API_VERSION/ns_instances/" "" "獲取 NS 實例列表"

# 預期：HTTP 200
# 響應：NS 實例列表（可能為空）
```

### 2.2 建立 NS 實例

```bash
# 首先需要上傳 NSD，獲取 NSD ID
# 這裡使用示例 NSD ID

NS_DATA='{
    "nsdId": "example-nsd-id",
    "nsName": "test-ns-instance",
    "nsDescription": "Test NS Instance"
}'

test_api "POST" "/nslcm/$API_VERSION/ns_instances/" "$NS_DATA" "建立 NS 實例"

# 預期：HTTP 201
# 響應：新建立的 NS 實例信息，包含 ID
```

### 2.3 獲取特定 NS 實例

```bash
# 使用上一步返回的 NS ID
NS_ID="<ns-instance-id>"

test_api "GET" "/nslcm/$API_VERSION/ns_instances/$NS_ID" "" "獲取特定 NS 實例"

# 預期：HTTP 200
# 響應：NS 實例詳細信息
```

### 2.4 實例化 NS

```bash
# 準備實例化數據
INSTANTIATE_DATA='{
    "vnfInstanceData": [
        {
            "vnfInstanceId": "vnf-instance-id-1",
            "vnfProfileId": "vnf-profile-1"
        }
    ]
}'

test_api "POST" "/nslcm/$API_VERSION/ns_instances/$NS_ID/instantiate/" "$INSTANTIATE_DATA" "實例化 NS"

# 預期：HTTP 202
# 響應：操作接受，返回操作 ID
```

### 2.5 終止 NS 實例

```bash
TERMINATE_DATA='{
    "terminationTime": "2025-12-31T23:59:59Z"
}'

test_api "POST" "/nslcm/$API_VERSION/ns_instances/$NS_ID/terminate/" "$TERMINATE_DATA" "終止 NS 實例"

# 預期：HTTP 202
# 響應：操作接受
```

### 2.6 刪除 NS 實例

```bash
test_api "DELETE" "/nslcm/$API_VERSION/ns_instances/$NS_ID" "" "刪除 NS 實例"

# 預期：HTTP 204
# 響應：無內容
```

---

## 📦 第三步：VNF Package Management API 測試

### 3.1 獲取 VNF 包列表

```bash
test_api "GET" "/vnfpkgm/$API_VERSION/vnf_packages/" "" "獲取 VNF 包列表"

# 預期：HTTP 200
# 響應：VNF 包列表
```

### 3.2 建立 VNF 包

```bash
VNF_DATA='{
    "userDefinedData": {
        "name": "test-vnf-package",
        "version": "1.0.0"
    }
}'

test_api "POST" "/vnfpkgm/$API_VERSION/vnf_packages/" "$VNF_DATA" "建立 VNF 包"

# 預期：HTTP 201
# 響應：新建立的 VNF 包信息，包含 ID
```

### 3.3 獲取特定 VNF 包

```bash
# 使用上一步返回的 VNF 包 ID
VNF_PKG_ID="<vnf-package-id>"

test_api "GET" "/vnfpkgm/$API_VERSION/vnf_packages/$VNF_PKG_ID" "" "獲取特定 VNF 包"

# 預期：HTTP 200
# 響應：VNF 包詳細信息
```

### 3.4 上傳 VNF 包內容

```bash
# 準備 VNF 包文件（ZIP 格式）
# 假設已有 vnf-package.zip

echo "上傳 VNF 包內容..."
curl -s -w "\nHTTP 狀態碼: %{http_code}\n" \
    -X PUT \
    -H "Accept: application/zip" \
    -H "Content-Type: application/zip" \
    --data-binary @vnf-package.zip \
    "$BASE_URL/vnfpkgm/$API_VERSION/vnf_packages/$VNF_PKG_ID/package_content/"

# 預期：HTTP 202
# 響應：操作接受
```

### 3.5 獲取 VNF 包內容

```bash
echo "下載 VNF 包內容..."
curl -s -w "\nHTTP 狀態碼: %{http_code}\n" \
    -X GET \
    -H "Accept: application/zip" \
    -o downloaded-vnf-package.zip \
    "$BASE_URL/vnfpkgm/$API_VERSION/vnf_packages/$VNF_PKG_ID/package_content/"

# 預期：HTTP 200
# 響應：ZIP 文件內容
```

### 3.6 刪除 VNF 包

```bash
test_api "DELETE" "/vnfpkgm/$API_VERSION/vnf_packages/$VNF_PKG_ID" "" "刪除 VNF 包"

# 預期：HTTP 204
# 響應：無內容
```

---

## 📋 第四步：NSD Management API 測試

### 4.1 獲取 NSD 列表

```bash
test_api "GET" "/nsd/$API_VERSION/ns_descriptors/" "" "獲取 NSD 列表"

# 預期：HTTP 200
# 響應：NSD 列表
```

### 4.2 建立 NSD

```bash
NSD_DATA='{
    "userDefinedData": {
        "name": "test-nsd",
        "version": "1.0.0"
    }
}'

test_api "POST" "/nsd/$API_VERSION/ns_descriptors/" "$NSD_DATA" "建立 NSD"

# 預期：HTTP 201
# 響應：新建立的 NSD 信息，包含 ID
```

### 4.3 獲取特定 NSD

```bash
# 使用上一步返回的 NSD ID
NSD_ID="<nsd-id>"

test_api "GET" "/nsd/$API_VERSION/ns_descriptors/$NSD_ID" "" "獲取特定 NSD"

# 預期：HTTP 200
# 響應：NSD 詳細信息
```

### 4.4 上傳 NSD 內容

```bash
# 準備 NSD 文件（ZIP 格式）
# 假設已有 nsd.zip

echo "上傳 NSD 內容..."
curl -s -w "\nHTTP 狀態碼: %{http_code}\n" \
    -X PUT \
    -H "Accept: application/zip" \
    -H "Content-Type: application/zip" \
    --data-binary @nsd.zip \
    "$BASE_URL/nsd/$API_VERSION/ns_descriptors/$NSD_ID/nsd_content/"

# 預期：HTTP 202
# 響應：操作接受
```

### 4.5 獲取 NSD 內容

```bash
echo "下載 NSD 內容..."
curl -s -w "\nHTTP 狀態碼: %{http_code}\n" \
    -X GET \
    -H "Accept: application/zip" \
    -o downloaded-nsd.zip \
    "$BASE_URL/nsd/$API_VERSION/ns_descriptors/$NSD_ID/nsd_content/"

# 預期：HTTP 200
# 響應：ZIP 文件內容
```

### 4.6 刪除 NSD

```bash
test_api "DELETE" "/nsd/$API_VERSION/ns_descriptors/$NSD_ID" "" "刪除 NSD"

# 預期：HTTP 204
# 響應：無內容
```

---

## 🔔 第五步：Subscription API 測試

### 5.1 建立 NS 訂閱

```bash
SUBSCRIPTION_DATA='{
    "callbackUri": "http://example.com/callback",
    "authentication": {
        "authType": ["BASIC"],
        "paramsBasic": {
            "userName": "user"
        }
    }
}'

test_api "POST" "/nslcm/$API_VERSION/subscriptions/" "$SUBSCRIPTION_DATA" "建立 NS 訂閱"

# 預期：HTTP 201
# 響應：訂閱信息，包含訂閱 ID
```

### 5.2 獲取訂閱列表

```bash
test_api "GET" "/nslcm/$API_VERSION/subscriptions/" "" "獲取訂閱列表"

# 預期：HTTP 200
# 響應：訂閱列表
```

### 5.3 獲取特定訂閱

```bash
# 使用上一步返回的訂閱 ID
SUBSCRIPTION_ID="<subscription-id>"

test_api "GET" "/nslcm/$API_VERSION/subscriptions/$SUBSCRIPTION_ID" "" "獲取特定訂閱"

# 預期：HTTP 200
# 響應：訂閱詳細信息
```

### 5.4 刪除訂閱

```bash
test_api "DELETE" "/nslcm/$API_VERSION/subscriptions/$SUBSCRIPTION_ID" "" "刪除訂閱"

# 預期：HTTP 204
# 響應：無內容
```

---

## 📊 第六步：完整的自動化測試腳本

### 6.1 建立測試腳本

建立 `test-all-apis.sh` 檔案：

```bash
#!/bin/bash

# Kube5GNfvo 完整 API 測試腳本

set -e

# 顏色定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 計數器
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0

# 設定 API 基礎 URL
NODE_IP=$(kubectl get nodes -o jsonpath='{.items[0].status.addresses[?(@.type=="InternalIP")].address}')
if command -v minikube &> /dev/null; then
    NODE_IP=$(minikube ip)
fi

export BASE_URL="http://$NODE_IP:30888"
export API_VERSION="v1"

echo "=========================================="
echo "Kube5GNfvo 完整 API 測試"
echo "=========================================="
echo "API 基礎 URL: $BASE_URL"
echo ""

# 測試函數
test_endpoint() {
    local method=$1
    local endpoint=$2
    local data=$3
    local expected_code=$4
    local description=$5
    
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    
    echo -n "[$TOTAL_TESTS] $description ... "
    
    if [ -z "$data" ]; then
        response=$(curl -s -w "\n%{http_code}" -X $method \
            -H "Content-Type: application/json" \
            "$BASE_URL$endpoint")
    else
        response=$(curl -s -w "\n%{http_code}" -X $method \
            -H "Content-Type: application/json" \
            -d "$data" \
            "$BASE_URL$endpoint")
    fi
    
    http_code=$(echo "$response" | tail -n1)
    
    if [ "$http_code" = "$expected_code" ]; then
        echo -e "${GREEN}✓ ($http_code)${NC}"
        PASSED_TESTS=$((PASSED_TESTS + 1))
    else
        echo -e "${RED}✗ (期望: $expected_code, 實際: $http_code)${NC}"
        FAILED_TESTS=$((FAILED_TESTS + 1))
    fi
}

# 測試 NS Lifecycle API
echo -e "${YELLOW}=== NS Lifecycle Management API ===${NC}"
test_endpoint "GET" "/nslcm/$API_VERSION/ns_instances/" "" "200" "獲取 NS 實例列表"

# 測試 VNF Package API
echo -e "${YELLOW}=== VNF Package Management API ===${NC}"
test_endpoint "GET" "/vnfpkgm/$API_VERSION/vnf_packages/" "" "200" "獲取 VNF 包列表"

# 測試 NSD API
echo -e "${YELLOW}=== NSD Management API ===${NC}"
test_endpoint "GET" "/nsd/$API_VERSION/ns_descriptors/" "" "200" "獲取 NSD 列表"

# 測試 Subscription API
echo -e "${YELLOW}=== Subscription API ===${NC}"
test_endpoint "GET" "/nslcm/$API_VERSION/subscriptions/" "" "200" "獲取訂閱列表"

# 測試結果摘要
echo ""
echo "=========================================="
echo "測試結果摘要"
echo "=========================================="
echo -e "總測試數: $TOTAL_TESTS"
echo -e "${GREEN}通過: $PASSED_TESTS${NC}"
echo -e "${RED}失敗: $FAILED_TESTS${NC}"
echo ""

if [ $FAILED_TESTS -eq 0 ]; then
    echo -e "${GREEN}✓ 所有測試通過！${NC}"
    exit 0
else
    echo -e "${RED}✗ 有 $FAILED_TESTS 個測試失敗${NC}"
    exit 1
fi
```

### 6.2 運行測試腳本

```bash
# 保存腳本
chmod +x test-all-apis.sh

# 運行測試
./test-all-apis.sh
```

---

## 🧪 第七步：使用 Postman 進行測試

### 7.1 匯入 Postman Collection

建立 `kube5gnfvo-api.postman_collection.json`：

```json
{
  "info": {
    "name": "Kube5GNfvo API",
    "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
  },
  "item": [
    {
      "name": "NS Lifecycle",
      "item": [
        {
          "name": "Get NS Instances",
          "request": {
            "method": "GET",
            "url": {
              "raw": "{{base_url}}/nslcm/v1/ns_instances/",
              "host": ["{{base_url}}"],
              "path": ["nslcm", "v1", "ns_instances"]
            }
          }
        }
      ]
    },
    {
      "name": "VNF Package",
      "item": [
        {
          "name": "Get VNF Packages",
          "request": {
            "method": "GET",
            "url": {
              "raw": "{{base_url}}/vnfpkgm/v1/vnf_packages/",
              "host": ["{{base_url}}"],
              "path": ["vnfpkgm", "v1", "vnf_packages"]
            }
          }
        }
      ]
    },
    {
      "name": "NSD",
      "item": [
        {
          "name": "Get NSD Descriptors",
          "request": {
            "method": "GET",
            "url": {
              "raw": "{{base_url}}/nsd/v1/ns_descriptors/",
              "host": ["{{base_url}}"],
              "path": ["nsd", "v1", "ns_descriptors"]
            }
          }
        }
      ]
    }
  ],
  "variable": [
    {
      "key": "base_url",
      "value": "http://localhost:30888"
    }
  ]
}
```

### 7.2 在 Postman 中使用

1. 打開 Postman
2. 點擊 "Import"
3. 選擇上面的 JSON 文件
4. 設定 `base_url` 變數為你的 API 地址
5. 運行請求

---

## 📈 第八步：性能測試

### 8.1 使用 Apache Bench 進行負載測試

```bash
# 安裝 Apache Bench
sudo apt-get install -y apache2-utils

# 執行負載測試（100 個請求，10 個並發）
ab -n 100 -c 10 "$BASE_URL/nslcm/$API_VERSION/ns_instances/"

# 執行更激進的測試（1000 個請求，50 個並發）
ab -n 1000 -c 50 "$BASE_URL/nslcm/$API_VERSION/ns_instances/"
```

### 8.2 使用 wrk 進行性能測試

```bash
# 安裝 wrk
sudo apt-get install -y wrk

# 執行性能測試（4 個線程，12 個連接，30 秒）
wrk -t4 -c12 -d30s "$BASE_URL/nslcm/$API_VERSION/ns_instances/"
```

---

## ✅ 測試檢查清單

- [ ] NS Lifecycle API 測試通過
- [ ] VNF Package API 測試通過
- [ ] NSD API 測試通過
- [ ] Subscription API 測試通過
- [ ] 所有 GET 請求返回 HTTP 200
- [ ] 所有 POST 請求返回 HTTP 201 或 202
- [ ] 所有 DELETE 請求返回 HTTP 204
- [ ] 錯誤請求返回適當的錯誤碼
- [ ] 性能測試通過
- [ ] 沒有 5xx 錯誤

---

## 🆘 故障排除

### 問題：API 無法訪問

```bash
# 檢查應用 Pod 狀態
kubectl get pods -n kube5gnfvo -l app=kube5gnfvo

# 檢查應用日誌
kubectl logs -n kube5gnfvo -l app=kube5gnfvo --tail=50

# 測試 Pod 內部連接
kubectl exec -it -n kube5gnfvo $(kubectl get pod -n kube5gnfvo -l app=kube5gnfvo -o jsonpath='{.items[0].metadata.name}') -- \
  curl -v http://localhost:8000/nslcm/v1/ns_instances/
```

### 問題：API 返回 500 錯誤

```bash
# 查看詳細的應用日誌
kubectl logs -n kube5gnfvo -l app=kube5gnfvo -f

# 進入 Pod 檢查
kubectl exec -it -n kube5gnfvo $(kubectl get pod -n kube5gnfvo -l app=kube5gnfvo -o jsonpath='{.items[0].metadata.name}') -- bash
```

### 問題：資料庫連接錯誤

```bash
# 檢查 MySQL 連接
kubectl exec -it -n kube5gnfvo $(kubectl get pod -n kube5gnfvo -l app=kube5gnfvo -o jsonpath='{.items[0].metadata.name}') -- \
  nc -zv kube5gnfvo-mysql 3306

# 檢查 MySQL 日誌
kubectl logs -n kube5gnfvo -l app=kube5gnfvo-mysql --tail=50
```

---

**完成！** 所有 API 功能測試已完成。如有問題，請參考故障排除部分。
