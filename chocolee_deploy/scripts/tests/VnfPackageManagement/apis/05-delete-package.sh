#!/bin/bash
# API: DELETE /vnfpkgm/v1/vnf_packages/{id}/
# 功能: 刪除 VNF 套件

BASE_URL="${1:-http://localhost:8000}"
VNF_ID="${2}"

if [ -z "$VNF_ID" ]; then
  echo "⚠️  沒有提供 VNF_ID，跳過測試"
  exit 0
fi

DELETE_RESPONSE=$(curl -s -w "\n%{http_code}" -X DELETE "$BASE_URL/vnfpkgm/v1/vnf_packages/$VNF_ID/")
HTTP_CODE=$(echo "$DELETE_RESPONSE" | tail -n1)

if [ "$HTTP_CODE" = "204" ] || [ "$HTTP_CODE" = "200" ]; then
  echo "✅ DELETE /vnfpkgm/v1/vnf_packages/{id}/"
  exit 0
else
  echo "❌ DELETE /vnfpkgm/v1/vnf_packages/{id}/ (HTTP $HTTP_CODE)"
  exit 1
fi
