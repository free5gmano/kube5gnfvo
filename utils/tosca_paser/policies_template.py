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


class PoliciesTemplate(NodeTemplate):
    POLICIES_PROPERTIES = (MAX_INSTANCES, TARGET_CPU_UTILIZATION_PERCENTAGE) = \
        ('max_instances', 'target_cpu_utilization_percentage')

    POLICIES_REQUIREMENTS = (NODE) = 'node'

    def __init__(self, name, node_templates):
        super().__init__(name, node_templates)
        self._validate_fields(self.templates)
        self.max_instances = self.get_properties(self.MAX_INSTANCES)
        self.target_cpu_utilization_percentage = self.get_properties(self.TARGET_CPU_UTILIZATION_PERCENTAGE)
        self.node = self.get_requirements(self.NODE)

    def _validate_fields(self, policy_template):
        if self.REQUIREMENTS not in policy_template:
            raise ValueError("policy template need {}".format(self.REQUIREMENTS))

    def get_type(self):
        return self.TOSCA_SCALABLE

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
        traversal_dict = TraversalDict(False)
        traversal_dict.traversal(self.templates.get(self.PROPERTIES), key)
        return traversal_dict.result

    def _validate_properties(self):
        properties = self.templates.get(self.PROPERTIES)
        for properties_attr in self.POLICIES_PROPERTIES:
            if properties_attr not in properties:
                raise ValueError("node template properties need {}".format(properties_attr))
        return self.templates.get(self.PROPERTIES)

    def get_attributes(self, key):
        pass
