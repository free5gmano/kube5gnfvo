#!/bin/bash
# API: PUT /vnfpkgm/v1/vnf_packages/{id}/package_content/
# 功能: 上傳 VNF 套件內容

BASE_URL="${1:-http://localhost:8000}"
VNF_ID="${2}"

if [ -z "$VNF_ID" ]; then
  echo "⚠️  沒有提供 VNF_ID，跳過測試"
  exit 0
fi

# 建立臨時 YAML 文件
mkdir -p /tmp/vnf_package
cat > /tmp/vnf_package/vnfd.yaml << 'EOF'
tosca_definitions_version: tosca_simple_yaml_1_2
metadata:
  template_name: test-vnf
  template_version: 1.0
  template_author: test
topology_template:
  node_templates:
    VNF:
      type: tosca.nodes.nfv.VNF
      properties:
        descriptor_id: test-vnf-id
        provider: test
        product_name: test-vnf
        software_version: 1.0
        descriptor_version: 1.0
EOF

# 建立 TOSCA-Metadata
mkdir -p /tmp/vnf_package/TOSCA-Metadata
cat > /tmp/vnf_package/TOSCA-Metadata/TOSCA.meta << 'EOF'
TOSCA-Meta-File-Version: 1.0
CSAR-Version: 1.1
Created-By: test
Entry-Definitions: vnfd.yaml
ETSI-Entry-Manifest: MANIFEST.mf
EOF

# 建立 MANIFEST
cat > /tmp/vnf_package/MANIFEST.mf << 'EOF'
metadata:
  vnf_provider_id: test
  vnf_product_id: test-vnf
  vnf_release_date_time: 2024-01-01T00:00:00Z
EOF

# 建立 ZIP 文件
cd /tmp/vnf_package
zip -r /tmp/vnf_package.zip . > /dev/null 2>&1
cd - > /dev/null

# 上傳 VNF 內容
UPLOAD_RESPONSE=$(curl -s -w "\n%{http_code}" -X PUT "$BASE_URL/vnfpkgm/v1/vnf_packages/$VNF_ID/package_content/" \
  -H "X-Requested-With: XMLHttpRequest" \
  -F "file=@/tmp/vnf_package.zip")
HTTP_CODE=$(echo "$UPLOAD_RESPONSE" | tail -n1)

# 清理臨時文件
rm -rf /tmp/vnf_package /tmp/vnf_package.zip

if [ "$HTTP_CODE" = "202" ]; then
  echo "✅ PUT /vnfpkgm/v1/vnf_packages/{id}/package_content/"
  exit 0
else
  echo "❌ PUT /vnfpkgm/v1/vnf_packages/{id}/package_content/ (HTTP $HTTP_CODE)"
  exit 1
fi
