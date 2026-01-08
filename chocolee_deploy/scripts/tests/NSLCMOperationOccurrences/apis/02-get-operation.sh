#!/bin/bash
# API: GET /nslcm/v1/ns_lcm_op_occs/{id}/
# 功能: 查詢單個 LCM 操作

BASE_URL="${1:-http://localhost:8000}"
OP_ID="${2}"

if [ -z "$OP_ID" ]; then
  echo "⚠️  沒有提供 OP_ID，跳過測試"
  exit 0
fi

GET_RESPONSE=$(curl -s -w "\n%{http_code}" -X GET "$BASE_URL/nslcm/v1/ns_lcm_op_occs/$OP_ID/")
HTTP_CODE=$(echo "$GET_RESPONSE" | tail -n1)

if [ "$HTTP_CODE" = "200" ]; then
  echo "✅ GET /nslcm/v1/ns_lcm_op_occs/{id}/"
  exit 0
else
  echo "❌ GET /nslcm/v1/ns_lcm_op_occs/{id}/ (HTTP $HTTP_CODE)"
  exit 1
fi
