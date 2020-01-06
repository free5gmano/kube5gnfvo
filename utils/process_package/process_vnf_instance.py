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
from abc import abstractmethod
from utils.process_package.base_process import BaseProcess


class ProcessVNFInstance(BaseProcess):
    def __init__(self, vnf_package_id, vnf_instance_name=None):
        super().__init__(vnf_package_id)
        self.vnf_instance_name = None
        if vnf_instance_name:
            self.vnf_instance_name = vnf_instance_name.lower()

        self.connect_point = list()
        self.vdu = list()
        self.scale_policy = list()

    def process_node_template(self, node_template):
        if 'tosca.nodes.nfv.VduCpd' in node_template.get_type():
            self.connect_point.append(node_template)
        elif 'tosca.nodes.nfv.Vdu.Compute' in node_template.get_type():
            self.vdu.append(node_template)
            if node_template.config_path:
                self.process_artifacts(node_template)
            if node_template.ports and node_template.name_of_service:
                self.process_service(vdu=node_template)
            if node_template.storage_size and node_template.storage_path:
                self.process_persistent_volume_claim(vdu=node_template)
                self.process_persistent_volume(vdu=node_template)

    def process_topology_template(self, topology_template):
        if topology_template.policies:
            self.scale_policy = topology_template.policies

    def process_artifacts(self, vdu):
        for artifacts_path in self.entry_artifacts.split(","):
            path = artifacts_path.strip()
            self.process_config_map(
                artifacts_path=self.root_path + path,
                artifacts_name=os.path.split(path)[1],
                namespace=vdu.namespace)

    @abstractmethod
    def process_persistent_volume(self, **kwargs):
        pass

    @abstractmethod
    def process_persistent_volume_claim(self, **kwargs):
        pass

    @abstractmethod
    def process_service(self, **kwargs):
        pass

    @abstractmethod
    def process_deployment(self, **kwargs):
        pass

    @abstractmethod
    def process_config_map(self, **kwargs):
        pass

    @abstractmethod
    def process_horizontal_pod_autoscaler(self, **kwargs):
        pass
