#!/bin/bash
# API: GET /vnfpkgm/v1/vnf_packages/{id}/package_content/
# 功能: 下載 VNF 套件內容

BASE_URL="${1:-http://localhost:8000}"
VNF_ID="${2}"

if [ -z "$VNF_ID" ]; then
  echo "⚠️  沒有提供 VNF_ID，跳過測試"
  exit 0
fi

DOWNLOAD_RESPONSE=$(curl -s -w "\n%{http_code}" -X GET "$BASE_URL/vnfpkgm/v1/vnf_packages/$VNF_ID/package_content/" \
  -H "Accept: application/zip" \
  -H "X-Requested-With: XMLHttpRequest" \
  -o /tmp/vnf_download.zip)
HTTP_CODE=$(echo "$DOWNLOAD_RESPONSE" | tail -n1)

# 清理臨時文件
rm -f /tmp/vnf_download.zip

if [ "$HTTP_CODE" = "200" ]; then
  echo "✅ GET /vnfpkgm/v1/vnf_packages/{id}/package_content/"
  exit 0
else
  echo "❌ GET /vnfpkgm/v1/vnf_packages/{id}/package_content/ (HTTP $HTTP_CODE)"
  exit 1
fi
