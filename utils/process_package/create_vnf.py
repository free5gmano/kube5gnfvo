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
from VIMManagement.utils.virtual_machine_instance import VirtualMachineInstance
from os_ma_nfvo import settings
from utils.file_manipulation import create_dir
from utils.process_package.process_vnf_instance import ProcessVNFInstance


class CreateService(ProcessVNFInstance):
    def __init__(self, package_id, vnf_instance_name):
        super().__init__(package_id, vnf_instance_name)

    def process_config_map(self, **kwargs):
        with open(kwargs['artifacts_path'], 'r') as artifacts_file_content:
            client = ConfigMapClient(
                instance_name=self.vnf_instance_name, namespace=kwargs['namespace'],
                config_file_name=kwargs['artifacts_name'], config_file_content=artifacts_file_content.read())
            client.handle_create_or_update()

    def process_deployment(self, **kwargs):
        if kwargs['vdu_info']['diskFormat'] == 'raw':
            client = DeploymentClient(**kwargs['vdu_info'])
        else:
            client = VirtualMachineInstance(**kwargs['vdu_info'])

        client.handle_create_or_update()

    def process_service(self, **kwargs):
        vdu = kwargs['vdu']
        client = ServiceClient(
            instance_name=vdu.attributes['name_of_service'], namespace=vdu.attributes['namespace'],
            ports=vdu.attributes['ports'], protocol=vdu.attributes['protocol'],
            service_type='NodePort' if vdu.attributes['is_export_service'] else 'ClusterIP')
        client.handle_create_or_update()

    def process_persistent_volume_claim(self, **kwargs):
        vdu = kwargs['vdu']
        client = PersistentVolumeClaimClient(
            instance_name=self.vnf_instance_name, namespace=vdu.attributes['namespace'],
            storage_size=vdu.requirements['size_of_storage'])
        client.handle_create_or_update()

    def process_persistent_volume(self, **kwargs):
        vdu = kwargs['vdu']
        if vdu.requirements['type_of_storage'] == 'nfs':
            client = PersistentVolumeClient(instance_name=self.vnf_instance_name,
                                        storage_size=vdu.requirements['size_of_storage'],
                                        storage_type=vdu.requirements['type_of_storage'],
                                        nfs_server=vdu.requirements['server_of_storage'],
                                        nfs_path=vdu.requirements['path_of_storage'])
            client.handle_create_or_update()
            mount_dir(nfs_server=vdu.requirements['server_of_storage'],nfs_path=vdu.requirements['path_of_storage'])
            create_dir("{}{}".format(settings.NFS_PATH, self.vnf_instance_name))
        elif vdu.requirements['type_of_storage'] == 'volume' or vdu.requirements['type_of_storage'] == 'local':
            client = PersistentVolumeClient(instance_name=self.vnf_instance_name,
                                        storage_size=vdu.requirements['size_of_storage'],
                                        storage_type=vdu.requirements['type_of_storage'])
            client.handle_create_or_update()
            create_dir("{}{}".format(settings.VOLUME_PATH, self.vnf_instance_name))
        else:
            raise APIException(detail='storage type only local or nfs',
                                   code=status.HTTP_409_CONFLICT)

    def process_horizontal_pod_autoscaler(self, **kwargs):
        vdu = kwargs['vdu']
        scale = kwargs['scale']
        client = HorizontalPodAutoscalerClient(
            instance_name=self.vnf_instance_name, namespace=vdu.attributes['namespace'],
            max_replicas=scale['max_instances'],
            min_replicas=vdu.attributes['replicas'],
            target_cpu_utilization_percentage=scale['target_cpu_utilization_percentage'],
            isContainer=kwargs['isContainer'])
        client.handle_create_or_update()
