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
from VnfPackageManagement.serializers import vnf_package_base_path
from utils.file_manipulation import walk_file
from utils.process_package.base_process import BaseProcess


class ProcessVNFInstance(BaseProcess):

    def __init__(self, package_id, vnf_instance_name=None):
        super().__init__(package_id)
        self.vnf_instance_name = None
        if vnf_instance_name:
            self.vnf_instance_name = vnf_instance_name.lower()

    def get_root_path(self):
        root, dirs, files = walk_file('{}{}'.format(vnf_package_base_path, self.package_id), 'package_content')
        return '{}/{}/'.format(root, dirs.pop(0))

    def process_template(self, topology_template):
        vnf = list()
        for vdu in topology_template.node_templates.integration_vnf:
            vnf.append(topology_template.node_templates.integration_vnf[vdu])
        return vnf

    def process_instance(self, topology_template):
        node_template = topology_template.node_templates
        policy_template = topology_template.policies
        for integration_vnf in node_template.integration_vnf:
            vdu = node_template.integration_vnf[integration_vnf]['info']
            vl = node_template.integration_vnf[integration_vnf]['vl']
            vdu_info = dict()
            self.process_artifacts(vdu, vdu_info)

            if vdu.attributes['ports'] and vdu.attributes['name_of_service']:
                self.process_service(vdu=vdu)

            if vdu.requirements and vdu.requirements['size_of_storage'] and vdu.requirements['path_of_storage']:
                vdu_info.update(vdu.requirements)
                self.process_persistent_volume_claim(vdu=vdu)
                self.process_persistent_volume(vdu=vdu)

            if policy_template:
                vdu_scaling = policy_template.vdu_scaling
                for scale in vdu_scaling:
                    if integration_vnf in scale.targets:
                        vdu_info['max_instances'] = scale.properties['max_instances']
                        self.process_horizontal_pod_autoscaler(vdu=vdu, scale=scale.properties)
                        break

            vdu_info.update(vdu.properties)
            vdu_info.update(vdu.attributes)
            vdu_info.update(vdu.capabilities)
            self.process_deployment(vl=vl, vdu_info=vdu_info)

    def process_artifacts(self, vdu, vnf_info):
        artifacts = vdu.artifacts
        deploy_path = list()
        for artifact_name in artifacts:
            artifact = artifacts[artifact_name]
            if artifact['type'] != vdu.SW_IMAGE:
                path = os.path.split(artifact['deploy_path'])
                if "." not in path[1]:
                    artifacts_name = path[1]
                else:
                    artifacts_name = path[1].split(".")[0]

                self.process_config_map(artifacts_path=self.root_path + artifact['file'],
                                        artifacts_name=artifacts_name.lower(), namespace=vdu.attributes['namespace'])
                deploy_path.append(artifact['deploy_path'])
            else:
                vnf_info['image'] = artifact['file']

        if deploy_path.__len__() > 0:
            vnf_info['config_map_mount_path'] = deploy_path
        else:
            vnf_info['config_map_mount_path'] = None

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
