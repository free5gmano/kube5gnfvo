#!/bin/bash

# NSLifecycleManagement 模組測試 - 運行所有 API 測試

BASE_URL="${1:-http://localhost:8000}"
PASSED=0
FAILED=0

echo "🧪 NSLifecycleManagement 測試"
echo "---"

apis_dir="$(dirname "$0")/apis"

# 1. 查詢 NS Instance 列表
bash "$apis_dir/01-list-instances.sh" "$BASE_URL" > /tmp/test_output.txt 2>&1
if [ $? -eq 0 ]; then
  cat /tmp/test_output.txt
  ((PASSED++))
else
  cat /tmp/test_output.txt
  ((FAILED++))
fi

# 獲取有效的 NSD ID（nsdId 不為 null）
NSD_LIST=$(curl -s -X GET "$BASE_URL/nsd/v1/ns_descriptors/")
NSD_ID=$(echo "$NSD_LIST" | grep -o '"nsdId":"[^"]*' | head -1 | cut -d'"' -f4)

if [ -z "$NSD_ID" ] || [ "$NSD_ID" = "null" ]; then
  echo "⚠️  沒有找到有效的 NSD（nsdId 不為 null），跳過後續測試"
  exit 0
fi

# 2. 建立 NS Instance
bash "$apis_dir/03-create-instance.sh" "$BASE_URL" "$NSD_ID" > /tmp/test_output.txt 2>&1
if [ $? -eq 0 ]; then
  NS_ID=$(tail -1 /tmp/test_output.txt)
  head -1 /tmp/test_output.txt
  ((PASSED++))
else
  cat /tmp/test_output.txt
  ((FAILED++))
  NS_ID=""
fi

# 3. 查詢單個 NS Instance
if [ -n "$NS_ID" ]; then
  bash "$apis_dir/02-get-instance.sh" "$BASE_URL" "$NS_ID" > /tmp/test_output.txt 2>&1
  if [ $? -eq 0 ]; then
    cat /tmp/test_output.txt
    ((PASSED++))
  else
    cat /tmp/test_output.txt
    ((FAILED++))
  fi
fi

# 4. 實例化 NS Instance
if [ -n "$NS_ID" ]; then
  bash "$apis_dir/05-instantiate-instance.sh" "$BASE_URL" "$NS_ID" > /tmp/test_output.txt 2>&1
  if [ $? -eq 0 ]; then
    cat /tmp/test_output.txt
    ((PASSED++))
  else
    cat /tmp/test_output.txt
    ((FAILED++))
  fi
fi

# 5. 擴展 NS Instance
if [ -n "$NS_ID" ]; then
  bash "$apis_dir/07-scale-instance.sh" "$BASE_URL" "$NS_ID" > /tmp/test_output.txt 2>&1
  if [ $? -eq 0 ]; then
    cat /tmp/test_output.txt
    ((PASSED++))
  else
    cat /tmp/test_output.txt
    ((FAILED++))
  fi
fi

# 6. 更新 NS Instance
if [ -n "$NS_ID" ]; then
  bash "$apis_dir/08-update-instance.sh" "$BASE_URL" "$NS_ID" > /tmp/test_output.txt 2>&1
  if [ $? -eq 0 ]; then
    cat /tmp/test_output.txt
    ((PASSED++))
  else
    cat /tmp/test_output.txt
    ((FAILED++))
  fi
fi

# 7. 修復 NS Instance
if [ -n "$NS_ID" ]; then
  bash "$apis_dir/09-heal-instance.sh" "$BASE_URL" "$NS_ID" > /tmp/test_output.txt 2>&1
  if [ $? -eq 0 ]; then
    cat /tmp/test_output.txt
    ((PASSED++))
  else
    cat /tmp/test_output.txt
    ((FAILED++))
  fi
fi

# 8. 終止 NS Instance
if [ -n "$NS_ID" ]; then
  bash "$apis_dir/06-terminate-instance.sh" "$BASE_URL" "$NS_ID" > /tmp/test_output.txt 2>&1
  if [ $? -eq 0 ]; then
    cat /tmp/test_output.txt
    ((PASSED++))
  else
    cat /tmp/test_output.txt
    ((FAILED++))
  fi
fi

# 9. 刪除 NS Instance
if [ -n "$NS_ID" ]; then
  bash "$apis_dir/04-delete-instance.sh" "$BASE_URL" "$NS_ID" > /tmp/test_output.txt 2>&1
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
