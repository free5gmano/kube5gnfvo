#!/bin/bash
# API: PATCH /nsfm/v1/alarms/{id}/
# 功能: 確認告警

BASE_URL="${1:-http://localhost:8000}"
ALARM_ID="${2}"

if [ -z "$ALARM_ID" ]; then
  echo "⚠️  沒有提供 ALARM_ID，跳過測試"
  exit 0
fi

UPDATE_RESPONSE=$(curl -s -w "\n%{http_code}" -X PATCH "$BASE_URL/nsfm/v1/alarms/$ALARM_ID/" \
  -H "Content-Type: application/json" \
  -d '{"AlarmModifications": {"ackState": "ACKNOWLEDGED"}}')
HTTP_CODE=$(echo "$UPDATE_RESPONSE" | tail -n1)

if [ "$HTTP_CODE" = "200" ]; then
  echo "✅ PATCH /nsfm/v1/alarms/{id}/"
  exit 0
else
  echo "❌ PATCH /nsfm/v1/alarms/{id}/ (HTTP $HTTP_CODE)"
  exit 1
fi
