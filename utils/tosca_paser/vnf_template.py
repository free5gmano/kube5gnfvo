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


class VNFTemplate(EntityTemplate):
    VNF_PROPERTIES = (DESCRIPTOR_ID, DESCRIPTOR_VERSION, PROVIDER, PRODUCT_NAME, SOFTWARE_VERSION) = \
        ('descriptor_id', 'descriptor_version', 'provider', 'product_name', 'software_version')

    def __init__(self, node_template, name):
        super().__init__(node_template, name)
        self.properties = self._get_properties(self.VNF_PROPERTIES)

    def _validate_properties(self):
        if self.PROPERTIES not in self.template:
            self._value_empty_exception('vnf', self.PROPERTIES)

        properties = self.template.get(self.PROPERTIES)
        for vnf_properties in self.VNF_PROPERTIES:
            if vnf_properties not in properties:
                self._value_empty_exception('vnf properties', vnf_properties)

        return True

    def _validate_artifacts(self):
        pass

    def _validate_attributes(self):
        pass

    def _validate_requirements(self):
        pass

    def _validate_capabilities(self):
        pass
