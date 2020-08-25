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

from django.utils.crypto import random

from VIMManagement.utils.kubernetes_api import KubernetesApi
from utils.etcd_client.etcd_client import EtcdClient

# TODO only testing ubuntu image
from utils.tosca_paser.cp_template import SR_IOV, OVS


class VirtualMachineInstance(KubernetesApi):
    serial = "ABCDFGHJIKLMNOPQRSTUVWXYZ1234567890"

    def __init__(self, *args, **kwargs):
        if 'virtual_mem_size' in kwargs and 'num_virtual_cpu' in kwargs and 'image' in kwargs:
            self.memory = kwargs['virtual_mem_size']
            self.cpu = kwargs['num_virtual_cpu']
            self.image = kwargs['image']
        self.network_name = kwargs['network_name'] if 'network_name' in kwargs else None
        self.user_name = kwargs['user_name'] if 'user_name' in kwargs else None
        self.user_public_key = kwargs['user_public_key'] if 'user_public_key' in kwargs else None
        self.config_map_mount_path = kwargs['config_map_mount_path'] if 'config_map_mount_path' in kwargs else None
        self.command = kwargs['command'] if 'command' in kwargs else None
        self.replicas = kwargs['replicas'] if 'replicas' in kwargs else None
        self.labels = kwargs['labels'] if 'labels' in kwargs and isinstance(kwargs['labels'], dict) else None
        if 'ports' in kwargs and 'name_of_service' in kwargs:
            self.name_of_service = kwargs['name_of_service']
        super().__init__(*args, **kwargs)
        self.etcd_client = EtcdClient()
        self.etcd_client.set_deploy_name(instance_name=self.instance_name, pod_name=None)

    def instance_specific_resource(self, **kwargs):
        virtual_machine_instance_match_label = {
            "app": self.name_of_service if self.name_of_service else self.instance_name}
        virtual_machine_instance_meta = self.kubernetes_client.V1ObjectMeta(labels=virtual_machine_instance_match_label)
        vmirs_spec = self.kubevirt_client.V1VirtualMachineInstanceReplicaSetSpec(
            replicas=self.replicas,
            selector=self.kubevirt_client.V1LabelSelector(match_labels=virtual_machine_instance_match_label),
            template=self.kubevirt_client.V1VirtualMachineInstanceTemplateSpec(
                spec=self._get_virtual_machine_instance_replica_set_spec(), metadata=virtual_machine_instance_meta))
        vmirs = self.kubevirt_client.V1VirtualMachineInstanceReplicaSet(
            api_version="kubevirt.io/v1alpha3", kind="VirtualMachineInstanceReplicaSet", spec=vmirs_spec)
        vmirs.metadata = self.kubernetes_client.V1ObjectMeta(
            name=self.instance_name, namespace=self.namespace, labels=self.labels)
        return vmirs

    def _get_virtual_machine_instance_replica_set_spec(self):
        if isinstance(self.cpu, int):
            self.cpu = str(self.cpu)
        resource = self.kubevirt_client.V1ResourceRequirements(
            requests={'memory': self.memory, 'cpu': self.cpu})
        disks = list()
        disks.append(self.kubevirt_client.V1Disk(
            name='{}-{}'.format(self.instance_name, 'disk'),
            disk=self.kubevirt_client.V1DiskTarget(bus='virtio')))
        disks.append(self.kubevirt_client.V1Disk(
            name='{}-{}'.format(self.instance_name, 'init'),
            disk=self.kubevirt_client.V1DiskTarget(bus='virtio')))
        volumes = list()
        volumes.append(self.kubevirt_client.V1Volume(
            name='{}-{}'.format(self.instance_name, 'disk'),
            container_disk=self.kubevirt_client.V1ContainerDiskSource(image=self.image)))
        mount_script = str()
        if self.config_map_mount_path:
            for _ in self.config_map_mount_path:
                serial = self._get_serial()
                path = os.path.split(_.strip())
                disk_name = path[1].lower() if "." not in path[1] else path[1].split(".")[0].lower()
                disks.append(self.kubevirt_client.V1Disk(
                    name=disk_name, serial=serial, disk=self.kubevirt_client.V1DiskTarget()))
                mount_script += self._mount_configmap(path=path[0], serial=serial)
                volumes.append(self.kubevirt_client.V1Volume(
                    name=disk_name,
                    config_map=self.kubevirt_client.V1ConfigMapVolumeSource(name=disk_name)))

        interface = list()
        interface.append(self.kubevirt_client.V1Interface(
            name='default', masquerade=self.kubevirt_client.V1InterfaceMasquerade()))
        networks = list()
        networks.append(self.kubevirt_client.V1Network(name='default', pod=self.kubevirt_client.V1PodNetwork()))
        if self.network_name.__len__() > 0:
            for idx, net_info in enumerate(self.network_name):
                if net_info['type'] == SR_IOV:
                    interface.append(self.kubevirt_client.V1Interface(
                        name='{}-{}{}'.format(self.instance_name, net_info['network_name'], idx),
                        sriov=self.kubevirt_client.V1InterfaceSRIOV()))
                elif net_info['type'] == OVS:
                    interface.append(self.kubevirt_client.V1Interface(
                        name='{}-{}{}'.format(self.instance_name, net_info['network_name'], idx),
                        bridge=self.kubevirt_client.V1InterfaceBridge()))
                networks.append(
                    self.kubevirt_client.V1Network(
                        name='{}-{}{}'.format(self.instance_name, net_info['network_name'], idx),
                        multus=self.kubevirt_client.V1MultusNetwork(network_name=net_info['network_name'])))

                # TODO ovs-cni can not setting interface name
                interface_name_count = idx + 2
                interface_name = 'enp{}'.format(interface_name_count)
                mount_script += self._multiple_interface(interface_name, net_info['ip_address'][idx])
                interface_name_count += 1
            mount_script += "count=2;for net in `ip link | grep mtu |cut -d ':' -f 2| tail -n {}`;do \
                            sed -i \"s/enp$count/$net/g\" /etc/network/interfaces.d/50-cloud-init.cfg;\
                            count=$(($count+1));  done\n".format(len(self.network_name))
            mount_script += '/etc/init.d/networking restart\n'
        if self.command:
            for _ in self.command:
                mount_script += '{}\n'.format(_)

        volumes.append(self.kubevirt_client.V1Volume(
            name='{}-{}'.format(self.instance_name, 'init'),
            cloud_init_no_cloud=self.kubevirt_client.V1CloudInitNoCloudSource(
                user_data=self._get_user_data(mount_script))))

        devices = self.kubevirt_client.V1Devices(disks=disks, interfaces=interface)
        domain = self.kubevirt_client.V1DomainSpec(resources=resource, devices=devices)
        virtual_machine_instance_spec = self.kubevirt_client.V1VirtualMachineInstanceSpec(
            networks=networks, volumes=volumes, domain=domain, termination_grace_period_seconds=0)
        return virtual_machine_instance_spec

    def patch_resource(self, **kwargs):
        self.kubevirt_api.replace_namespaced_virtual_machine_instance_replica_set(
            name=self.instance_name, namespace=self.namespace, body=self.resource)

    def delete_resource(self, **kwargs):
        self.kubevirt_api.delete_namespaced_virtual_machine_instance_replica_set(
            namespace=self.namespace, name=self.instance_name, body=self.kubevirt_client.V1DeleteOptions())

    def create_resource(self, **kwargs):
        self.kubevirt_api.create_namespaced_virtual_machine_instance_replica_set(
            namespace=self.namespace, body=self.resource)

    def read_resource(self, **kwargs):
        try:
            resource = self.kubevirt_api.read_namespaced_virtual_machine_instance_replica_set(
                name=self.instance_name, namespace=self.namespace)
        except self.kubevirt_client.api_client.ApiException as e:
            if e.status == 404:
                print(
                    "Exception when calling DefaultApi->read_namespaced_virtual_machine_instance_replica_set: %s\n" % e)
                return None
            raise
        return resource

    def _restart_vmis(self):
        self.kubevirt_api.restart(namespace=self.namespace, name=self.instance_name)

    def _get_serial(self):
        return ''.join(random.choice(self.serial) for _ in range(16))

    def _get_user_data(self, mount_script):
        return ('#!/bin/bash\n'
                'export NEW_USER={user_name}\n'
                'export SSH_PUB_KEY="{user_public_key}"\n'
                'sudo adduser -U -m $NEW_USER\n'
                'echo "$NEW_USER:atomic" | chpasswd\n'
                'sudo mkdir /home/$NEW_USER/.ssh\n'
                'sudo echo "$SSH_PUB_KEY" > /home/$NEW_USER/.ssh/authorized_keys\n'
                'sudo chown -R ${NEW_USER}: /home/$NEW_USER/.ssh\n'
                '{mount_script}'
                ).format(user_name=self.user_name, user_public_key=self.user_public_key, NEW_USER='{NEW_USER}',
                         mount_script=mount_script)

    def _multiple_interface(self, interface_name, cidr):
        return ('cat << EOF >> /etc/network/interfaces.d/50-cloud-init.cfg\n'
                'auto {interface_name}\n'
                'iface {interface_name} inet static\n'
                'address {cidr} \n'
                'EOF\n'
                ).format(interface_name=interface_name, cidr=cidr)

    def _mount_configmap(self, path, serial):
        return ('sudo mkdir {config_path}\n'
                'sudo mount /dev/$(lsblk --nodeps -no name,serial | grep {serial} | cut -f1 -d " ") {config_path}\n'
                ).format(config_path=path, serial=serial)
