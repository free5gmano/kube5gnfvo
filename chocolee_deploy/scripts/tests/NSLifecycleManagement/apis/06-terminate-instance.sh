#!/bin/bash
# API: POST /nslcm/v1/ns_instances/{id}/terminate
# 功能: 終止 NS 實例

BASE_URL="${1:-http://localhost:8000}"
NS_ID="${2}"

if [ -z "$NS_ID" ]; then
  echo "⚠️  沒有提供 NS_ID，跳過測試"
  exit 0
fi

# 準備終止請求數據
TERMINATE_DATA=$(cat <<'EOF'
{
  "additionalParamsForNs": {}
}
EOF
)

TERMINATE_RESPONSE=$(curl -s -w "\n%{http_code}" -X POST "$BASE_URL/nslcm/v1/ns_instances/$NS_ID/terminate" \
  -H "Content-Type: application/json" \
  -H "X-Requested-With: XMLHttpRequest" \
  -d "$TERMINATE_DATA")
HTTP_CODE=$(echo "$TERMINATE_RESPONSE" | tail -n1)
BODY=$(echo "$TERMINATE_RESPONSE" | head -n-1)

if [ "$HTTP_CODE" = "202" ]; then
  echo "✅ POST /nslcm/v1/ns_instances/{id}/terminate"
  exit 0
else
  echo "❌ POST /nslcm/v1/ns_instances/{id}/terminate (HTTP $HTTP_CODE)"
  echo "$BODY" | head -5
  exit 1
fi
