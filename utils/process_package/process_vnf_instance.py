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

import json
import os
from abc import abstractmethod
from VnfPackageManagement.serializers import vnf_package_base_path
from utils.file_manipulation import walk_file
from utils.process_package.base_process import BaseProcess
from utils.onos_client import ONOSClient


class ProcessVNFInstance(BaseProcess):

    def __init__(self, package_id, vnf_instance_name=None):
        super().__init__(package_id)
        self.vnf_instance_name = None
        self.onos_client = ONOSClient()
        if vnf_instance_name:
            self.vnf_instance_name = vnf_instance_name.lower()

    def get_root_path(self):
        root, dirs, files = walk_file('{}{}'.format(vnf_package_base_path, self.package_id), 'package_content')
        return '{}/{}/'.format(root, dirs.pop(0))

    # need to fix
    def _process_network(self, net_list, vdu_info, isTemplate=False, max_instances=None):
        self.etcd_client.set_deploy_name(instance_name=self.vnf_instance_name, pod_name=None)
        ip_address = list()
        network_name_list = list()
        ext_cp_info = list()
        rate = 0

        for net_info in net_list:
            for vl_info, cp_info in net_info.items():
                dhcp_enabled = False
                if vl_info.properties['bandwidth']:
                    rate = vl_info.properties['bandwidth']

                if vl_info.properties['cidr']:
                    dhcp_enabled = True
                    cidr = vl_info.properties['cidr']
                    ip_address.append(cidr)
                    ip_address_mask = cidr.split('/')
                    self.etcd_client.check_valid_static_ip_address(ip_address_mask[0],
                                                                   ip_address_mask[1])
                elif vl_info.properties['dhcp_enabled']:
                    dhcp_enabled = True
                    if max_instances:
                        ip_address = [self.etcd_client.create_ip_pool() for _ in range(max_instances)]
                    else:
                        ip_address = [self.etcd_client.create_ip_pool() for _ in
                                      range(vdu_info.attributes.replicas)]

                if isTemplate:
                    vnf_ext_cp_info_info = dict()
                    vnf_ext_cp_info_info['cpdId'] = cp_info.name
                    vnf_ext_cp_info_info['cpProtocolInfo'] = list()
                    cp_protocol_info = dict()
                    cp_protocol_info['layerProtocol'] = 'IP_OVER_ETHERNET'
                    cp_protocol_info['ipOverEthernet'] = dict()
                    cp_protocol_info['ipOverEthernet']['ipAddresses'] = list()
                    ip_info = dict()
                    ip_info['isDynamic'] = dhcp_enabled
                    ip_info['type'] = 'IPV4'
                    if dhcp_enabled:
                        for ip in ip_address:
                            ip_info['addresses'] = ip
                            cp_protocol_info['ipOverEthernet']['ipAddresses'].append(ip_info)
                    else:
                        cp_protocol_info['ipOverEthernet']['ipAddresses'].append(ip_info)

                    vnf_ext_cp_info_info['cpProtocolInfo'].append(cp_protocol_info)
                    ext_cp_info.append(vnf_ext_cp_info_info)
                if 'management' != vl_info.properties['network_name']:
                    network_name_list.append({vl_info.properties['network_name']: dhcp_enabled})

        if isTemplate:
            return ext_cp_info
        else:
            return rate, network_name_list

    # need to fix
    def process_template(self, **kwargs):
        total_vdu_list = list()
        max_instances = None
        node_template = self.topology_template.node_templates
        policy_template = self.topology_template.policies
        for vnf in node_template.integration_vnf:
            vdu = node_template.integration_vnf[vnf]
            if policy_template:
                vdu_scaling = policy_template.vdu_scaling
                for scale in vdu_scaling:
                    if vnf in scale.targets:
                        max_instances = scale.properties['max_instances']
                        self.process_horizontal_pod_autoscaler(vdu=vdu, scale=scale.properties)
                        break
            total_vdu_list += self._process_network(vdu['net'], vdu['info'], isTemplate=True,
                                                    max_instances=max_instances)
        return total_vdu_list

    # need to fix
    def process_instance(self, topology_template):
        node_template = topology_template.node_templates
        policy_template = topology_template.policies
        max_instances = None
        for vnf in node_template.integration_vnf:
            vdu = node_template.integration_vnf[vnf]
            net_list = vdu['net']
            vdu = vdu['info']
            vdu_info = dict()
            self.process_artifacts(vdu, vdu_info)

            if vdu.attributes['ports'] and vdu.attributes['name_of_service']:
                self.process_service(vdu=vdu)

            if vdu.requirements and vdu.requirements['size_of_storage'] and vdu.requirements['path_of_storage']:
                vdu_info.update(vdu.requirements)
                self.process_persistent_volume_claim(vdu=vdu)
                self.process_persistent_volume(vdu=vdu)

            if policy_template:
                vdu_scaling = policy_template.vdu_scaling
                for scale in vdu_scaling:
                    if vnf in scale.targets:
                        max_instances = scale.properties['max_instances']
                        self.process_horizontal_pod_autoscaler(vdu=vdu, scale=scale.properties)
                        break

            rate, network_name_list = self._process_network(net_list, vdu, max_instances=max_instances)

            vdu_info.update(vdu.properties)
            vdu_info.update(vdu.attributes)
            vdu_info.update(vdu.capabilities)
            vdu_info['instance_name'] = self.vnf_instance_name
            vdu_info['network_name'] = network_name_list
            self.process_deployment(vdu_info=vdu_info)

    def process_artifacts(self, vdu, vnf_info):
        artifacts = vdu.artifacts
        deploy_path = list()
        for artifact_name in artifacts:
            artifact = artifacts[artifact_name]
            if artifact['type'] != vdu.SW_IMAGE:
                path = os.path.split(artifact['deploy_path'])
                if "." not in path[1]:
                    artifacts_name = path[1]
                else:
                    artifacts_name = path[1].split(".")[0]

                self.process_config_map(artifacts_path=self.root_path + artifact['file'],
                                        artifacts_name=artifacts_name.lower(), namespace=vdu.attributes['namespace'])
                deploy_path.append(artifact['deploy_path'])
            else:
                vnf_info['image'] = artifact['file']

        if deploy_path.__len__() > 0:
            vnf_info['config_map_mount_path'] = deploy_path
        else:
            vnf_info['config_map_mount_path'] = None

    @abstractmethod
    def process_persistent_volume(self, **kwargs):
        pass

    @abstractmethod
    def process_persistent_volume_claim(self, **kwargs):
        pass

    @abstractmethod
    def process_service(self, **kwargs):
        pass

    @abstractmethod
    def process_deployment(self, **kwargs):
        pass

    @abstractmethod
    def process_config_map(self, **kwargs):
        pass

    @abstractmethod
    def process_horizontal_pod_autoscaler(self, **kwargs):
        pass
