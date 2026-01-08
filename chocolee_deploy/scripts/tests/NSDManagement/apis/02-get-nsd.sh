#!/bin/bash
# API: GET /nsd/v1/ns_descriptors/{id}/
# 功能: 查詢單個 NSD

BASE_URL="${1:-http://localhost:8000}"

# 獲取第一個 NSD ID
LIST_RESPONSE=$(curl -s -X GET "$BASE_URL/nsd/v1/ns_descriptors/")
NSD_ID=$(echo $LIST_RESPONSE | grep -o '"id":"[^"]*' | head -1 | cut -d'"' -f4)

if [ -z "$NSD_ID" ]; then
  echo "⚠️  沒有找到 NSD"
  exit 0
fi

GET_RESPONSE=$(curl -s -w "\n%{http_code}" -X GET "$BASE_URL/nsd/v1/ns_descriptors/$NSD_ID/")
HTTP_CODE=$(echo "$GET_RESPONSE" | tail -n1)

if [ "$HTTP_CODE" = "200" ]; then
  echo "✅ GET /nsd/v1/ns_descriptors/{id}/"
  exit 0
else
  echo "❌ GET /nsd/v1/ns_descriptors/{id}/ (HTTP $HTTP_CODE)"
  exit 1
fi
