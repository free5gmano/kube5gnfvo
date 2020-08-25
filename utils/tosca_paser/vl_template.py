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


class VLTemplate(EntityTemplate):
    VL_PROPERTIES = (NETWORK_NAME, BANDWIDTH, CIDR, DHCP_ENABLED) = (
        'network_name', 'bandwidth', 'cidr', 'dhcp_enabled')

    def __init__(self, node_template, name):
        super().__init__(node_template, name)
        self.properties = self._get_properties(self.VL_PROPERTIES)

    def _validate_properties(self):
        if self.PROPERTIES not in self.template:
            self._value_empty_exception('vl', self.PROPERTIES)

        properties = self.template.get(self.PROPERTIES)
        if self.NETWORK_NAME not in properties:
            self._value_empty_exception(self.PROPERTIES, self.NETWORK_NAME)

        if 'vl_profile' not in properties:
            self._value_empty_exception(self.PROPERTIES, 'vl profile')

        vl_profile = properties['vl_profile']
        if 'virtual_link_protocol_data' not in vl_profile:
            self._value_empty_exception('vl profile', 'virtual_link_protocol_data')

        virtual_link_protocol_data = vl_profile['virtual_link_protocol_data']
        if 'l3_protocol_data' not in virtual_link_protocol_data:
            self._value_empty_exception('virtual link protocol data', 'l3_protocol_data')

        l3_protocol_data = virtual_link_protocol_data['l3_protocol_data']
        if 'dhcp_enabled' not in l3_protocol_data and 'cidr' not in l3_protocol_data:
            self._value_empty_exception('virtual link protocol data', 'l3_protocol_data')

        return True

    def _validate_artifacts(self):
        pass

    def _validate_attributes(self):
        pass

    def _validate_requirements(self):
        pass

    def _validate_capabilities(self):
        pass
