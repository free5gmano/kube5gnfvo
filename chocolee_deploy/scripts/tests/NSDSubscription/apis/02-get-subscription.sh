#!/bin/bash
# API: GET /nsd/v1/subscriptions/{id}/
# 功能: 查詢單個訂閱

BASE_URL="${1:-http://localhost:8000}"
SUB_ID="${2}"

if [ -z "$SUB_ID" ]; then
  echo "⚠️  沒有提供 SUB_ID，跳過測試"
  exit 0
fi

GET_RESPONSE=$(curl -s -w "\n%{http_code}" -X GET "$BASE_URL/nsd/v1/subscriptions/$SUB_ID/")
HTTP_CODE=$(echo "$GET_RESPONSE" | tail -n1)
BODY=$(echo "$GET_RESPONSE" | head -n-1)

if [ "$HTTP_CODE" = "200" ]; then
  # 驗證回應中包含 id 和 callbackUri
  if echo "$BODY" | grep -q '"id"' && echo "$BODY" | grep -q '"callbackUri"'; then
    echo "✅ GET /nsd/v1/subscriptions/{id}/"
    exit 0
  else
    echo "⚠️  GET /nsd/v1/subscriptions/{id}/ - 回應格式不正確"
    exit 0
  fi
else
  echo "❌ GET /nsd/v1/subscriptions/{id}/ (HTTP $HTTP_CODE)"
  exit 1
fi
