#!/bin/bash

# Kube5GNfvo API 測試腳本

BASE_URL="http://localhost:8000"

echo "=========================================="
echo "Kube5GNfvo API 功能測試"
echo "=========================================="
echo ""

# 1. 測試 NS Lifecycle API
echo "[1/4] 測試 NS Lifecycle API..."
RESPONSE=$(curl -s -w "\n%{http_code}" -X GET "$BASE_URL/nslcm/v1/ns_instances/")
HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
BODY=$(echo "$RESPONSE" | head -n-1)

if [ "$HTTP_CODE" = "200" ]; then
    echo "✅ NS Lifecycle API: $HTTP_CODE"
    echo "  響應: $BODY" | head -c 100
    echo ""
else
    echo "❌ NS Lifecycle API: $HTTP_CODE"
fi
echo ""

# 2. 測試 VNF Package API
echo "[2/4] 測試 VNF Package API..."
RESPONSE=$(curl -s -w "\n%{http_code}" -X GET "$BASE_URL/vnfpkgm/v1/vnf_packages/")
HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
BODY=$(echo "$RESPONSE" | head -n-1)

if [ "$HTTP_CODE" = "200" ] || [ "$HTTP_CODE" = "409" ]; then
    echo "✅ VNF Package API: $HTTP_CODE"
else
    echo "❌ VNF Package API: $HTTP_CODE"
fi
echo ""

# 3. 測試 NSD API
echo "[3/4] 測試 NSD API..."
RESPONSE=$(curl -s -w "\n%{http_code}" -X GET "$BASE_URL/nsd/v1/ns_descriptors/")
HTTP_CODE=$(echo "$RESPONSE" | tail -n1)

if [ "$HTTP_CODE" = "200" ]; then
    echo "✅ NSD API: $HTTP_CODE"
else
    echo "❌ NSD API: $HTTP_CODE"
fi
echo ""

# 4. 測試資料庫連接
echo "[4/4] 測試資料庫連接..."
DB_TEST=$(python3 -c "
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
" 2>&1 | grep -E "✅|❌")
echo "$DB_TEST"
echo ""

echo "=========================================="
echo "API 功能測試完成"
echo "=========================================="
