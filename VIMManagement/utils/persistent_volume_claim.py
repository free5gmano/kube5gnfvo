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


class PersistentVolumeClaimClient(KubernetesApi):
    def __init__(self, *args, **kwargs):
        if 'storage_size' in kwargs:
            self.storage_size = kwargs['storage_size']
        super().__init__(*args, **kwargs)

    def read_resource(self, **kwargs):
        return self.core_v1.read_namespaced_persistent_volume_claim(self.instance_name, self.namespace)

    def create_resource(self, **kwargs):
        self.core_v1.create_namespaced_persistent_volume_claim(self.namespace, self.resource)

    def patch_resource(self, **kwargs):
        self.core_v1.patch_namespaced_persistent_volume_claim(self.instance_name, self.namespace, self.resource)

    def delete_resource(self, **kwargs):
        self.core_v1.delete_namespaced_persistent_volume_claim(
            name=self.instance_name, namespace=self.namespace, body=self.delete_options)

    def instance_specific_resource(self, **kwargs):
        persistent_volume_claim = self.kubernetes_client.V1PersistentVolumeClaim(
            api_version='v1', kind='PersistentVolumeClaim')
        persistent_volume_claim.metadata = self.kubernetes_client.V1ObjectMeta(name=self.instance_name)
        persistent_volume_claim.spec = self.kubernetes_client.V1PersistentVolumeClaimSpec(
            access_modes=["ReadWriteMany"], resources={"requests": {"storage": self.storage_size}})
        return persistent_volume_claim
