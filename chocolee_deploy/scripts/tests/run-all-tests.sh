#!/bin/bash

# 主測試腳本 - 運行所有服務的 API 測試

BASE_URL="${1:-http://localhost:8000}"
TOTAL_PASSED=0
TOTAL_FAILED=0

echo "🧪 開始運行所有服務測試"
echo "=================================================="
echo "基礎 URL: $BASE_URL"
echo ""

# 定義所有測試模組
MODULES=(
  "VIMManagement"
  "NSDManagement"
  "NSDSubscription"
  "NSFaultManagement"
  "NSFaultSubscription"
  "NSLCMOperationOccurrences"
  "NSLifecycleManagement"
  "NSLifecycleSubscriptions"
  "VnfPackageManagement"
  "VnfPackageSubscription"
)

# 運行每個模組的測試
for module in "${MODULES[@]}"; do
  echo ""
  echo "📦 測試模組: $module"
  echo "---"
  
  module_path="chocolee_deploy/scripts/tests/$module/apis"
  
  if [ ! -d "$module_path" ]; then
    echo "⚠️  模組目錄不存在: $module_path"
    continue
  fi
  
  # 運行該模組下的所有測試腳本
  test_files=$(find "$module_path" -name "*.sh" -type f | sort)
  
  if [ -z "$test_files" ]; then
    echo "⚠️  沒有找到測試腳本"
    continue
  fi
  
  module_passed=0
  module_failed=0
  
  for test_file in $test_files; do
    test_name=$(basename "$test_file")
    
    # 運行測試
    bash "$test_file" "$BASE_URL" > /tmp/test_output.txt 2>&1
    exit_code=$?
    
    # 讀取輸出
    output=$(cat /tmp/test_output.txt)
    
    # 檢查結果
    if [ $exit_code -eq 0 ]; then
      echo "  ✅ $test_name"
      ((module_passed++))
      ((TOTAL_PASSED++))
    else
      echo "  ❌ $test_name"
      ((module_failed++))
      ((TOTAL_FAILED++))
      # 顯示錯誤信息
      echo "     $output" | head -3
    fi
  done
  
  echo "  結果: $module_passed 通過, $module_failed 失敗"
done

# 總結
echo ""
echo "=================================================="
echo "📊 總體測試結果"
echo "=================================================="
echo "✅ 總通過: $TOTAL_PASSED"
echo "❌ 總失敗: $TOTAL_FAILED"

if [ $((TOTAL_PASSED + TOTAL_FAILED)) -gt 0 ]; then
  SUCCESS_RATE=$(( TOTAL_PASSED * 100 / (TOTAL_PASSED + TOTAL_FAILED) ))
  echo "📈 成功率: $SUCCESS_RATE%"
fi

echo ""

if [ $TOTAL_FAILED -eq 0 ]; then
  echo "🎉 所有測試通過！"
  exit 0
else
  echo "⚠️  有 $TOTAL_FAILED 個測試失敗"
  exit 1
fi
