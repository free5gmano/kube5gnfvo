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

from abc import abstractmethod


class NodeTemplate(object):
    TOSCA_TYPE = (TOSCA_VDU, TOSCA_CP, TOSCA_NS, TOSCA_SCALABLE) = \
        ('tosca.nodes.nfv.Vdu.Compute', 'tosca.nodes.nfv.VduCpd', 'tosca.nodes.nfv.NS', 'tosca.capabilities.Scalable')
    ATTRIBUTE = (TYPE, PROPERTIES, CAPABILITIES, REQUIREMENTS, ATTRIBUTES, VNFFGD) = \
        ('type', 'properties', 'capabilities', 'requirements', 'attributes', 'vnffgd')

    def __init__(self, name, node_templates):
        self.node_name = name
        self.templates = node_templates[name]
        self._validate_fields(self.templates)
        self._validate_necessary_value(self.templates)
        self.template_type = self.templates["type"]
        self._validate_type()

    def _validate_fields(self, node_template):
        for key in node_template.keys():
            if key not in self.ATTRIBUTE:
                raise ValueError("node template has illegal attributes")

    def _validate_type(self):
        if self.template_type not in self.TOSCA_TYPE:
            raise ValueError("node template type has illegal attributes")

    def _validate_necessary_value(self, node_template):
        if self.TYPE not in node_template or self.PROPERTIES not in node_template:
            raise ValueError("node template need type or properties attributes")

    @abstractmethod
    def get_properties(self, key):
        pass

    @abstractmethod
    def get_capabilities(self, key):
        pass

    @abstractmethod
    def get_requirements(self, key):
        pass

    @abstractmethod
    def get_type(self):
        pass

    @abstractmethod
    def get_attributes(self, key):
        pass
