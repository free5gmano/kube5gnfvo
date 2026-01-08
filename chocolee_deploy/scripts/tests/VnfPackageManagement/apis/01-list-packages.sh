#!/bin/bash
# API: GET /vnfpkgm/v1/vnf_packages/
# 功能: 查詢 VNF 套件列表

BASE_URL="${1:-http://localhost:8000}"

LIST_RESPONSE=$(curl -s -w "\n%{http_code}" -X GET "$BASE_URL/vnfpkgm/v1/vnf_packages/")
HTTP_CODE=$(echo "$LIST_RESPONSE" | tail -n1)
BODY=$(echo "$LIST_RESPONSE" | head -n-1)

if [ "$HTTP_CODE" = "200" ]; then
  COUNT=$(echo "$BODY" | grep -o '"id"' | wc -l)
  echo "✅ GET /vnfpkgm/v1/vnf_packages/ (找到 $COUNT 個套件)"
  exit 0
elif [ "$HTTP_CODE" = "409" ]; then
  echo "⚠️  GET /vnfpkgm/v1/vnf_packages/ - 沒有 VNF 套件資源 (HTTP $HTTP_CODE)"
  exit 0
else
  echo "❌ GET /vnfpkgm/v1/vnf_packages/ (HTTP $HTTP_CODE)"
  exit 1
fi
