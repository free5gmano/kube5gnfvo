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


class VduScalingTemplate(EntityTemplate):
    VDU_SCALING_PROPERTIES = (MAX_INSTANCES, TARGET_CPU_UTILIZATION_PERCENTAGE) = \
        ('max_instances', 'target_cpu_utilization_percentage')

    VDU_SCALING_TARGETS = (TARGETS) = 'targets'

    def __init__(self, node_template, name):
        super().__init__(node_template, name)
        self.properties = self._get_properties(properties=self.VDU_SCALING_PROPERTIES)
        self.targets = self.template.get(self.TARGETS)

    def _validate_properties(self):
        if self.PROPERTIES not in self.template:
            self._value_empty_exception('vdu_scaling', self.PROPERTIES)

        properties = self.template.get(self.PROPERTIES)
        for vdu_scaling_property in properties:
            if vdu_scaling_property not in self.VDU_SCALING_PROPERTIES:
                self._value_error_exception('vdu_scaling', vdu_scaling_property)

        return True

    def _validate_artifacts(self):
        pass

    def _validate_attributes(self):
        pass

    def _validate_requirements(self):
        pass

    def _validate_capabilities(self):
        pass
