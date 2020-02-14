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

import random
import etcd3


class EtcdClient(object):
    def __init__(self, **kwargs):
        self.etcd_domain = 'dual-network-nic-etcd-cluster-client.default.svc.cluster.local'
        self.etcd_port = 2379
        self.ip_pool = '192.168.{}.{}'
        self.instance_name = None
        self.pod_name = None
        self.client = etcd3.client(host=self.etcd_domain, port=self.etcd_port)

    def set_deploy_name(self, instance_name=None, pod_name=None):
        self.instance_name = instance_name
        self.pod_name = pod_name

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.client.close()

    def get_etcd_all_key(self):
        return [path.key.decode("utf-8") for (_, path) in self.client.get_all()]

    def create_ip_pool(self):
        return self._check_valid_ip_address(self._get_random_ip_address())

    def release_pod_ip_address(self):
        for (_, path) in self.client.get_all():
            path = path.key.decode("utf-8")
            if self.instance_name:
                if self.instance_name in path:
                    self.client.delete(path)
            elif self.pod_name:
                if self.pod_name in path:
                    self._recover_ip_address_pool(
                        path.split('/')[1], self._get_deployment_ip(path))
                    self.client.delete(path)

    def _get_deployment_ip(self, path):
        return self.client.get(path)[0].decode("utf-8")

    def _recover_ip_address_pool(self, instance_name, ip_address):
        self.client.put('/{}/pool/{}'.format(instance_name, ip_address), ip_address)

    def _check_valid_ip_address(self, ip_address):
        used_ip_address = self._get_all_saved_ip_address()
        if len(used_ip_address) == 0:
            self._put_valid_ip_address(ip_address)
            return ip_address
        else:
            try:
                while ip_address in used_ip_address:
                    ip_address = self._get_random_ip_address()
                self._put_valid_ip_address(ip_address)
                return ip_address
            except Exception:
                raise

    def check_valid_static_ip_address(self, ip_address, mask):
        used_ip_address = self._get_all_saved_ip_address()
        if len(used_ip_address) == 0:
            self._put_valid_ip_address('{}-{}'.format(ip_address, mask))
        else:
            if ip_address in used_ip_address:
                raise ValueError('CIDR used')
            self._put_valid_ip_address('{}-{}'.format(ip_address, mask))

    def _put_valid_ip_address(self, ip_address):
        self.client.put('/{}/pool/{}'.format(self.instance_name, ip_address), ip_address)

    def _get_all_saved_ip_address(self):
        return [_.decode("utf-8") for _ in dict(self.client.get_prefix('/'))]

    def get_specific_saved_ip_address(self):
        return [_.decode("utf-8").split('-')[0] for _ in dict(self.client.get_prefix('/{}'.format(self.instance_name)))]

    def _get_random_ip_address(self):
        return self.ip_pool.format(random.randint(0, 255), random.randint(1, 254))

    # vm
    def get_vm_cidr(self) -> str:
        ip_address_pool = self._get_not_in_using_ip_address()
        ip_address = ip_address_pool[random.randint(0, len(ip_address_pool) - 1)]
        self._put_used_ip_address(ip_address)
        self._delete_used_ip_address(ip_address)
        if '-' in ip_address:
            return ip_address.replace('-', '/')
        else:
            return '{}/16'.format(ip_address)

    def _get_not_in_using_ip_address(self):
        return [_.decode("utf-8") for _ in dict(self.client.get_prefix('/{}/pool'.format(self.instance_name)))]

    def _put_used_ip_address(self, ip_address):
        self.client.put('/{}/{}/{}'.format(self.instance_name, self.instance_name, ip_address), ip_address)

    def _delete_used_ip_address(self, ip_address):
        self.client.delete('/{}/pool/{}'.format(self.instance_name, ip_address))
