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
import json
import os
from VIMManagement.utils.kubernetes_api import KubernetesApi
from utils.tosca_paser.cp_template import SR_IOV


class DeploymentClient(KubernetesApi):
    def __init__(self, *args, **kwargs):
        self.config_map_mount_path = kwargs['config_map_mount_path'] if 'config_map_mount_path' in kwargs else None
        self.tun = kwargs['tun'] if 'tun' in kwargs else None
        if 'virtual_mem_size' in kwargs and 'num_virtual_cpu' in kwargs:
            self.virtual_mem_size = kwargs['virtual_mem_size']
            self.num_virtual_cpu = kwargs['num_virtual_cpu']
        self.protocol = kwargs['protocol'] if 'protocol' in kwargs else None
        if 'ports' in kwargs and 'name_of_service' in kwargs:
            self.ports = kwargs['ports']
            self.name_of_service = kwargs['name_of_service']
        if 'nodeport' in kwargs and 'name_of_nodeport' in kwargs:
            self.nodeport = kwargs['nodeport']
            self.name_of_nodeport = kwargs['name_of_nodeport']
        self.path_of_storage = kwargs['path_of_storage'] if 'path_of_storage' in kwargs else None
        self.command = kwargs['command'] if 'command' in kwargs else None
        self.env = kwargs['env'] if 'env' in kwargs else None
        if 'image' in kwargs and 'replicas' in kwargs:
            self.image = kwargs['image']
            self.replicas = kwargs['replicas']
        self.network_name = kwargs['network_name'] if 'network_name' in kwargs else None
        self.labels = kwargs['labels'] if 'labels' in kwargs and isinstance(kwargs['labels'], dict) else None
        self.sriov_type = 'intel.com/intel_sriov_netdevice'
        self.apply_cluster = kwargs['apply_cluster'] if 'apply_cluster' in kwargs else None
        if not self.apply_cluster:
            self.core_v1 = self.kubernetes_client.CoreV1Api(api_client=config.new_client_from_config(context=self.apply_cluster))
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
            name=self.instance_name, namespace=self.namespace, labels=self.labels)
        deployment.spec = self._get_deployment_spec()
        return deployment

    def _get_deployment_spec(self):
        deployment_match_label = {
            "app": self.name_of_service if self.name_of_service else self.instance_name,
            "nodeport": self.name_of_nodeport if self.name_of_nodeport else self.instance_name,
            }
        deployment_meta = self.kubernetes_client.V1ObjectMeta(labels=deployment_match_label)
        volume_mounts = list()
        volumes = list()
        default_mode = None

        limits = {"memory": self.virtual_mem_size, "cpu": self.num_virtual_cpu}
        requests = {"memory": self.virtual_mem_size, "cpu": self.num_virtual_cpu}

        if self.config_map_mount_path:
            for _ in self.config_map_mount_path:
                path = os.path.split(_)
                if '.' not in path[1]:
                    key_name = path[1].lower()
                else:
                    dot_path_list = path[1].split('.')
                    key_name = (path[0].split('/')[path[0].split('/').__len__()-1]+'-'+dot_path_list[0]).lower()
                    if 'sh' in dot_path_list[1].lower():
                        default_mode = 0o777

                volume_mounts.append(self._get_volume_mount(key_name, _.strip(), path[1]))
                volumes.append(self._get_volume(
                    name=key_name, config_map=self.kubernetes_client.V1ConfigMapVolumeSource(
                        name=key_name, items=[{"key": key_name, "path": path[1]}],
                        default_mode=default_mode)))

        init_containers = list()
        if self.network_name.__len__() > 0:
            sr_iov_count = 0
            env_var = self.kubernetes_client.V1EnvVar(
                name='POD_NAME', value_from=self.kubernetes_client.V1EnvVarSource(
                    field_ref=self.kubernetes_client.V1ObjectFieldSelector(
                        api_version='v1', field_path='metadata.name')))
            annotations_name = str()
            for idx, net_info in enumerate(self.network_name):
                if idx == self.network_name.__len__() - 1:
                    annotations_name += net_info['network_name']
                else:
                    annotations_name += '{},'.format(net_info['network_name'])
                init_containers.append(self.kubernetes_client.V1Container(
                    name='init-network-client{}'.format(net_info['network_name']),
                    image='tw0927041027/init-network-setting',
                    command=["./ip_service"], args=['-d', self.instance_name, '-n', 'net{}'.format(idx + 1),
                                                    '-c', json.dumps(net_info['ip_address'])],
                    env=[env_var],
                    security_context=self.kubernetes_client.V1SecurityContext(privileged=True)))

                if net_info['type'] == SR_IOV:
                    sr_iov_count = +1

            deployment_meta.annotations = {'k8s.v1.cni.cncf.io/networks': annotations_name}
            requests.update({self.sriov_type: sr_iov_count})
            limits.update({self.sriov_type: sr_iov_count})

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
            limits=limits,
            requests=requests)

        container_ports = list()
        if self.ports and self.name_of_service:
            for port in self.ports:
                container_ports.append(self._get_container_port(port))

        if self.path_of_storage:
            volume_mounts.append(self._get_volume_mount(
                name=self.instance_name, mount_path=self.path_of_storage))
            volumes.append(self._get_volume(
                name=self.instance_name,
                persistent_volume_claim=self.kubernetes_client.V1PersistentVolumeClaimVolumeSource(
                    claim_name=self.instance_name)))

        env = self.env if self.env else None
        container = self.kubernetes_client.V1Container(
            name=self.instance_name, image=self.image, volume_mounts=volume_mounts, command=self.command,
            env=env, resources=resource, security_context=security_context, ports=container_ports)
        pod_spec = self.kubernetes_client.V1PodSpec(
            containers=[container], volumes=volumes, init_containers=init_containers)
        return self.kubernetes_client.V1DeploymentSpec(
            replicas=self.replicas,
            selector=self.kubernetes_client.V1LabelSelector(match_labels=deployment_match_label),
            template=self.kubernetes_client.V1PodTemplateSpec(
                spec=pod_spec, metadata=deployment_meta))

    def _get_container_port(self, port: int):
        return self.kubernetes_client.V1ContainerPort(
            name='{}{}'.format(self.instance_name[-10:], port),
            container_port=port,
            protocol=self.protocol)

    def _get_volume_mount(self, name, mount_path, sub_path=None):
        return self.kubernetes_client.V1VolumeMount(
            name=name, mount_path=mount_path, sub_path=sub_path)

    def _get_volume(self, name, config_map=None, host_path=None, persistent_volume_claim=None):
        return self.kubernetes_client.V1Volume(
            name=name, config_map=config_map, host_path=host_path, persistent_volume_claim=persistent_volume_claim)
