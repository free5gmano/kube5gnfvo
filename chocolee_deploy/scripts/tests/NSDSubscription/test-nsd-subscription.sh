#!/bin/bash

# NSDSubscription 模組測試 - 運行所有 API 測試

BASE_URL="${1:-http://localhost:8000}"
PASSED=0
FAILED=0

echo "🧪 NSDSubscription 測試"
echo "---"

apis_dir="$(dirname "$0")/apis"

# 獲取 NSD ID
NSD_LIST=$(curl -s -X GET "$BASE_URL/nsd/v1/ns_descriptors/")
NSD_ID=$(echo "$NSD_LIST" | grep -o '"id":"[^"]*' | head -1 | cut -d'"' -f4)

if [ -z "$NSD_ID" ]; then
  echo "⚠️  沒有找到 NSD，跳過測試"
  exit 0
fi

# 1. 查詢訂閱列表
bash "$apis_dir/01-list-subscriptions.sh" "$BASE_URL" > /tmp/test_output.txt 2>&1
if [ $? -eq 0 ]; then
  cat /tmp/test_output.txt
  ((PASSED++))
else
  cat /tmp/test_output.txt
  ((FAILED++))
fi

# 2. 建立訂閱
bash "$apis_dir/03-create-subscription.sh" "$BASE_URL" "$NSD_ID" > /tmp/test_output.txt 2>&1
if [ $? -eq 0 ]; then
  SUB_ID=$(tail -1 /tmp/test_output.txt)
  head -1 /tmp/test_output.txt
  ((PASSED++))
else
  cat /tmp/test_output.txt
  ((FAILED++))
  SUB_ID=""
fi

# 3. 查詢單個訂閱
if [ -n "$SUB_ID" ]; then
  bash "$apis_dir/02-get-subscription.sh" "$BASE_URL" "$SUB_ID" > /tmp/test_output.txt 2>&1
  if [ $? -eq 0 ]; then
    cat /tmp/test_output.txt
    ((PASSED++))
  else
    cat /tmp/test_output.txt
    ((FAILED++))
  fi
fi

# 4. 刪除訂閱
if [ -n "$SUB_ID" ]; then
  bash "$apis_dir/04-delete-subscription.sh" "$BASE_URL" "$SUB_ID" > /tmp/test_output.txt 2>&1
  if [ $? -eq 0 ]; then
    cat /tmp/test_output.txt
    ((PASSED++))
  else
    cat /tmp/test_output.txt
    ((FAILED++))
  fi
fi

echo ""
echo "結果: $PASSED 通過, $FAILED 失敗"
[ $FAILED -eq 0 ]
