#!/bin/bash

# NSLCMOperationOccurrences 模組測試 - 運行所有 API 測試

BASE_URL="${1:-http://localhost:8000}"
PASSED=0
FAILED=0

echo "🧪 NSLCMOperationOccurrences 測試"
echo "---"

apis_dir="$(dirname "$0")/apis"

# 1. 查詢 LCM 操作列表
bash "$apis_dir/01-list-operations.sh" "$BASE_URL" > /tmp/test_output.txt 2>&1
if [ $? -eq 0 ]; then
  cat /tmp/test_output.txt
  ((PASSED++))
else
  cat /tmp/test_output.txt
  ((FAILED++))
fi

# 2. 查詢單個 LCM 操作（需要先從列表中獲取 ID）
LIST_RESPONSE=$(curl -s -X GET "$BASE_URL/nslcm/v1/ns_lcm_op_occs/")
OP_ID=$(echo "$LIST_RESPONSE" | grep -o '"id":"[^"]*' | head -1 | cut -d'"' -f4)

if [ -z "$OP_ID" ]; then
  echo "⚠️  沒有找到 LCM 操作，跳過後續測試"
  exit 0
fi

bash "$apis_dir/02-get-operation.sh" "$BASE_URL" "$OP_ID" > /tmp/test_output.txt 2>&1
if [ $? -eq 0 ]; then
  cat /tmp/test_output.txt
  ((PASSED++))
else
  cat /tmp/test_output.txt
  ((FAILED++))
fi

echo ""
echo "結果: $PASSED 通過, $FAILED 失敗"
[ $FAILED -eq 0 ]
