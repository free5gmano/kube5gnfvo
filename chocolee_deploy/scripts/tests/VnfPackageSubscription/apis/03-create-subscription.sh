#!/bin/bash
# API: POST /vnfpkgm/v1/subscriptions/
# 功能: 建立訂閱

BASE_URL="${1:-http://localhost:8000}"
VNF_ID="${2}"

if [ -z "$VNF_ID" ]; then
  echo "⚠️  沒有提供 VNF_ID，跳過測試"
  exit 0
fi

SUB_RESPONSE=$(curl -s -w "\n%{http_code}" -X POST "$BASE_URL/vnfpkgm/v1/subscriptions/" \
  -H "Content-Type: application/json" \
  -d "{\"callbackUri\": \"http://localhost:9000/vnfpkg-notifications\", \"filter\": {\"vnfPkgId\": [\"$VNF_ID\"]}}")
HTTP_CODE=$(echo "$SUB_RESPONSE" | tail -n1)
BODY=$(echo "$SUB_RESPONSE" | head -n-1)
SUB_ID=$(echo "$BODY" | grep -o '"id":"[^"]*' | head -1 | cut -d'"' -f4)

if [ -n "$SUB_ID" ] && [ "$HTTP_CODE" = "201" ]; then
  echo "✅ POST /vnfpkgm/v1/subscriptions/ (ID: $SUB_ID)"
  echo "$SUB_ID"
  exit 0
else
  echo "❌ POST /vnfpkgm/v1/subscriptions/ (HTTP $HTTP_CODE)"
  echo "$BODY"
  exit 1
fi
