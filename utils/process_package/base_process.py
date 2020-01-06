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

from abc import abstractmethod

from VnfPackageManagement.serializers import vnf_package_base_path
from utils.file_manipulation import walk_file
from utils.process_package.base_package import BasePackage


class BaseProcess(BasePackage):
    def __init__(self, vnf_package_id):
        self.vnf_package_id = vnf_package_id
        super().__init__(self.get_root_path())

    def process_definitions(self):
        self.process_topology_template(self.topology_template)
        for node_template in self.topology_template.node_templates:
            self.process_node_template(node_template)

    def get_root_path(self):
        root, dirs, files = walk_file('{}{}'.format(vnf_package_base_path, self.vnf_package_id), 'package_content')
        return '{}/{}/'.format(root, dirs.pop(0))

    @abstractmethod
    def process_node_template(self, node_template):
        pass

    @abstractmethod
    def process_topology_template(self, topology_template):
        pass
