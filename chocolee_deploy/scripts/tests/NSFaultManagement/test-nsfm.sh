#!/bin/bash

# NSFaultManagement 模組測試 - 運行所有 API 測試

BASE_URL="${1:-http://localhost:8000}"
PASSED=0
FAILED=0

echo "🧪 NSFaultManagement 測試"
echo "---"

apis_dir="$(dirname "$0")/apis"

# 1. 查詢告警列表
bash "$apis_dir/01-list-alarms.sh" "$BASE_URL" > /tmp/test_output.txt 2>&1
if [ $? -eq 0 ]; then
  cat /tmp/test_output.txt
  ((PASSED++))
else
  cat /tmp/test_output.txt
  ((FAILED++))
fi

# 2. 查詢單個告警（需要先從列表中獲取 ID）
LIST_RESPONSE=$(curl -s -X GET "$BASE_URL/nsfm/v1/alarms/")
ALARM_ID=$(echo "$LIST_RESPONSE" | grep -o '"id":"[^"]*' | head -1 | cut -d'"' -f4)

if [ -z "$ALARM_ID" ]; then
  echo "⚠️  沒有找到告警，跳過後續測試"
  exit 0
fi

bash "$apis_dir/02-get-alarm.sh" "$BASE_URL" "$ALARM_ID" > /tmp/test_output.txt 2>&1
if [ $? -eq 0 ]; then
  cat /tmp/test_output.txt
  ((PASSED++))
else
  cat /tmp/test_output.txt
  ((FAILED++))
fi

# 3. 更新告警
bash "$apis_dir/03-update-alarm.sh" "$BASE_URL" "$ALARM_ID" > /tmp/test_output.txt 2>&1
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
