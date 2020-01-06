# All Rights Reserved.
#
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

import uuid

from utils.file_manipulation import sha256_hash
from utils.process_package.base_package import BasePackage


class PackageVNFInstance(BasePackage):

    def __init__(self, path=None):
        super().__init__(path)
        self.artifacts_hash = 'SHA-256'

    def processing_data(self) -> dict:
        node_templates = self.topology_template.node_templates
        vdu_list = list()
        for node_template in node_templates:
            if 'tosca.nodes.nfv.Vdu.Compute' in node_template.get_type():
                vdu_list.append(node_template)

        software_images = self.get_software_images(vdu_list)

        result = {'vnfdId': str(uuid.uuid4()),
                  'vnfProvider': self.tosca_metadata['Created-By'],
                  'vnfProductName': self.entry_manifest['vnf_product_name'],
                  'vnfdVersion': self.entry_manifest['vnf_package_version'],
                  'checksum': {'algorithm': 'SHA-256', 'hash': sha256_hash(self.root_path + self.entry_definitions)},
                  'softwareImages': software_images,
                  'vnfSoftwareVersion': software_images[0]['version']}
        if 'ETSI-Entry-Artifacts' in self.tosca_metadata:
            result['additionalArtifacts'] = self.get_additional_artifacts(
                self.root_path, self.tosca_metadata['ETSI-Entry-Artifacts'])
        return result

    def get_additional_artifacts(self, base_path, artifacts_path) -> list:
        return [self.get_artifacts_value(_.strip(), self.artifacts_hash, sha256_hash(base_path + _.strip()))
                for _ in artifacts_path.split(',')]

    def get_artifacts_value(self, path, algorithm, _hash) -> dict:
        return {'artifactPath': path,
                'checksum': {'algorithm': algorithm,
                             'hash': _hash}}

    # image kind: provide/image_name:version
    # example: ubuntu:16.04, free5gmano/free5gc-base:latest
    def get_software_images(self, vdu_list: list) -> list:
        software_images = list()
        for vdu in vdu_list:
            image_info = vdu.image.split('/')
            if len(image_info) > 1:
                provider = image_info[0]
                provider_with_version = image_info[1].split(':')
            else:
                provider = str()
                provider_with_version = image_info[0].split(':')

            software_images.append(
                {'provider': provider,
                 'name': provider_with_version[0],
                 'version': provider_with_version[1] if len(provider_with_version) > 1 else 'latest',
                 'minRam': vdu.virtual_mem_size,
                 'diskFormat': 'RAW'})
        return software_images
