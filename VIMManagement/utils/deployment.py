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
from VIMManagement.utils.kubernetes_api import KubernetesApi


class DeploymentClient(KubernetesApi):
    def __init__(self, *args, **kwargs):
        self.config_path = kwargs['config_path'] if 'config_path' in kwargs else None
        self.tun = kwargs['tun'] if 'tun' in kwargs else None
        if 'memory' in kwargs and 'cpu' in kwargs:
            self.memory = kwargs['memory']
            self.cpu = kwargs['cpu']
        self.protocol = kwargs['protocol'] if 'protocol' in kwargs else None
        if 'ports' in kwargs and 'service_name' in kwargs:
            self.ports = kwargs['ports']
            self.service_name = kwargs['service_name']
        self.mount_path = kwargs['mount_path'] if 'mount_path' in kwargs else None
        self.command = kwargs['command'] if 'command' in kwargs else None
        self.env = kwargs['env'] if 'env' in kwargs else None
        if 'image' in kwargs and 'replicas' in kwargs:
            self.image = kwargs['image']
            self.replicas = kwargs['replicas']
        if 'cp_count' in kwargs:
            self.cp_count = kwargs['cp_count']
        super().__init__(*args, **kwargs)

    def read_resource(self, **kwargs):
        return self.app_v1.read_namespaced_deployment(self.instance_name, self.namespace)

    def create_resource(self, **kwargs):
        self.app_v1.create_namespaced_deployment(self.namespace, self.resource)

    def patch_resource(self, **kwargs):
        self.resource.spec = self._get_deployment_spec()
        self.app_v1.patch_namespaced_deployment(
            self.instance_name, self.namespace, self.resource)

    def delete_resource(self, **kwargs):
        self.app_v1.delete_namespaced_deployment(
            name=self.instance_name, namespace=self.namespace, body=self.delete_options)

    def instance_specific_resource(self, **kwargs):
        deployment = self.kubernetes_client.V1Deployment(api_version="apps/v1", kind="Deployment")
        deployment.metadata = self.kubernetes_client.V1ObjectMeta(
            name=self.instance_name, namespace=self.namespace)
        deployment.spec = self._get_deployment_spec()
        return deployment

    def _get_deployment_spec(self):
        deployment_match_label = {
            "app": self.service_name if self.service_name else self.instance_name}
        deployment_meta = self.kubernetes_client.V1ObjectMeta(labels=deployment_match_label)
        volume_mounts = list()
        volumes = list()
        if self.config_path:
            for _ in self.config_path.split(","):
                path = os.path.split(_.strip())
                volume_name = "{}-{}".format(
                    self.instance_name, path[1] if "." not in path[1] else path[1].split(".")[0])
                volume_mounts.append(self._get_volume_mount(volume_name, _.strip(), path[1]))
                volumes.append(self._get_volume(
                    name=volume_name, config_map=self.kubernetes_client.V1ConfigMapVolumeSource(
                        name=volume_name, items=[{"key": path[1], "path": path[1]}])))

        init_containers = list()
        if self.cp_count:
            deployment_meta.annotations = {'k8s.v1.cni.cncf.io/networks': 'ovs-net-1'}
            env_var = self.kubernetes_client.V1EnvVar(
                name='POD_NAME', value_from=self.kubernetes_client.V1EnvVarSource(
                    field_ref=self.kubernetes_client.V1ObjectFieldSelector(
                        api_version='v1', field_path='metadata.name')))
            while self.cp_count:
                init_containers.append(self.kubernetes_client.V1Container(
                    name='init-network-client{}'.format(self.cp_count), image='free5gmano/networking-controller',
                    command=["./ip_service"], args=['-d', self.instance_name],
                    env=[env_var],
                    security_context=self.kubernetes_client.V1SecurityContext(privileged=True)))
                self.cp_count -= 1

        security_context = None
        if self.tun:
            volume_mounts.append(self._get_volume_mount(
                name=self.instance_name, mount_path=self.tun))
            volumes.append(
                self._get_volume(name=self.instance_name,
                                 host_path=self.kubernetes_client.V1HostPathVolumeSource(path=self.tun)))
            security_context = self.kubernetes_client.V1SecurityContext(
                privileged=True, capabilities=self.kubernetes_client.V1Capabilities(add=["NET_ADMIN", "SYS_TIME"]))

        resource = self.kubernetes_client.V1ResourceRequirements(
            limits={"memory": self.memory, "cpu": self.cpu}, requests={"memory": self.memory, "cpu": self.cpu})

        container_ports = list()
        if self.ports and self.service_name:
            if isinstance(self.ports, int):
                container_ports.append(self._get_container_port(self.ports))
            else:
                container_ports = [self._get_container_port(_.strip()) for _ in self.ports.split(",")]

        if self.mount_path:
            volume_mounts.append(self._get_volume_mount(
                name=self.instance_name, mount_path=self.mount_path))
            volumes.append(self._get_volume(
                name=self.instance_name,
                persistent_volume_claim=self.kubernetes_client.V1PersistentVolumeClaimVolumeSource(
                    claim_name=self.instance_name)))

        command = [_.strip() for _ in self.command.split(',')] if self.command else None
        env = self.env if self.env else None
        container = self.kubernetes_client.V1Container(
            name=self.instance_name, image=self.image, volume_mounts=volume_mounts, command=command,
            env=env, resources=resource, security_context=security_context, ports=container_ports)
        pod_spec = self.kubernetes_client.V1PodSpec(
            containers=[container], volumes=volumes, init_containers=init_containers)
        return self.kubernetes_client.V1DeploymentSpec(
            replicas=self.replicas,
            selector=self.kubernetes_client.V1LabelSelector(match_labels=deployment_match_label),
            template=self.kubernetes_client.V1PodTemplateSpec(
                spec=pod_spec, metadata=deployment_meta))

    def _get_container_port(self, port):
        return self.kubernetes_client.V1ContainerPort(container_port=int(port), protocol=self.protocol)

    def _get_volume_mount(self, name, mount_path, sub_path=None):
        return self.kubernetes_client.V1VolumeMount(
            name=name, mount_path=mount_path, sub_path=sub_path)

    def _get_volume(self, name, config_map=None, host_path=None, persistent_volume_claim=None):
        return self.kubernetes_client.V1Volume(
            name=name, config_map=config_map, host_path=host_path, persistent_volume_claim=persistent_volume_claim)
