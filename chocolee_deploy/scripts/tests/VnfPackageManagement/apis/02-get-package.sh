#!/bin/bash
# API: GET /vnfpkgm/v1/vnf_packages/{id}/
# 功能: 查詢單個 VNF 套件

BASE_URL="${1:-http://localhost:8000}"
VNF_ID="${2}"

if [ -z "$VNF_ID" ]; then
  echo "⚠️  沒有提供 VNF_ID，跳過測試"
  exit 0
fi

GET_RESPONSE=$(curl -s -w "\n%{http_code}" -X GET "$BASE_URL/vnfpkgm/v1/vnf_packages/$VNF_ID/")
HTTP_CODE=$(echo "$GET_RESPONSE" | tail -n1)

if [ "$HTTP_CODE" = "200" ]; then
  echo "✅ GET /vnfpkgm/v1/vnf_packages/{id}/"
  exit 0
else
  echo "❌ GET /vnfpkgm/v1/vnf_packages/{id}/ (HTTP $HTTP_CODE)"
  exit 1
fi
