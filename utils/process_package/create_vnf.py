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

from VIMManagement.utils.config_map import ConfigMapClient
from VIMManagement.utils.deployment import DeploymentClient
from VIMManagement.utils.horizontal_pod_autoscaler import HorizontalPodAutoscalerClient
from VIMManagement.utils.persistent_volume import PersistentVolumeClient
from VIMManagement.utils.persistent_volume_claim import PersistentVolumeClaimClient
from VIMManagement.utils.service import ServiceClient
from os_ma_nfvo import settings
from utils.file_manipulation import create_dir
from utils.process_package.process_vnf_instance import ProcessVNFInstance


class CreateService(ProcessVNFInstance):
    def __init__(self, vnf_package_id, vnf_instance_name):
        super().__init__(vnf_package_id, vnf_instance_name)

    def process_config_map(self, **kwargs):
        with open(kwargs['artifacts_path'], 'r') as artifacts_file_content:
            client = ConfigMapClient(
                instance_name=self.vnf_instance_name, namespace=kwargs['namespace'],
                config_file_name=kwargs['artifacts_name'], config_file_content=artifacts_file_content.read())
            client.handle_create_or_update()

    def process_deployment(self, **kwargs):
        vdu = kwargs['vdu']
        data = {'instance_name': self.vnf_instance_name,
                'namespace': vdu.namespace,
                'replicas': vdu.replicas,
                'image': vdu.image,
                'command': vdu.command,
                'mount_path': vdu.storage_path,
                'config_path': vdu.config_path,
                'cpu': vdu.num_virtual_cpu,
                'memory': vdu.virtual_mem_size,
                'env': vdu.env,
                'tun': vdu.tun,
                'protocol': vdu.protocol if vdu.protocol else 'TCP',
                'ports': vdu.ports,
                'service_name': vdu.name_of_service,
                'cp_count': kwargs['cp_count'],
                'user_public_key': vdu.user_public_key}
        client = DeploymentClient(**data)
        client.handle_create_or_update()

    def process_service(self, **kwargs):
        vdu = kwargs['vdu']
        client = ServiceClient(
            instance_name=kwargs['vdu'].name_of_service, namespace=vdu.namespace, port=vdu.ports,
            protocol=vdu.protocol, service_type='NodePort' if vdu.is_export_service == 'True' else 'ClusterIP')
        client.handle_create_or_update()

    def process_persistent_volume_claim(self, **kwargs):
        vdu = kwargs['vdu']
        client = PersistentVolumeClaimClient(
            instance_name=self.vnf_instance_name, namespace=vdu.namespace, storage_size=vdu.storage_size)
        client.handle_create_or_update()

    def process_persistent_volume(self, **kwargs):
        vdu = kwargs['vdu']
        client = PersistentVolumeClient(instance_name=self.vnf_instance_name, storage_size=vdu.storage_size)
        client.handle_create_or_update()

    def process_horizontal_pod_autoscaler(self, **kwargs):
        vdu = kwargs['vdu']
        scale = kwargs['scale']
        client = HorizontalPodAutoscalerClient(
            instance_name=self.vnf_instance_name, namespace=vdu.namespace, max_replicas=scale.max_instances,
            min_replicas=vdu.replicas, target_cpu_utilization_percentage=scale.target_cpu_utilization_percentage)
        client.handle_create_or_update()

    def process_deploy(self, **kwargs):
        for vdu in self.vdu:
            instances_count = None
            for scale_policy in self.scale_policy:
                if vdu.node_name == scale_policy.node:
                    instances_count = scale_policy.max_instances
                    self.process_horizontal_pod_autoscaler(vdu=vdu, scale=scale_policy)
            for cp in self.connect_point:
                if cp.node == vdu.node_name:
                    if cp.cidr:
                        for cidr in cp.cidr:
                            ip_address_mask = cidr.split('/')
                            kwargs['etcd_client'].check_valid_static_ip_address(
                                ip_address_mask[0], ip_address_mask[1])
                    else:
                        [kwargs['etcd_client'].create_ip_pool() for _ in
                         range(instances_count if instances_count else vdu.replicas)]
            vdu.virtual_mem_size = kwargs['scale_memory'] if 'scale_memory' in kwargs else vdu.virtual_mem_size
            vdu.num_virtual_cpu = kwargs['scale_cpu'] if 'scale_cpu' in kwargs else vdu.num_virtual_cpu
            if vdu.storage_path and vdu.storage_size:
                create_dir("{}{}".format(settings.VOLUME_PATH, self.vnf_instance_name))

            self.process_deployment(vdu=vdu, cp_count=len(self.connect_point))
