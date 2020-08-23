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

CNI_TYPE = (SR_IOV, OVS) = ('sr-iov', 'ovs')


class CPTemplate(EntityTemplate):
    CP_PROPERTIES = (LAYER_PROTOCOL, CP_TYPE) = ('layer_protocol', 'type')
    CP_REQUIREMENTS = (VIRTUAL_BINDING, VIRTUAL_LINK) = ('virtual_binding', 'virtual_link')

    def __init__(self, node_template, name):
        super().__init__(node_template, name)
        self.properties = self._get_properties(self.CP_PROPERTIES)
        self.requirements = self._get_requirements(self.CP_REQUIREMENTS)

    def _validate_properties(self):
        if self.PROPERTIES not in self.template:
            self._value_empty_exception('cp', self.PROPERTIES)

        properties = self.template.get(self.PROPERTIES)
        if self.LAYER_PROTOCOL not in properties:
            self._value_empty_exception('cp properties', self.LAYER_PROTOCOL)

        return True

    def _validate_requirements(self):
        if self.REQUIREMENTS not in self.template:
            self._value_empty_exception('cp', self.REQUIREMENTS)

        requirements = self.template.get(self.REQUIREMENTS)
        if not requirements or self.VIRTUAL_BINDING not in requirements \
                or self.VIRTUAL_LINK not in requirements:
            self._value_empty_exception('cp requirements', '{} and {}'.format(self.VIRTUAL_BINDING, self.VIRTUAL_LINK))

        if self.CP_TYPE in self.REQUIREMENTS:
            if self.REQUIREMENTS[self.CP_TYPE] not in CNI_TYPE:
                self._value_error_exception(self.REQUIREMENTS, self.CP_TYPE)

        return True

    def _validate_artifacts(self):
        pass

    def _validate_attributes(self):
        pass

    def _validate_capabilities(self):
        pass
