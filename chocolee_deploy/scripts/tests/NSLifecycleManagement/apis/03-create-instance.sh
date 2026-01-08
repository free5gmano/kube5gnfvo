#!/bin/bash
# API: POST /nslcm/v1/ns_instances/
# 功能: 建立 NS Instance

BASE_URL="${1:-http://localhost:8000}"
NSD_ID="${2}"

if [ -z "$NSD_ID" ]; then
  echo "⚠️  沒有提供 NSD_ID，跳過測試"
  exit 0
fi

NS_RESPONSE=$(curl -s -w "\n%{http_code}" -X POST "$BASE_URL/nslcm/v1/ns_instances/" \
  -H "Content-Type: application/json" \
  -d "{\"nsdId\": \"$NSD_ID\", \"nsName\": \"test-ns-$(date +%s)\", \"nsDescription\": \"Test NS Instance\"}")
HTTP_CODE=$(echo "$NS_RESPONSE" | tail -n1)
BODY=$(echo "$NS_RESPONSE" | head -n-1)
NS_ID=$(echo "$BODY" | grep -o '"id":"[^"]*' | head -1 | cut -d'"' -f4)

if [ -n "$NS_ID" ] && [ "$HTTP_CODE" = "201" ]; then
  echo "✅ POST /nslcm/v1/ns_instances/ (ID: $NS_ID)"
  echo "$NS_ID"
  exit 0
else
  echo "❌ POST /nslcm/v1/ns_instances/ (HTTP $HTTP_CODE)"
  echo "$BODY"
  exit 1
fi
