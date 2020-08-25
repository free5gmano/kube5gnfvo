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
from os_ma_nfvo.settings import ONOS_IP
from utils.base_request import BaseRequest


class ONOSClient(BaseRequest):
    onos_account = 'onos'
    onos_password = 'rocks'
    onos_base_uri = ONOS_IP

    def __init__(self):
        super().__init__(
            self.onos_base_uri, auth_account=self.onos_account, auth_password=self.onos_password)

    def register_sfc(self, body: dict):
        self.post('register', data=body)

    def notification_sf_info(self, body: dict):
        self.post('notification', data=body)

    def read_sfc(self, body: dict):
        return self.post('read', data=body)

    def remove_sfc(self, body: dict):
        self.post('delete', data=body)
