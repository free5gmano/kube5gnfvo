#!/bin/bash
# API: POST /nsd/v1/ns_descriptors/
# 功能: 建立 NSD

BASE_URL="${1:-http://localhost:8000}"

NSD_RESPONSE=$(curl -s -w "\n%{http_code}" -X POST "$BASE_URL/nsd/v1/ns_descriptors/" \
  -H "Content-Type: application/json" \
  -d "{\"nsdId\": \"test-nsd-$(date +%s)\", \"nsdName\": \"test-nsd\", \"nsdVersion\": \"1.0\"}")
HTTP_CODE=$(echo "$NSD_RESPONSE" | tail -n1)
BODY=$(echo "$NSD_RESPONSE" | head -n-1)
NSD_ID=$(echo "$BODY" | grep -o '"id":"[^"]*' | head -1 | cut -d'"' -f4)

if [ -n "$NSD_ID" ] && [ "$HTTP_CODE" = "201" ]; then
  echo "✅ POST /nsd/v1/ns_descriptors/ (ID: $NSD_ID)"
  echo "$NSD_ID"
  exit 0
else
  echo "❌ POST /nsd/v1/ns_descriptors/ (HTTP $HTTP_CODE)"
  echo "$BODY"
  exit 1
fi
