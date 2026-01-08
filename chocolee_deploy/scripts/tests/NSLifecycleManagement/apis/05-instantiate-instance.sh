#!/bin/bash
# API: POST /nslcm/v1/ns_instances/{id}/instantiate
# 功能: 實例化 NS 實例

BASE_URL="${1:-http://localhost:8000}"
NS_ID="${2}"

if [ -z "$NS_ID" ]; then
  echo "⚠️  沒有提供 NS_ID，跳過測試"
  exit 0
fi

# 準備實例化請求數據
INSTANTIATE_DATA=$(cat <<'EOF'
{
  "flavourId": "default",
  "instantiationLevelId": "default",
  "additionalParamsForNs": {},
  "additionalParamsForVnf": []
}
EOF
)

INSTANTIATE_RESPONSE=$(curl -s -w "\n%{http_code}" -X POST "$BASE_URL/nslcm/v1/ns_instances/$NS_ID/instantiate" \
  -H "Content-Type: application/json" \
  -H "X-Requested-With: XMLHttpRequest" \
  -d "$INSTANTIATE_DATA")
HTTP_CODE=$(echo "$INSTANTIATE_RESPONSE" | tail -n1)
BODY=$(echo "$INSTANTIATE_RESPONSE" | head -n-1)

if [ "$HTTP_CODE" = "202" ]; then
  echo "✅ POST /nslcm/v1/ns_instances/{id}/instantiate"
  exit 0
else
  echo "❌ POST /nslcm/v1/ns_instances/{id}/instantiate (HTTP $HTTP_CODE)"
  echo "$BODY" | head -5
  exit 1
fi
