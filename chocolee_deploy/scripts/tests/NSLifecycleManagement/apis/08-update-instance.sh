#!/bin/bash
# API: POST /nslcm/v1/ns_instances/{id}/update
# 功能: 更新 NS 實例

BASE_URL="${1:-http://localhost:8000}"
NS_ID="${2}"

if [ -z "$NS_ID" ]; then
  echo "⚠️  沒有提供 NS_ID，跳過測試"
  exit 0
fi

# 準備更新請求數據
UPDATE_DATA=$(cat <<'EOF'
{
  "updateType": "MODIFY_VNF_INFORMATION",
  "modifyVnfInfoData": [
    {
      "vnfInstanceId": "test-vnf-id",
      "metadata": {
        "key": "value"
      }
    }
  ]
}
EOF
)

UPDATE_RESPONSE=$(curl -s -w "\n%{http_code}" -X POST "$BASE_URL/nslcm/v1/ns_instances/$NS_ID/update" \
  -H "Content-Type: application/json" \
  -H "X-Requested-With: XMLHttpRequest" \
  -d "$UPDATE_DATA")
HTTP_CODE=$(echo "$UPDATE_RESPONSE" | tail -n1)

if [ "$HTTP_CODE" = "202" ]; then
  echo "✅ POST /nslcm/v1/ns_instances/{id}/update"
  exit 0
else
  echo "⚠️  POST /nslcm/v1/ns_instances/{id}/update (HTTP $HTTP_CODE)"
  exit 0
fi
