#!/bin/bash

# VIMManagement 模組測試 - 運行所有 API 測試

BASE_URL="${1:-http://localhost:8000}"
PASSED=0
FAILED=0

echo "🧪 VIMManagement 測試"
echo "---"

apis_dir="$(dirname "$0")/apis"

# 1. 查詢 Kubernetes 資源
bash "$apis_dir/01-get-kubernetes-resources.sh" "$BASE_URL" > /tmp/test_output.txt 2>&1
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
