#!/bin/bash
# API: GET /nsfm/v1/alarms/
# 功能: 查詢告警列表

BASE_URL="${1:-http://localhost:8000}"

LIST_RESPONSE=$(curl -s -w "\n%{http_code}" -X GET "$BASE_URL/nsfm/v1/alarms/")
HTTP_CODE=$(echo "$LIST_RESPONSE" | tail -n1)
BODY=$(echo "$LIST_RESPONSE" | head -n-1)

if [ "$HTTP_CODE" = "200" ]; then
  COUNT=$(echo "$BODY" | grep -o '"id"' | wc -l)
  echo "✅ GET /nsfm/v1/alarms/ (找到 $COUNT 個告警)"
  exit 0
else
  echo "❌ GET /nsfm/v1/alarms/ (HTTP $HTTP_CODE)"
  exit 1
fi
