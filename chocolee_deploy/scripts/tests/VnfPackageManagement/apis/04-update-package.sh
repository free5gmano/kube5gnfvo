#!/bin/bash
# API: PATCH /vnfpkgm/v1/vnf_packages/{id}/
# 功能: 更新 VNF 套件狀態

BASE_URL="${1:-http://localhost:8000}"
VNF_ID="${2}"

if [ -z "$VNF_ID" ]; then
  echo "⚠️  沒有提供 VNF_ID，跳過測試"
  exit 0
fi

UPDATE_RESPONSE=$(curl -s -w "\n%{http_code}" -X PATCH "$BASE_URL/vnfpkgm/v1/vnf_packages/$VNF_ID/" \
  -H "Content-Type: application/json" \
  -H "X-Requested-With: XMLHttpRequest" \
  -d '{"operationalState": "DISABLED"}')
HTTP_CODE=$(echo "$UPDATE_RESPONSE" | tail -n1)
BODY=$(echo "$UPDATE_RESPONSE" | head -n-1)

if [ "$HTTP_CODE" = "200" ]; then
  echo "✅ PATCH /vnfpkgm/v1/vnf_packages/{id}/"
  exit 0
else
  echo "❌ PATCH /vnfpkgm/v1/vnf_packages/{id}/ (HTTP $HTTP_CODE)"
  echo "$BODY" | head -20
  exit 1
fi
