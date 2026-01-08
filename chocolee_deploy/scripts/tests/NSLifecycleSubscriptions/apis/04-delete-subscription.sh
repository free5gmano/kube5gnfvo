#!/bin/bash
# API: DELETE /nslcm/v1/subscriptions/{id}/
# 功能: 刪除訂閱

BASE_URL="${1:-http://localhost:8000}"
SUB_ID="${2}"

if [ -z "$SUB_ID" ]; then
  echo "⚠️  沒有提供 SUB_ID，跳過測試"
  exit 0
fi

DELETE_RESPONSE=$(curl -s -w "\n%{http_code}" -X DELETE "$BASE_URL/nslcm/v1/subscriptions/$SUB_ID/")
HTTP_CODE=$(echo "$DELETE_RESPONSE" | tail -n1)

if [ "$HTTP_CODE" = "204" ] || [ "$HTTP_CODE" = "200" ]; then
  echo "✅ DELETE /nslcm/v1/subscriptions/{id}/"
  exit 0
else
  echo "❌ DELETE /nslcm/v1/subscriptions/{id}/ (HTTP $HTTP_CODE)"
  exit 1
fi
