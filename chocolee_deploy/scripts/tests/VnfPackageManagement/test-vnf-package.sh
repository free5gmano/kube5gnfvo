#!/bin/bash

# VnfPackageManagement 模組測試 - 運行所有 API 測試

BASE_URL="${1:-http://localhost:8000}"
PASSED=0
FAILED=0

echo "🧪 VnfPackageManagement 測試"
echo "---"

apis_dir="$(dirname "$0")/apis"

# 1. 查詢 VNF 套件列表
bash "$apis_dir/01-list-packages.sh" "$BASE_URL" > /tmp/test_output.txt 2>&1
if [ $? -eq 0 ]; then
  cat /tmp/test_output.txt
  ((PASSED++))
else
  cat /tmp/test_output.txt
  ((FAILED++))
fi

# 2. 建立 VNF 套件
bash "$apis_dir/03-create-package.sh" "$BASE_URL" > /tmp/test_output.txt 2>&1
if [ $? -eq 0 ]; then
  VNF_ID=$(tail -1 /tmp/test_output.txt)
  head -1 /tmp/test_output.txt
  ((PASSED++))
else
  cat /tmp/test_output.txt
  ((FAILED++))
  VNF_ID=""
fi

# 3. 查詢單個 VNF 套件
if [ -n "$VNF_ID" ]; then
  bash "$apis_dir/02-get-package.sh" "$BASE_URL" "$VNF_ID" > /tmp/test_output.txt 2>&1
  if [ $? -eq 0 ]; then
    cat /tmp/test_output.txt
    ((PASSED++))
  else
    cat /tmp/test_output.txt
    ((FAILED++))
  fi
fi

# 4. 更新 VNF 套件
if [ -n "$VNF_ID" ]; then
  bash "$apis_dir/04-update-package.sh" "$BASE_URL" "$VNF_ID" > /tmp/test_output.txt 2>&1
  if [ $? -eq 0 ]; then
    cat /tmp/test_output.txt
    ((PASSED++))
  else
    cat /tmp/test_output.txt
    ((FAILED++))
  fi
fi

# 5. 上傳 VNF 套件內容
if [ -n "$VNF_ID" ]; then
  bash "$apis_dir/06-upload-package-content.sh" "$BASE_URL" "$VNF_ID" > /tmp/test_output.txt 2>&1
  if [ $? -eq 0 ]; then
    cat /tmp/test_output.txt
    ((PASSED++))
  else
    cat /tmp/test_output.txt
    ((FAILED++))
  fi
fi

# 6. 下載 VNF 套件內容
if [ -n "$VNF_ID" ]; then
  bash "$apis_dir/07-download-package-content.sh" "$BASE_URL" "$VNF_ID" > /tmp/test_output.txt 2>&1
  if [ $? -eq 0 ]; then
    cat /tmp/test_output.txt
    ((PASSED++))
  else
    cat /tmp/test_output.txt
    ((FAILED++))
  fi
fi

# 7. 獲取 VNFD
if [ -n "$VNF_ID" ]; then
  bash "$apis_dir/08-get-vnfd.sh" "$BASE_URL" "$VNF_ID" > /tmp/test_output.txt 2>&1
  if [ $? -eq 0 ]; then
    cat /tmp/test_output.txt
    ((PASSED++))
  else
    cat /tmp/test_output.txt
    ((FAILED++))
  fi
fi

# 8. 從 URI 上傳
if [ -n "$VNF_ID" ]; then
  bash "$apis_dir/09-upload-from-uri.sh" "$BASE_URL" "$VNF_ID" > /tmp/test_output.txt 2>&1
  if [ $? -eq 0 ]; then
    cat /tmp/test_output.txt
    ((PASSED++))
  else
    cat /tmp/test_output.txt
    ((FAILED++))
  fi
fi

# 9. 獲取工件
if [ -n "$VNF_ID" ]; then
  bash "$apis_dir/10-get-artifact.sh" "$BASE_URL" "$VNF_ID" > /tmp/test_output.txt 2>&1
  if [ $? -eq 0 ]; then
    cat /tmp/test_output.txt
    ((PASSED++))
  else
    cat /tmp/test_output.txt
    ((FAILED++))
  fi
fi

# 10. 刪除 VNF 套件
if [ -n "$VNF_ID" ]; then
  bash "$apis_dir/05-delete-package.sh" "$BASE_URL" "$VNF_ID" > /tmp/test_output.txt 2>&1
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
