#!/bin/bash
# API: DELETE /nsd/v1/ns_descriptors/{id}/
# 功能: 刪除 NSD

BASE_URL="${1:-http://localhost:8000}"
NSD_ID="${2}"

if [ -z "$NSD_ID" ]; then
  echo "⚠️  沒有提供 NSD_ID，跳過測試"
  exit 0
fi

DELETE_RESPONSE=$(curl -s -w "\n%{http_code}" -X DELETE "$BASE_URL/nsd/v1/ns_descriptors/$NSD_ID/")
HTTP_CODE=$(echo "$DELETE_RESPONSE" | tail -n1)

if [ "$HTTP_CODE" = "204" ] || [ "$HTTP_CODE" = "200" ]; then
  echo "✅ DELETE /nsd/v1/ns_descriptors/{id}/"
  exit 0
else
  echo "❌ DELETE /nsd/v1/ns_descriptors/{id}/ (HTTP $HTTP_CODE)"
  exit 1
fi
