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

from utils.tosca_paser.entity_template import EntityTemplate


class VDUTemplate(EntityTemplate):
    VDU_CAPABILITIES = (NUM_VIRTUAL_CPU, VIRTUAL_MEM_SIZE) = \
        ('num_virtual_cpu', 'virtual_mem_size')
    VDU_PROPERTIES = (NAME, PROVIDER, VERSION, DISK_FORMAT) = \
        ('name', 'provider', 'version', 'diskFormat')
    VDU_REQUIREMENTS = (STORAGE_TYPE, STORAGE_SIZE, STORAGE_PATH) = \
        ('type_of_storage', 'size_of_storage', 'path_of_storage')
    VDU_ATTRIBUTES = (NAMESPACE, REPLICAS, TUN, USER_PUBLIC_KEY, USER_NAME,
                      NAME_OF_SERVICE, PORTS, IS_EXPORT_SERVICE, PROTOCOL) = \
        ('namespace', 'replicas', 'tun', 'user_public_key', 'user_name',
         'name_of_service', 'ports', 'is_export_service', 'protocol')
    VDU_ATTRIBUTES_LIST = (COMMAND, ENV) = ('command', 'env')
    VDU_ARTIFACTS = (TYPE, FILE, DEPLOY_PATH) = ('type', 'file', 'deploy_path')
    VDU_ARTIFACTS_TYPE = (SW_IMAGE, ARTIFACTS_FILE) = ('tosca.artifacts.nfv.SwImage', 'tosca.artifacts.File')

    def __init__(self, node_template, name):
        super().__init__(node_template, name)
        self.properties = self._get_properties(self.VDU_PROPERTIES)
        self.capabilities = self._get_capabilities(self.VDU_CAPABILITIES)
        self.requirements = self._get_requirements(self.VDU_REQUIREMENTS)
        self.attributes = self._get_attributes(self.VDU_ATTRIBUTES, attributes_list=self.VDU_ATTRIBUTES_LIST)
        self.artifacts = self._get_artifacts()

    def _validate_properties(self):
        if self.PROPERTIES not in self.template:
            self._value_empty_exception('vdu', self.PROPERTIES)

        properties = self.template.get(self.PROPERTIES)
        if 'sw_image_data' not in properties or not isinstance(properties.get('sw_image_data'), dict):
            self._value_error_exception('vdu properties', 'sw_image_data')

        sw_image_data = properties.get('sw_image_data')
        if self.NAME not in sw_image_data or self.PROVIDER not in sw_image_data \
                or self.VERSION not in sw_image_data or self.DISK_FORMAT not in sw_image_data:
            self._value_empty_exception('vdu properties sw_image_data',
                                        '{} or {} or {} or {}'.format(self.NAME, self.PROVIDER, self.VERSION,
                                                                      self.DISK_FORMAT))
        return True

    def _validate_capabilities(self):
        if self.CAPABILITIES not in self.template or \
                'virtual_compute' not in self.template.get(self.CAPABILITIES):
            self._value_empty_exception('vdu', self.CAPABILITIES)

        virtual_compute = self.template.get(self.CAPABILITIES).get('virtual_compute')
        if self.PROPERTIES not in virtual_compute:
            self._value_empty_exception('vdu virtual_compute', self.PROPERTIES)

        properties = virtual_compute.get(self.PROPERTIES)
        if 'virtual_memory' not in properties or 'virtual_cpu' not in properties:
            self._value_empty_exception('vdu virtual_compute properties', 'virtual_memory and virtual_cpu')

        mem = properties.get('virtual_memory')
        cpu = properties.get('virtual_cpu')
        if 'virtual_mem_size' not in mem or 'num_virtual_cpu' not in cpu:
            self._value_empty_exception(
                'vdu virtual_compute properties virtual_memory or virtual_cpu',
                'virtual_mem_size and num_virtual_cpu')

        return True

    def _validate_requirements(self):
        if self.REQUIREMENTS in self.template \
                and 'virtual_storage' in self.template.get(self.REQUIREMENTS):
            virtual_storage = self.template.get(self.REQUIREMENTS).get('virtual_storage')
            if virtual_storage and self.PROPERTIES in virtual_storage:
                properties = virtual_storage.get(self.PROPERTIES)
                for requirement in self.VDU_REQUIREMENTS:
                    if requirement not in properties:
                        self._value_error_exception('virtual_storage', requirement)

                return True

    def _validate_attributes(self):
        return True

    def _validate_artifacts(self):
        if self.ARTIFACTS not in self.template:
            return False

        artifacts = self.template.get(self.ARTIFACTS)
        if 'sw_image' not in artifacts:
            self._value_empty_exception('vdu artifacts', 'sw_image')

        for artifact_name in artifacts:
            if artifacts.get(artifact_name).get('type') not in self.VDU_ARTIFACTS_TYPE:
                self._value_error_exception(artifact_name, 'type')

        return True
