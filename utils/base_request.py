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

import requests
import json


class BaseRequest(object):
    TOSCA_TYPE = (USER_ERROR, SERVER_ERROR) = \
        ('4', '5')

    def __init__(self, base_uri, **kwargs):
        self.base_uri = base_uri
        self.auth_account = None
        self.auth_password = None
        if 'auth_account' in kwargs and 'auth_password' in kwargs:
            self.auth_account = kwargs['auth_account']
            self.auth_password = kwargs['auth_password']

    def get(self, uri):
        respond = requests.get(url="{}{}".format(self.base_uri, uri),
                               auth=(self.auth_account, self.auth_password))
        return self._validate_status(respond)

    def post(self, uri, data: dict):
        respond = requests.post(url="{}{}".format(self.base_uri, uri),
                                auth=(self.auth_account, self.auth_password),
                                data=json.dumps(data))
        return self._validate_status(respond)

    def delete(self, uri):
        respond = requests.delete(url="{}{}".format(self.base_uri, uri),
                                  auth=(self.auth_account, self.auth_password))
        return self._validate_status(respond)

    def _validate_status(self, respond):
        status_code = str(respond.status_code)[0]
        if status_code[0] == self.USER_ERROR or status_code[0] == self.SERVER_ERROR:
            # raise ValueError(respond.text)
            return False
            # raise ValueError(respond.text)
        else:
            return respond
