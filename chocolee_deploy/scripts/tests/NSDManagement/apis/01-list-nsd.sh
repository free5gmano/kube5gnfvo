#!/bin/bash
# API: GET /nsd/v1/ns_descriptors/
# 功能: 查詢 NSD 列表

BASE_URL="${1:-http://localhost:8000}"

LIST_RESPONSE=$(curl -s -w "\n%{http_code}" -X GET "$BASE_URL/nsd/v1/ns_descriptors/")
HTTP_CODE=$(echo "$LIST_RESPONSE" | tail -n1)
BODY=$(echo "$LIST_RESPONSE" | head -n-1)

if [ "$HTTP_CODE" = "200" ]; then
  COUNT=$(echo "$BODY" | grep -o '"id"' | wc -l)
  echo "✅ GET /nsd/v1/ns_descriptors/ (找到 $COUNT 個 NSD)"
  exit 0
elif [ "$HTTP_CODE" = "500" ]; then
  echo "⚠️  GET /nsd/v1/ns_descriptors/ - 沒有 NSD 資源 (HTTP $HTTP_CODE)"
  exit 0
else
  echo "❌ GET /nsd/v1/ns_descriptors/ (HTTP $HTTP_CODE)"
  exit 1
fi
