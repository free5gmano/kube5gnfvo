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

    VERSIONS = 'tosca_simple_yaml_1_0'

    def __init__(self, vnfd_dict):
        self.template = vnfd_dict
        if not self._validate_version():
            raise ValueError('tosca template has illegal attribute')

        self.topology_template = self._topology_template()

    def _validate_version(self):
        for attribute in self.ATTRIBUTE:
            if attribute not in self.template:
                raise ValueError('node template type has illegal attribute')

            else:
                if attribute == self.DEFINITION_VERSION and self.template[attribute] != self.VERSIONS:
                    raise ValueError('node type has illegal version')
            return True

    def _template_topology_template(self):
        return self.template.get(self.TOPOLOGY_TEMPLATE)

    def _topology_template(self):
        return TopologyTemplate(self._template_topology_template())
