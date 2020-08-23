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


class ConfigMapClient(KubernetesApi):
    def __init__(self, *args, **kwargs):
        self.config_file_name = kwargs['config_file_name'] if 'config_file_name' in kwargs else None
        self.config_file_content = kwargs['config_file_content'] if 'config_file_content' in kwargs else None
        kwargs['instance_name'] = self.config_file_name if "." not in self.config_file_name else \
            self.config_file_name.split(".")[0]
        super().__init__(*args, **kwargs)

    def read_resource(self, **kwargs):
        return self.core_v1.read_namespaced_config_map(self.instance_name, self.namespace)

    def create_resource(self, **kwargs):
        self.core_v1.create_namespaced_config_map(self.namespace, self.resource)

    def patch_resource(self, **kwargs):
        self.resource.data = {self.config_file_name: self.config_file_content}
        self.core_v1.patch_namespaced_config_map(self.instance_name, self.namespace, self.resource)

    def delete_resource(self, **kwargs):
        self.core_v1.delete_namespaced_config_map(
            name=self.instance_name, namespace=self.namespace, body=self.delete_options)

    def instance_specific_resource(self, **kwargs):
        config_map = self.kubernetes_client.V1ConfigMap(api_version="v1", kind="ConfigMap")
        config_map.data = {self.config_file_name: self.config_file_content}
        config_map.metadata = self.kubernetes_client.V1ObjectMeta(name=self.instance_name)
        return config_map
