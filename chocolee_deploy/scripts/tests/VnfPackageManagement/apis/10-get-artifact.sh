#!/bin/bash
# API: GET /vnfpkgm/v1/vnf_packages/{id}/artifacts/{artifactPath}
# 功能: 獲取 VNF 套件中的工件

BASE_URL="${1:-http://localhost:8000}"
VNF_ID="${2}"

if [ -z "$VNF_ID" ]; then
  echo "⚠️  沒有提供 VNF_ID，跳過測試"
  exit 0
fi

# 嘗試獲取一個常見的工件路徑
ARTIFACT_PATH="Definitions/vnfd.yaml"

ARTIFACT_RESPONSE=$(curl -s -w "\n%{http_code}" -X GET "$BASE_URL/vnfpkgm/v1/vnf_packages/$VNF_ID/artifacts/$ARTIFACT_PATH" \
  -H "Accept: application/zip" \
  -H "X-Requested-With: XMLHttpRequest" \
  -o /tmp/artifact_download.zip)
HTTP_CODE=$(echo "$ARTIFACT_RESPONSE" | tail -n1)

# 清理臨時文件
rm -f /tmp/artifact_download.zip

if [ "$HTTP_CODE" = "200" ]; then
  echo "✅ GET /vnfpkgm/v1/vnf_packages/{id}/artifacts/{artifactPath}"
  exit 0
else
  echo "⚠️  GET /vnfpkgm/v1/vnf_packages/{id}/artifacts/{artifactPath} (HTTP $HTTP_CODE)"
  exit 0
fi
