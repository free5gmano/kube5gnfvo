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
from utils.tosca_paser.topology_template import TopologyTemplate


class ToscaTemplate(object):
    ATTRIBUTE = (DEFINITION_VERSION, TOPOLOGY_TEMPLATE) = \
        ('tosca_definitions_version', 'topology_template')

    VERSIONS = 'tosca_simple_yaml_1_0', 'tosca_simple_yaml_1_2'

    def __init__(self, vnfd_dict):
        self.template = vnfd_dict
        self._validate_field()
        self.topology_template = self._topology_template()

    def _validate_field(self):
        if not self.template:
            raise ValueError('tosca template is None')

        for field in self.template:
            if field is self.DEFINITION_VERSION:
                self._validate_tosca_version()
            elif field not in self.ATTRIBUTE:
                raise ValueError('node template type has illegal attribute')

    def _validate_tosca_version(self):
        version = self.template.get(self.DEFINITION_VERSION)
        if not version or version is not self.VERSIONS:
            raise ValueError('node type has illegal version')

    def _template_topology_template(self):
        return self.template.get(self.TOPOLOGY_TEMPLATE)

    def _topology_template(self):
        return TopologyTemplate(self._template_topology_template())
