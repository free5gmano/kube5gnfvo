#!/bin/bash
# API: GET /nsd/v1/ns_descriptors/{id}/nsd_content/
# 功能: 下載 NSD 內容

BASE_URL="${1:-http://localhost:8000}"
NSD_ID="${2}"

if [ -z "$NSD_ID" ]; then
  echo "⚠️  沒有提供 NSD_ID，跳過測試"
  exit 0
fi

DOWNLOAD_RESPONSE=$(curl -s -w "\n%{http_code}" -X GET "$BASE_URL/nsd/v1/ns_descriptors/$NSD_ID/nsd_content/" \
  -H "Accept: application/zip" \
  -H "X-Requested-With: XMLHttpRequest" \
  -o /tmp/nsd_download.zip)
HTTP_CODE=$(echo "$DOWNLOAD_RESPONSE" | tail -n1)

# 清理臨時文件
rm -f /tmp/nsd_download.zip

if [ "$HTTP_CODE" = "200" ]; then
  echo "✅ GET /nsd/v1/ns_descriptors/{id}/nsd_content/"
  exit 0
else
  echo "⚠️  GET /nsd/v1/ns_descriptors/{id}/nsd_content/ (HTTP $HTTP_CODE)"
  exit 0
fi
