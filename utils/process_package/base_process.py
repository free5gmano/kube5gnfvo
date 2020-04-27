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
from utils.etcd_client.etcd_client import EtcdClient
from utils.process_package.base_package import BasePackage

from abc import abstractmethod

from utils.etcd_client.etcd_client import EtcdClient
from utils.process_package.base_package import BasePackage


class BaseProcess(BasePackage):
    def __init__(self, package_id):
        self.package_id = package_id
        super().__init__(self.get_root_path())
        self.etcd_client = EtcdClient()

    @abstractmethod
    def get_root_path(self):
        pass

    @abstractmethod
    def process_template(self, **kwargs):
        pass

    @abstractmethod
    def process_instance(self, **kwargs):
        pass
