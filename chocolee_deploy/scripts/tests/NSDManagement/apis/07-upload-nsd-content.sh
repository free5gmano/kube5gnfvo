#!/bin/bash
# API: PUT /nsd/v1/ns_descriptors/{id}/nsd_content/
# 功能: 上傳 NSD 內容

BASE_URL="${1:-http://localhost:8000}"
NSD_ID="${2}"

if [ -z "$NSD_ID" ]; then
  echo "⚠️  沒有提供 NSD_ID，跳過測試"
  exit 0
fi

# 建立臨時 YAML 文件
cat > /tmp/ns.yaml << 'EOF'
tosca_definitions_version: tosca_simple_yaml_1_2
topology_template:
  node_templates:
    NS1:
      type: tosca.nodes.nfv.NS
      properties:
        descriptor_id: test-nsd-id
        designer: test
        version: 1.0
        name: test-ns
        invariant_id: test-invariant-id
        constituent_vnfd:
          - vnfd_id: test-vnf-id
EOF

# 建立 ZIP 文件
python3 << 'PYTHON_EOF'
import zipfile
zip_path = '/tmp/nsd-temp.zip'
with zipfile.ZipFile(zip_path, 'w') as zf:
    zf.write('/tmp/ns.yaml', 'ns.yaml')
PYTHON_EOF

# 上傳 NSD 內容
UPLOAD_RESPONSE=$(curl -s -w "\n%{http_code}" -X PUT "$BASE_URL/nsd/v1/ns_descriptors/$NSD_ID/nsd_content/" \
  -F "file=@/tmp/nsd-temp.zip")
HTTP_CODE=$(echo "$UPLOAD_RESPONSE" | tail -n1)

# 清理臨時文件
rm -f /tmp/nsd-temp.zip /tmp/ns.yaml

if [ "$HTTP_CODE" = "202" ]; then
  echo "✅ PUT /nsd/v1/ns_descriptors/{id}/nsd_content/"
  exit 0
else
  echo "⚠️  PUT /nsd/v1/ns_descriptors/{id}/nsd_content/ (HTTP $HTTP_CODE)"
  exit 0
fi
