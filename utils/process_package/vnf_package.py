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
from utils.file_manipulation import sha256_hash
from utils.process_package.base_package import BasePackage


class PackageVNF(BasePackage):

    def __init__(self, path=None):
        super().__init__(path)
        self.artifacts_hash = 'SHA-256'
        node_templates = self.topology_template.node_templates
        self.vdu = node_templates.vdu[0]
        self.vnf = node_templates.vnf[0]

    def processing_data(self) -> dict:
        result = {'vnfdId': self.vnf.properties['descriptor_id'],
                  'vnfProvider': self.vnf.properties['provider'],
                  'vnfProductName': self.vnf.properties['product_name'],
                  'vnfdVersion': self.vnf.properties['software_version'],
                  'checksum': {'algorithm': 'SHA-256', 'hash': sha256_hash(self.root_path + self.entry_definitions)},
                  'softwareImages': self._get_software_images(),
                  'vnfSoftwareVersion': self.vdu.properties['version'],
                  'additionalArtifacts': self._get_additional_artifacts()}

        return result

    def _get_additional_artifacts(self) -> list:
        if self.vdu.artifacts:
            additional_artifacts = list()
            for artifact_name in self.vdu.artifacts:
                artifact = self.vdu.artifacts[artifact_name]
                if artifact['type'] != self.vdu.SW_IMAGE:
                    additional_artifacts.append(self._artifacts_info(artifact_name))

            return additional_artifacts
        return list()

    def _artifacts_info(self, artifact_name):
        artifact_path = self.vdu.artifacts[artifact_name]['file']
        return {'artifactPath': artifact_path,
                'checksum': {'algorithm': self.artifacts_hash,
                             'hash': sha256_hash(self.root_path + artifact_path)}}

    def _get_software_images(self) -> list:
        return [{'provider': self.vdu.properties['provider'],
                 'name': self.vdu.properties['name'],
                 'version': self.vdu.properties['version'],
                 'diskFormat': self.vdu.properties['diskFormat']}]
