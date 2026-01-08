#!/bin/bash
# API: GET /nslcm/v1/ns_lcm_op_occs/
# 功能: 查詢 LCM 操作列表

BASE_URL="${1:-http://localhost:8000}"

LIST_RESPONSE=$(curl -s -w "\n%{http_code}" -X GET "$BASE_URL/nslcm/v1/ns_lcm_op_occs/")
HTTP_CODE=$(echo "$LIST_RESPONSE" | tail -n1)
BODY=$(echo "$LIST_RESPONSE" | head -n-1)

if [ "$HTTP_CODE" = "200" ]; then
  COUNT=$(echo "$BODY" | grep -o '"id"' | wc -l)
  echo "✅ GET /nslcm/v1/ns_lcm_op_occs/ (找到 $COUNT 個操作)"
  exit 0
else
  echo "❌ GET /nslcm/v1/ns_lcm_op_occs/ (HTTP $HTTP_CODE)"
  exit 1
fi
