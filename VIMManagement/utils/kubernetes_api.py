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

from VIMManagement.utils.base_kubernetes import BaseKubernetes
from abc import abstractmethod


class KubernetesApi(BaseKubernetes):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if 'instance_name' in kwargs:
            self.instance_name = kwargs['instance_name']
        if 'namespace' in kwargs:
            self.namespace = kwargs['namespace']
        self.delete_options = self.kubernetes_client.V1DeleteOptions()
        self.resource = None

    def _get_resource(self):
        try:
            resource = self.read_resource()
        except self.ApiException as e:
            if e.status == 404:
                return None
            raise
        return resource

    def handle_create_or_update(self):
        self.resource = self._get_resource()
        if not self.resource:
            self.resource = self.instance_specific_resource()
            self.create_resource()
        else:
            self.patch_resource()

    def handle_delete(self):
        service = self._get_resource()
        if service:
            self.delete_resource()

    @abstractmethod
    def read_resource(self, **kwargs):
        pass

    @abstractmethod
    def create_resource(self, **kwargs):
        pass

    @abstractmethod
    def patch_resource(self, **kwargs):
        pass

    @abstractmethod
    def delete_resource(self, **kwargs):
        pass

    @abstractmethod
    def instance_specific_resource(self, **kwargs):
        pass
