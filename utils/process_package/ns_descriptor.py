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
        self.vnffgd = None

    def process_topology_template(self, topology_template):
        pass

    def process_node_template(self, node_template):
        if 'tosca.nodes.nfv.NS' in node_template.get_type():
            self.vnffgd = node_template

    def processing_data(self):
        ns_info_list = [node_template
                        for node_template in self.topology_template.node_templates
                        if 'tosca.nodes.nfv.NS' in node_template.get_type()]
        # TODO multiple NS
        ns_info = ns_info_list.pop(0)
        return {'nsdId': ns_info.descriptor_id,
                'nsdName': ns_info.name,
                'nsdVersion': ns_info.version,
                'nsdDesigner': ns_info.designer,
                'nsdInvariantId': ns_info.invariant_id,
                'vnfPkgIds': list()}, ns_info.constituent_vnfd
