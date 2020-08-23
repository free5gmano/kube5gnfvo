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


class ServiceClient(KubernetesApi):
    def __init__(self, *args, **kwargs):
        self.service_type = kwargs['service_type'] if 'service_type' in kwargs else None
        self.ports = kwargs['ports'] if 'ports' in kwargs else None
        self.protocol = kwargs['protocol'] if 'protocol' in kwargs else None
        super().__init__(*args, **kwargs)

    def read_resource(self, **kwargs):
        return self.core_v1.read_namespaced_service(self.instance_name, self.namespace)

    def create_resource(self, **kwargs):
        self.core_v1.create_namespaced_service(self.namespace, self.resource)

    def patch_resource(self, **kwargs):
        self.core_v1.patch_namespaced_service(self.instance_name, self.namespace, self.resource)

    def delete_resource(self, **kwargs):
        self.core_v1.delete_namespaced_service(
            name=self.instance_name, namespace=self.namespace, body=self.delete_options)

    def instance_specific_resource(self, **kwargs):
        service = self.kubernetes_client.V1Service(api_version="v1", kind="Service")
        service.metadata = self.kubernetes_client.V1ObjectMeta(name=self.instance_name)
        service.spec = self.kubernetes_client.V1ServiceSpec(
            selector={'app': self.instance_name}, ports=self._get_service_port(), type=self.service_type)
        return service

    def _get_service_port(self):
        return [self._create_service_port(_) for _ in self.ports]

    def _create_service_port(self, port: int):
        return self.kubernetes_client.V1ServicePort(
            name='{}{}'.format(self.instance_name[-10:], port), port=int(port), protocol=self.protocol)
