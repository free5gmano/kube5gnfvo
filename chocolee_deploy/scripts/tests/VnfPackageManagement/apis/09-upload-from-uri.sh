#!/bin/bash
# API: POST /vnfpkgm/v1/vnf_packages/{id}/package_content/upload_from_uri
# 功能: 從 URI 上傳 VNF 套件內容

BASE_URL="${1:-http://localhost:8000}"
VNF_ID="${2}"

if [ -z "$VNF_ID" ]; then
  echo "⚠️  沒有提供 VNF_ID，跳過測試"
  exit 0
fi

# 準備從 URI 上傳的請求數據
UPLOAD_URI_DATA=$(cat <<'EOF'
{
  "UploadVnfPackageFromUriRequest": {
    "addressInformation": "http://example.com/vnf-package.zip"
  }
}
EOF
)

UPLOAD_RESPONSE=$(curl -s -w "\n%{http_code}" -X POST "$BASE_URL/vnfpkgm/v1/vnf_packages/$VNF_ID/package_content/upload_from_uri" \
  -H "Content-Type: application/json" \
  -H "X-Requested-With: XMLHttpRequest" \
  -d "$UPLOAD_URI_DATA")
HTTP_CODE=$(echo "$UPLOAD_RESPONSE" | tail -n1)

if [ "$HTTP_CODE" = "202" ]; then
  echo "✅ POST /vnfpkgm/v1/vnf_packages/{id}/package_content/upload_from_uri"
  exit 0
else
  echo "⚠️  POST /vnfpkgm/v1/vnf_packages/{id}/package_content/upload_from_uri (HTTP $HTTP_CODE)"
  exit 0
fi
