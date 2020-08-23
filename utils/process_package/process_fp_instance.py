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
from NSDManagement.serializers import nsd_base_path
from utils.file_manipulation import walk_file
from utils.onos_client import ONOSClient
from utils.process_package.base_process import BaseProcess


class ProcessFPInstance(BaseProcess):

    def __init__(self, package_id):
        super().__init__(package_id)
        self.onos_client = ONOSClient()
        self.vnffg_info = self.process_template()

    def get_root_path(self):
        root, dirs, files = walk_file('{}{}'.format(nsd_base_path, self.package_id), 'nsd_content')
        return '{}/{}/'.format(root, dirs.pop(0))

    def process_template(self, **kwargs):
        instance_info = list()
        node_template = self.topology_template.node_templates
        group = self.topology_template.group
        if not group:
            return None

        vnffgs = group.vnffg
        fps = node_template.fp
        for vnffg in vnffgs:
            for fp in fps:
                if vnffg.targets[0] == fp.name:
                    vnffg_info = dict()
                    vnffg_info['rsp'] = list()
                    for vnf in fp.requirements['rsp']:
                        vnffg_info['rsp'].append(vnf['forwarder'])
                    vnffg_info['source'] = fp.properties['source']
                    vnffg_info['destination'] = fp.properties['destination']
                    vnffg_info['constituent_vnfd'] = vnffg.properties['constituent_vnfs']
                    vnffg_info['connection_point'] = vnffg.properties['connection_point']
                    vnffg_info['vnffgdId'] = vnffg.properties['id']
                    instance_info.append(vnffg_info)
        return instance_info

    def process_instance(self, **kwargs):
        for vnffg in self.vnffg_info:
            if not self._read_vnffg(vnffg):
                self.register_vnffg(vnffg)

    # id to fqdn
    def mapping_rsp(self, vnfd_id, vnf_instance_name):
        for vnffg in self.vnffg_info:
            position = [i for i, x in enumerate(vnffg['rsp']) if x == vnfd_id]
            if position.__len__() > 0:
                vnffg['rsp'].insert(position[0], vnf_instance_name.lower() + '.imac.edu')
                vnffg['rsp'].remove(vnfd_id)

            if vnffg['source'] == vnfd_id:
                vnffg['source'] = vnf_instance_name.lower() + '.imac.edu'

            if vnffg['destination'] == vnfd_id:
                vnffg['destination'] = vnf_instance_name.lower() + '.imac.edu'

    def register_vnffg(self, vnffg):
        onos_parameter = dict()
        onos_parameter['classifier'] = {"source": vnffg['source'],
                                        "destination": vnffg['destination']}
        onos_parameter['rsp'] = vnffg['rsp']

    def _read_vnffg(self, vnffg):
        onos_parameter = dict()
        onos_parameter['classifier'] = {"source": vnffg['source'],
                                        "destination": vnffg['destination']}
        return self.onos_client.read_sfc(body=onos_parameter)

    def remove_vnffg(self):
        for vnffg in self.vnffg_info:
            onos_parameter = dict()
            onos_parameter['classifier'] = {"source": vnffg['source'],
                                            "destination": vnffg['destination']}
            return self.onos_client.remove_sfc(body=onos_parameter)
