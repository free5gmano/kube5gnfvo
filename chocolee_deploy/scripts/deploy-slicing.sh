#!/bin/bash

# Kube5GNfvo 切片部署腳本

set -e

BASE_URL="http://localhost:8000"
EXAMPLE_DIR="../examples/free5gcv1"

echo "=========================================="
echo "Kube5GNfvo 切片部署"
echo "=========================================="
echo ""

# 1. 準備 VNF 包
echo "[1/4] 準備 VNF 包..."
cd "$EXAMPLE_DIR/vnfpackage"
for dir in */; do
    if [ ! -f "${dir%/}.zip" ]; then
        echo "  壓縮 ${dir%/}..."
        zip -r -q "${dir%/}.zip" "$dir"
    fi
done
cd - > /dev/null
echo "✅ VNF 包準備完成"
echo ""

# 2. 上傳 VNF 包
echo "[2/4] 上傳 VNF 包..."
for vnf_file in "$EXAMPLE_DIR/vnfpackage"/*.zip; do
    vnf_name=$(basename "$vnf_file" .zip)
    echo "  上傳 $vnf_name..."
    
    # 建立 VNF Package
    RESPONSE=$(curl -s -X POST "$BASE_URL/vnfpkgm/v1/vnf_packages/" \
        -H "Content-Type: application/json" \
        -d '{}')
    
    VNF_ID=$(echo "$RESPONSE" | grep -o '"id":"[^"]*' | cut -d'"' -f4)
    
    if [ -z "$VNF_ID" ]; then
        echo "  ❌ 無法建立 VNF Package"
        continue
    fi
    
    echo "    VNF ID: $VNF_ID"
    
    # 上傳 VNF 包內容
    curl -s -X PUT "$BASE_URL/vnfpkgm/v1/vnf_packages/$VNF_ID/package_content/" \
        -H "Accept: application/zip" \
        -H "Accept: application/json" \
        -F "file=@$vnf_file" > /dev/null
    
    echo "    ✅ $vnf_name 上傳完成"
done
echo "✅ VNF 包上傳完成"
echo ""

# 3. 上傳 NS 描述符
echo "[3/4] 上傳 NS 描述符..."
NS_ZIP="$EXAMPLE_DIR/ns.zip"
if [ ! -f "$NS_ZIP" ]; then
    echo "  壓縮 NS..."
    cd "$EXAMPLE_DIR"
    zip -r -q ns.zip ns/
    cd - > /dev/null
fi

# 建立 NSD
RESPONSE=$(curl -s -X POST "$BASE_URL/nsd/v1/ns_descriptors/" \
    -H "Content-Type: application/json" \
    -d '{}')

NSD_ID=$(echo "$RESPONSE" | grep -o '"id":"[^"]*' | cut -d'"' -f4)

if [ -z "$NSD_ID" ]; then
    echo "  ❌ 無法建立 NSD"
    exit 1
fi

echo "  NSD ID: $NSD_ID"

# 上傳 NSD 內容
curl -s -X PUT "$BASE_URL/nsd/v1/ns_descriptors/$NSD_ID/nsd_content/" \
    -H "Accept: application/zip" \
    -H "Accept: application/json" \
    -F "file=@$NS_ZIP" > /dev/null

echo "✅ NS 描述符上傳完成"
echo ""

# 4. 建立 NS 實例
echo "[4/4] 建立 NS 實例..."

# 建立 NS Instance
RESPONSE=$(curl -s -X POST "$BASE_URL/nslcm/v1/ns_instances/" \
    -H "Content-Type: application/json" \
    -d "{
        \"nsdId\": \"$NSD_ID\",
        \"nsName\": \"free5gc-ns\",
        \"nsDescription\": \"Free5GC Network Slice\"
    }")

NS_INSTANCE_ID=$(echo "$RESPONSE" | grep -o '"id":"[^"]*' | cut -d'"' -f4)

if [ -z "$NS_INSTANCE_ID" ]; then
    echo "  ❌ 無法建立 NS Instance"
    exit 1
fi

echo "  NS Instance ID: $NS_INSTANCE_ID"

# 實例化 NS
curl -s -X POST "$BASE_URL/nslcm/v1/ns_instances/$NS_INSTANCE_ID/instantiate/" \
    -H "Content-Type: application/json" \
    -d "{
        \"vnfInstanceData\": []
    }" > /dev/null

echo "✅ NS 實例建立完成"
echo ""

echo "=========================================="
echo "切片部署完成"
echo "=========================================="
echo ""
echo "NS Instance ID: $NS_INSTANCE_ID"
echo "NSD ID: $NSD_ID"
echo ""
echo "檢查部署狀態:"
echo "  curl -X GET $BASE_URL/nslcm/v1/ns_instances/$NS_INSTANCE_ID/"
