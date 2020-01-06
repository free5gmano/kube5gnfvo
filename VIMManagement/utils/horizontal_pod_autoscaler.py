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


class HorizontalPodAutoscalerClient(KubernetesApi):
    def __init__(self, *args, **kwargs):
        if 'max_replicas' in kwargs and 'min_replicas' in kwargs \
                and 'target_cpu_utilization_percentage' in kwargs:
            self.max_replicas = kwargs['max_replicas']
            self.min_replicas = kwargs['min_replicas']
            self.target_cpu_utilization_percentage = kwargs['target_cpu_utilization_percentage']
        super().__init__(*args, **kwargs)

    def read_resource(self, **kwargs):
        return self.auto_scaling_v1.read_namespaced_horizontal_pod_autoscaler(
            self.instance_name, self.namespace)

    def create_resource(self, **kwargs):
        self.auto_scaling_v1.create_namespaced_horizontal_pod_autoscaler(
            self.namespace, self.resource)

    def patch_resource(self, **kwargs):
        self.auto_scaling_v1.patch_namespaced_horizontal_pod_autoscaler(
            self.instance_name, self.namespace, self.resource)

    def delete_resource(self, **kwargs):
        self.auto_scaling_v1.delete_namespaced_horizontal_pod_autoscaler(
            name=self.instance_name, namespace=self.namespace, body=self.delete_options)

    def instance_specific_resource(self, **kwargs):
        horizontal_pod_autoscaler = self.kubernetes_client.V1HorizontalPodAutoscaler(
            api_version='autoscaling/v1', kind='HorizontalPodAutoscaler')
        horizontal_pod_autoscaler.metadata = self.kubernetes_client.V1ObjectMeta(
            name=self.instance_name)
        horizontal_pod_autoscaler.spec = self.kubernetes_client.V1HorizontalPodAutoscalerSpec(
            max_replicas=self.max_replicas, min_replicas=self.min_replicas,
            scale_target_ref=self.kubernetes_client.V1CrossVersionObjectReference(
                api_version='apps/v1', kind='Deployment', name=self.instance_name),
            target_cpu_utilization_percentage=self.target_cpu_utilization_percentage)
        return horizontal_pod_autoscaler
