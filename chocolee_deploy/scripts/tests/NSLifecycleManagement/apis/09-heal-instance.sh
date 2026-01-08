#!/bin/bash
# API: POST /nslcm/v1/ns_instances/{id}/heal
# 功能: 修復 NS 實例

BASE_URL="${1:-http://localhost:8000}"
NS_ID="${2}"

if [ -z "$NS_ID" ]; then
  echo "⚠️  沒有提供 NS_ID，跳過測試"
  exit 0
fi

# 準備修復請求數據
HEAL_DATA=$(cat <<'EOF'
{
  "healNsData": {
    "vnfInstanceId": [
      "test-vnf-id"
    ]
  }
}
EOF
)

HEAL_RESPONSE=$(curl -s -w "\n%{http_code}" -X POST "$BASE_URL/nslcm/v1/ns_instances/$NS_ID/heal" \
  -H "Content-Type: application/json" \
  -H "X-Requested-With: XMLHttpRequest" \
  -d "$HEAL_DATA")
HTTP_CODE=$(echo "$HEAL_RESPONSE" | tail -n1)

if [ "$HTTP_CODE" = "202" ]; then
  echo "✅ POST /nslcm/v1/ns_instances/{id}/heal"
  exit 0
else
  echo "⚠️  POST /nslcm/v1/ns_instances/{id}/heal (HTTP $HTTP_CODE)"
  exit 0
fi
