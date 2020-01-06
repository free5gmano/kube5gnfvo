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


class CPTemplate(NodeTemplate):
    CONNECT_POINT_PROPERTIES = (BRIDGE_NAME, INTERFACE_NAME, CIDR) = \
        ('bridge_name', 'interface_name', 'cidr')

    CONNECT_POINT_REQUIREMENTS = (NODE) = 'node'

    def __init__(self, name, node_templates):
        super().__init__(name, node_templates)
        self._validate_fields(self.templates)
        self.bridge_name = self.get_properties(self.BRIDGE_NAME)
        self.interface_name = self.get_properties(self.INTERFACE_NAME)
        self.node = self.get_requirements(self.NODE)
        self.cidr = self.get_properties(self.CIDR)

    def _validate_fields(self, node_template):
        if self.REQUIREMENTS not in node_template:
            raise ValueError("connect point need {}".format(self.REQUIREMENTS))

    def get_type(self):
        return self.TOSCA_CP

    def get_requirements(self, key):
        traversal_dict = TraversalDict(False)
        traversal_dict.traversal(self._validate_requirements(), key)
        return traversal_dict.result

    def _validate_requirements(self):
        requirements = self.templates.get(self.REQUIREMENTS)
        if requirements and 'virtual_binding' not in requirements:
            raise ValueError("node template requirements has illegal attribute")
        return self.templates.get(self.REQUIREMENTS)

    def get_capabilities(self, key):
        pass

    def get_properties(self, key):
        traversal_dict = TraversalDict(True) if key == self.CIDR else TraversalDict(False)
        traversal_dict.traversal(self.templates.get(self.PROPERTIES), key)
        return traversal_dict.result

    def _validate_properties(self):
        properties = self.templates.get(self.PROPERTIES)
        if properties and 'address_data' not in properties and \
                'l2_address_data' not in properties['address_data']:
            raise ValueError("node template properties need address_data or l2_address_data")
        return self.templates.get(self.PROPERTIES)

    def get_attributes(self, key):
        pass
