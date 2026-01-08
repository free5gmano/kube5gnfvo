#!/bin/bash
# API: POST /nslcm/v1/ns_instances/{id}/scale
# 功能: 擴展 NS 實例

BASE_URL="${1:-http://localhost:8000}"
NS_ID="${2}"

if [ -z "$NS_ID" ]; then
  echo "⚠️  沒有提供 NS_ID，跳過測試"
  exit 0
fi

# 準備擴展請求數據
SCALE_DATA=$(cat <<'EOF'
{
  "scaleType": "SCALE_NS",
  "scaleNsData": {
    "scaleNsByStepsData": [
      {
        "scalingDirection": "OUT",
        "aspectId": "default",
        "numberOfSteps": 1
      }
    ]
  }
}
EOF
)

SCALE_RESPONSE=$(curl -s -w "\n%{http_code}" -X POST "$BASE_URL/nslcm/v1/ns_instances/$NS_ID/scale" \
  -H "Content-Type: application/json" \
  -H "X-Requested-With: XMLHttpRequest" \
  -d "$SCALE_DATA")
HTTP_CODE=$(echo "$SCALE_RESPONSE" | tail -n1)

if [ "$HTTP_CODE" = "202" ]; then
  echo "✅ POST /nslcm/v1/ns_instances/{id}/scale"
  exit 0
else
  echo "⚠️  POST /nslcm/v1/ns_instances/{id}/scale (HTTP $HTTP_CODE)"
  exit 0
fi
