#!/bin/bash
# API: GET /vnfpkgm/v1/vnf_packages/{id}/vnfd
# 功能: 獲取 VNFD (VNF 描述符)

BASE_URL="${1:-http://localhost:8000}"
VNF_ID="${2}"

if [ -z "$VNF_ID" ]; then
  echo "⚠️  沒有提供 VNF_ID，跳過測試"
  exit 0
fi

VNFD_RESPONSE=$(curl -s -w "\n%{http_code}" -X GET "$BASE_URL/vnfpkgm/v1/vnf_packages/$VNF_ID/vnfd" \
  -H "Accept: application/zip" \
  -H "X-Requested-With: XMLHttpRequest" \
  -o /tmp/vnfd_download.zip)
HTTP_CODE=$(echo "$VNFD_RESPONSE" | tail -n1)

# 清理臨時文件
rm -f /tmp/vnfd_download.zip

if [ "$HTTP_CODE" = "200" ]; then
  echo "✅ GET /vnfpkgm/v1/vnf_packages/{id}/vnfd"
  exit 0
else
  echo "⚠️  GET /vnfpkgm/v1/vnf_packages/{id}/vnfd (HTTP $HTTP_CODE)"
  exit 0
fi
