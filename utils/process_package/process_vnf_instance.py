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
import os
from abc import abstractmethod
from VnfPackageManagement.serializers import vnf_package_base_path
from utils.file_manipulation import walk_file
from utils.process_package.base_process import BaseProcess


class ProcessVNFInstance(BaseProcess):

    def __init__(self, package_id, vnf_instance_name=None):
        super().__init__(package_id)
        self.vnf_instance_name = None
        if vnf_instance_name:
            self.vnf_instance_name = vnf_instance_name.lower()

    def get_root_path(self):
        root, dirs, files = walk_file('{}{}'.format(vnf_package_base_path, self.package_id), 'package_content')
        return '{}/{}/'.format(root, dirs.pop(0))

    # TODO
    def _process_network(self, net_list, vdu_info, isTemplate=False, max_instances=None):
        # self.etcd_client.set_deploy_name(instance_name=self.vnf_instance_name, pod_name=None)
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
                elif vl_info.properties['dhcp_enabled']:
                    dhcp_enabled = True

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
                    network_name_list.append({'network_name': vl_info.properties['network_name'],
                                              'type': cp_info.properties['type'],
                                              'ip_address': ip_address})

        if isTemplate:
            return ext_cp_info
        else:
            return rate, network_name_list

    # TODO
    def process_template(self, **kwargs):
        total_vdu_list = list()
        node_template = self.topology_template.node_templates
        for vnf in node_template.integration_vnf:
            vdu = node_template.integration_vnf[vnf]
            total_vdu_list += self._process_network(
                vdu['net'], vdu['info'], isTemplate=True)
        return total_vdu_list

    # TODO
    def process_instance(self, **kwargs):
        node_template = self.topology_template.node_templates
        policy_template = self.topology_template.policies
        max_instances = None
        for vnf in node_template.integration_vnf:
            vdu = node_template.integration_vnf[vnf]
            net_list = vdu['net']
            service_mesh = vdu['service_mesh']
            vdu = vdu['info']
            vdu_info = dict()
            vdu_info['instance_name'] = self.vnf_instance_name
            vdu_info.update(vdu.properties)
            vdu_info.update(vdu.attributes)
            vdu_info.update(vdu.capabilities)

            if vdu.attributes['stateful_application'] == 1 :
                self.process_docker(vdu=vdu)
                return

            self.process_namespace(vdu=vdu)
            self.process_artifacts(vdu, vdu_info)

            if vdu.attributes['ports'] and vdu.attributes['name_of_service']:
                self.process_service(vdu=vdu)
            
            if vdu.attributes['nodeport'] and vdu.attributes['name_of_nodeport']:
                self.process_nodeport(vdu=vdu)

            if vdu.attributes['tenant']:
                self.process_network_policy(vdu=vdu)

            if vdu.requirements and vdu.requirements['size_of_storage'] and vdu.requirements['path_of_storage']:
                vdu_info.update(vdu.requirements)
                self.process_persistent_volume_claim(vdu=vdu)
                self.process_persistent_volume(vdu=vdu)

            if policy_template:
                vdu_scaling = policy_template.vdu_scaling
                for scale in vdu_scaling:
                    if vnf in scale.targets:
                        max_instances = scale.properties['max_instances']
                        if vdu.properties['diskFormat'] == 'raw':
                            self.process_horizontal_pod_autoscaler(vdu=vdu, scale=scale.properties, isContainer=True)
                        else:
                            self.process_horizontal_pod_autoscaler(vdu=vdu, scale=scale.properties, isContainer=False)
                        break

            if service_mesh:
                if 'circuit_breaking' in service_mesh:
                    self.process_destination_rule(vdu_info=vdu_info, service_mesh_info=service_mesh)
                if 'retry_policy' in service_mesh:
                    self.process_virtual_service(vdu_info=vdu_info, service_mesh_info=service_mesh)
                if 'canary' in service_mesh:
                    self.process_destination_rule(vdu_info=vdu_info, service_mesh_info=service_mesh)
                    self.process_virtual_service(vdu_info=vdu_info, service_mesh_info=service_mesh)
            rate, network_name_list = self._process_network(net_list, vdu, max_instances=max_instances)
            vdu_info['network_name'] = network_name_list

            # update api
            if 'replicas' in kwargs and kwargs['replicas']:
                vdu_info['replicas'] = kwargs['replicas']

            if 'virtual_mem_size' in kwargs and kwargs['virtual_mem_size']:
                vdu_info['virtual_mem_size'] = kwargs['virtual_mem_size']

            if 'num_virtual_cpu' in kwargs and kwargs['num_virtual_cpu']:
                vdu_info['num_virtual_cpu'] = kwargs['num_virtual_cpu']

            if 'vdu' in kwargs and kwargs['vdu']:
                vdu_info['vdu'] = kwargs['vdu']

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
                    artifacts_name = (path[0].split('/')[path[0].split('/').__len__()-1]+'-'+path[1].split(".")[0]).lower()

                self.process_config_map(artifacts_path=self.root_path + artifact['file'],  artifacts_name=artifacts_name.lower(), 
                                        namespace=vdu.attributes['namespace'], apply_cluster=vdu.attributes['apply_cluster'])
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
    def process_namespace(self, **kwargs):
        pass
    @abstractmethod
    def process_horizontal_pod_autoscaler(self, **kwargs):
        pass
    @abstractmethod
    def process_virtual_service(self, **kwargs):
        pass
    @abstractmethod
    def process_destination_rule(self, **kwargs):
        pass