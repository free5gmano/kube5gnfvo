#!/bin/bash
# API: GET /vimm/v1/kubernetes
# 功能: 查詢 Kubernetes 資源

BASE_URL="${1:-http://localhost:8000}"

GET_RESPONSE=$(curl -s -w "\n%{http_code}" -X GET "$BASE_URL/vimm/v1/kubernetes")
HTTP_CODE=$(echo "$GET_RESPONSE" | tail -n1)
BODY=$(echo "$GET_RESPONSE" | head -n-1)

if [ "$HTTP_CODE" = "200" ]; then
  COUNT=$(echo "$BODY" | grep -o '"cpu_request"' | wc -l)
  echo "✅ GET /vimm/v1/kubernetes (找到 $COUNT 個資源)"
  exit 0
else
  echo "❌ GET /vimm/v1/kubernetes (HTTP $HTTP_CODE)"
  echo "$BODY"
  exit 1
fi
