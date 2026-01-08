#!/bin/bash
# API: POST /vnfpkgm/v1/vnf_packages/
# 功能: 建立 VNF 套件

BASE_URL="${1:-http://localhost:8000}"

VNF_RESPONSE=$(curl -s -w "\n%{http_code}" -X POST "$BASE_URL/vnfpkgm/v1/vnf_packages/" \
  -H "Content-Type: application/json" \
  -d '{"userDefinedData": {}}')
HTTP_CODE=$(echo "$VNF_RESPONSE" | tail -n1)
BODY=$(echo "$VNF_RESPONSE" | head -n-1)
VNF_ID=$(echo "$BODY" | grep -o '"id":"[^"]*' | head -1 | cut -d'"' -f4)

if [ -n "$VNF_ID" ] && [ "$HTTP_CODE" = "201" ]; then
  echo "✅ POST /vnfpkgm/v1/vnf_packages/ (ID: $VNF_ID)"
  echo "$VNF_ID"
  exit 0
else
  echo "❌ POST /vnfpkgm/v1/vnf_packages/ (HTTP $HTTP_CODE)"
  echo "$BODY"
  exit 1
fi
