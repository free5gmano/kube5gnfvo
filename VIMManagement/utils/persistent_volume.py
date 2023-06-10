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

from VIMManagement.utils.kubernetes_api import KubernetesApi
import os_ma_nfvo.settings as setting


class PersistentVolumeClient(KubernetesApi):
    def __init__(self, *args, **kwargs):
        if 'storage_size' in kwargs:
            self.storage_size = kwargs['storage_size']
        if 'storage_type' in kwargs:
            self.storage_type = kwargs['storage_type']
        if 'nfs_path' in kwargs:
            self.nfs_path = kwargs['nfs_path']
        if 'nfs_server' in kwargs:
            self.nfs_server = kwargs['nfs_server']
        self.apply_cluster = kwargs['apply_cluster'] if 'apply_cluster' in kwargs else None

        

        super().__init__(*args, **kwargs)
        if self.apply_cluster:
            self.core_v1 = self.kubernetes_client.CoreV1Api(api_client=self.config.new_client_from_config(context=self.apply_cluster))

    def read_resource(self, **kwargs):
        return self.core_v1.read_persistent_volume(self.instance_name)

    def create_resource(self, **kwargs):
        self.core_v1.create_persistent_volume(self.resource)

    def patch_resource(self, **kwargs):
        self.core_v1.patch_persistent_volume(self.instance_name, self.resource)

    def delete_resource(self, **kwargs):
        self.core_v1.delete_persistent_volume(
            name=self.instance_name, body=self.delete_options)

    def instance_specific_resource(self, **kwargs):
        persistent_volume = self.kubernetes_client.V1PersistentVolume(
            api_version='v1', kind='PersistentVolume')
        persistent_volume.metadata = self.kubernetes_client.V1ObjectMeta(name=self.instance_name,
                                                                         labels={"name": self.instance_name})
        if self.storage_type == 'nfs':
            persistent_volume.spec = self.kubernetes_client.V1PersistentVolumeSpec(
                capacity={"storage": self.storage_size}, access_modes=["ReadWriteOnce"],
                nfs=self.kubernetes_client.V1NFSVolumeSource(
                    path='{}'.format(self.nfs_path),
                    server='{}'.format(self.nfs_server)))
        elif self.storage_type == 'volume' or self.storage_type == 'local':
            persistent_volume.spec = self.kubernetes_client.V1PersistentVolumeSpec(
                capacity={"storage": self.storage_size}, access_modes=["ReadWriteOnce"],
                host_path=self.kubernetes_client.V1HostPathVolumeSource(
                    path='{}{}'.format(setting.VOLUME_PATH, self.instance_name)))
        else:
            raise APIException(detail='storage type only local or nfs',
                                   code=status.HTTP_409_CONFLICT)
        return persistent_volume