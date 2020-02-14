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


class FPTemplate(EntityTemplate):
    FP_REQUIREMENTS_LIST = (RSP) = 'rsp'
    FP_PROPERTIES = (SOURCE, DESTINATION) = ('source', 'destination')

    def __init__(self, node_template, name):
        super().__init__(node_template, name)
        self.properties = self._get_properties(self.FP_PROPERTIES)
        self.requirements = self._get_requirements(requirements_list=self.FP_REQUIREMENTS_LIST)

    def _validate_properties(self):
        if self.PROPERTIES not in self.template:
            self._value_empty_exception('fp', self.PROPERTIES)

        properties = self.template.get(self.PROPERTIES)
        if 'policy' not in properties or 'classifier' not in properties:
            self._value_empty_exception('fp properties', 'policy or classifier')

        policy = properties.get('policy')
        if policy != 'ACL':
            self._value_error_exception('fp properties', 'policy')

        classifier = properties.get('classifier')
        if self.DESTINATION not in classifier or self.SOURCE not in classifier:
            self._value_empty_exception('fp properties policy', 'source or destination')

        return True

    def _validate_artifacts(self):
        pass

    def _validate_attributes(self):
        pass

    def _validate_requirements(self):
        if self.REQUIREMENTS not in self.template:
            self._value_empty_exception('fp', self.REQUIREMENTS)

        requirements = self.template.get(self.REQUIREMENTS)
        if self.RSP not in requirements:
            self._value_empty_exception('fp requirements', self.RSP)

        return True

    def _validate_capabilities(self):
        pass
