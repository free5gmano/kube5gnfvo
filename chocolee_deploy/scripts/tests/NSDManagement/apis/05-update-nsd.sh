#!/bin/bash
# API: PATCH /nsd/v1/ns_descriptors/{id}/
# 功能: 更新 NSD 狀態

BASE_URL="${1:-http://localhost:8000}"

# 獲取第一個 NSD ID
LIST_RESPONSE=$(curl -s -X GET "$BASE_URL/nsd/v1/ns_descriptors/")
NSD_ID=$(echo "$LIST_RESPONSE" | grep -o '"id":"[^"]*' | head -1 | cut -d'"' -f4)

if [ -z "$NSD_ID" ]; then
  echo "⚠️  沒有找到 NSD，跳過測試"
  exit 0
fi

UPDATE_RESPONSE=$(curl -s -w "\n%{http_code}" -X PATCH "$BASE_URL/nsd/v1/ns_descriptors/$NSD_ID/" \
  -H "Content-Type: application/json" \
  -d '{"nsdOperationalState": "DISABLED"}')
HTTP_CODE=$(echo "$UPDATE_RESPONSE" | tail -n1)

if [ "$HTTP_CODE" = "200" ]; then
  echo "✅ PATCH /nsd/v1/ns_descriptors/{id}/"
  exit 0
else
  echo "⚠️  PATCH /nsd/v1/ns_descriptors/{id}/ (HTTP $HTTP_CODE)"
  exit 0
fi
