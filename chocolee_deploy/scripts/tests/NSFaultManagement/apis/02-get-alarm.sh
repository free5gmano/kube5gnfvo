#!/bin/bash
# API: GET /nsfm/v1/alarms/{id}/
# 功能: 查詢單個告警

BASE_URL="${1:-http://localhost:8000}"
ALARM_ID="${2}"

if [ -z "$ALARM_ID" ]; then
  echo "⚠️  沒有提供 ALARM_ID，跳過測試"
  exit 0
fi

GET_RESPONSE=$(curl -s -w "\n%{http_code}" -X GET "$BASE_URL/nsfm/v1/alarms/$ALARM_ID/")
HTTP_CODE=$(echo "$GET_RESPONSE" | tail -n1)

if [ "$HTTP_CODE" = "200" ]; then
  echo "✅ GET /nsfm/v1/alarms/{id}/"
  exit 0
else
  echo "❌ GET /nsfm/v1/alarms/{id}/ (HTTP $HTTP_CODE)"
  exit 1
fi
