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

from utils.process_package.base_package import BasePackage


class NetworkServiceDescriptor(BasePackage):

    def __init__(self, path):
        super().__init__(path=path)
        node_templates = self.topology_template.node_templates
        self.ns = node_templates.ns[0]

    def processing_data(self):
        # TODO multiple NS
        return {'nsdId': self.ns.properties['descriptor_id'],
                'nsdName': self.ns.properties['name'],
                'nsdVersion': self.ns.properties['version'],
                'nsdDesigner': self.ns.properties['designer'],
                'nsdInvariantId': self.ns.properties['invariant_id'],
                'vnfPkgIds': list()}

    def get_constituent_vnfd(self):
        return self.ns.properties['constituent_vnfd']
