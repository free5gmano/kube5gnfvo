#!/bin/bash

# NSDManagement 模組測試 - 運行所有 API 測試

BASE_URL="${1:-http://localhost:8000}"
PASSED=0
FAILED=0

echo "🧪 NSDManagement 測試"
echo "---"

apis_dir="$(dirname "$0")/apis"

# 1. 查詢 NSD 列表
bash "$apis_dir/01-list-nsd.sh" "$BASE_URL" > /tmp/test_output.txt 2>&1
if [ $? -eq 0 ]; then
  cat /tmp/test_output.txt
  ((PASSED++))
else
  cat /tmp/test_output.txt
  ((FAILED++))
fi

# 2. 建立 NSD
bash "$apis_dir/03-create-nsd.sh" "$BASE_URL" > /tmp/test_output.txt 2>&1
if [ $? -eq 0 ]; then
  NSD_ID=$(tail -1 /tmp/test_output.txt)
  head -1 /tmp/test_output.txt
  ((PASSED++))
else
  cat /tmp/test_output.txt
  ((FAILED++))
  NSD_ID=""
fi

# 3. 查詢單個 NSD
if [ -n "$NSD_ID" ]; then
  bash "$apis_dir/02-get-nsd.sh" "$BASE_URL" "$NSD_ID" > /tmp/test_output.txt 2>&1
  if [ $? -eq 0 ]; then
    cat /tmp/test_output.txt
    ((PASSED++))
  else
    cat /tmp/test_output.txt
    ((FAILED++))
  fi
fi

# 4. 上傳 NSD 內容
if [ -n "$NSD_ID" ]; then
  bash "$apis_dir/07-upload-nsd-content.sh" "$BASE_URL" "$NSD_ID" > /tmp/test_output.txt 2>&1
  if [ $? -eq 0 ]; then
    cat /tmp/test_output.txt
    ((PASSED++))
  else
    cat /tmp/test_output.txt
    ((FAILED++))
  fi
fi

# 5. 下載 NSD 內容
if [ -n "$NSD_ID" ]; then
  bash "$apis_dir/08-download-nsd-content.sh" "$BASE_URL" "$NSD_ID" > /tmp/test_output.txt 2>&1
  if [ $? -eq 0 ]; then
    cat /tmp/test_output.txt
    ((PASSED++))
  else
    cat /tmp/test_output.txt
    ((FAILED++))
  fi
fi

# 6. 更新 NSD
if [ -n "$NSD_ID" ]; then
  bash "$apis_dir/05-update-nsd.sh" "$BASE_URL" "$NSD_ID" > /tmp/test_output.txt 2>&1
  if [ $? -eq 0 ]; then
    cat /tmp/test_output.txt
    ((PASSED++))
  else
    cat /tmp/test_output.txt
    ((FAILED++))
  fi
fi

# 7. 刪除 NSD
if [ -n "$NSD_ID" ]; then
  bash "$apis_dir/04-delete-nsd.sh" "$BASE_URL" "$NSD_ID" > /tmp/test_output.txt 2>&1
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
