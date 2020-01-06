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

from utils.tosca_paser.node_template import NodeTemplate
from utils.tosca_paser.traversal_dict import TraversalDict


class VDUTemplate(NodeTemplate):
    VDU_CAPABILITIES = (VIRTUAL_MEM_SIZE, NUM_VIRTUAL_CPU) = \
        ('virtual_mem_size', 'num_virtual_cpu')
    VDU_PROPERTIES = (NAME, NAMESPACE, REPLICAS, IMAGE) = \
        ('name', 'namespace', 'replicas', 'image')
    VDU_REQUIREMENTS = (STORAGE_TYPE, STORAGE_SIZE, STORAGE_PATH) = \
        ('type_of_storage', 'size_of_storage', 'path_of_storage')
    VDU_ATTRIBUTES = (KIND, COMMAND, CONFIG_PATH, ENV, TUN, USER_PUBLIC_KEY,
                      SERVICE_NAME, PORT, IS_EXPORT_SERVICE, PROTOCOL) = \
        ('kind', 'command', 'config_path', 'env', 'tun', 'user_public_key',
         'name_of_service', 'ports', 'is_export_service', 'protocol')

    def __init__(self, name, node_templates):
        super().__init__(name, node_templates)
        self.name = self.get_properties(self.NAME)
        self.namespace = self.get_properties(self.NAMESPACE)
        self.replicas = self.get_properties(self.REPLICAS)
        self.image = self.get_properties(self.IMAGE)
        self.virtual_mem_size = self.get_capabilities(self.VIRTUAL_MEM_SIZE)
        self.num_virtual_cpu = self.get_capabilities(self.NUM_VIRTUAL_CPU)
        self.storage_type = self.get_requirements(self.STORAGE_TYPE)
        self.storage_size = self.get_requirements(self.STORAGE_SIZE)
        self.storage_path = self.get_requirements(self.STORAGE_PATH)
        self.user_public_key = self.get_attributes(self.USER_PUBLIC_KEY)
        self.kind = self.get_attributes(self.KIND)
        self.command = self.get_attributes(self.COMMAND)
        self.config_path = self.get_attributes(self.CONFIG_PATH)
        self.env = self.get_attributes(self.ENV)
        self.tun = self.get_attributes(self.TUN)
        self.name_of_service = self.get_attributes(self.SERVICE_NAME)
        self.ports = self.get_attributes(self.PORT)
        self.is_export_service = self.get_attributes(self.IS_EXPORT_SERVICE)
        self.protocol = self.get_attributes(self.PROTOCOL)

    def get_type(self):
        return self.TOSCA_VDU

    def get_attributes(self, key):
        traversal_dict = TraversalDict(True) if key == self.ENV else TraversalDict(False)
        traversal_dict.traversal(self.templates.get(self.ATTRIBUTES), key)
        return traversal_dict.result

    def get_requirements(self, key):
        node_template = self._requirements_node_template()
        if not node_template:
            return None
        traversal_dict = TraversalDict(False)
        traversal_dict.traversal(node_template, key)
        return traversal_dict.result

    def _requirements_node_template(self):
        requirements = self.templates.get(self.REQUIREMENTS)
        if not requirements:
            return None
        if 'virtual_storage' not in requirements:
            raise ValueError("requirements need virtual_storage attributes")
        return requirements

    def get_capabilities(self, key):
        node_template = self._capabilities_node_template()
        if not node_template:
            return None
        traversal_dict = TraversalDict(False)
        traversal_dict.traversal(self._capabilities_node_template(), key)
        return traversal_dict.result

    def _capabilities_node_template(self):
        capabilities = self.templates.get(self.CAPABILITIES)
        if capabilities and 'virtual_compute' not in capabilities:
            raise ValueError("node template capabilities has illegal attribute")
        return capabilities

    def get_properties(self, key):
        traversal_dict = TraversalDict(False)
        traversal_dict.traversal(self.templates.get(self.PROPERTIES), key)
        return traversal_dict.result
