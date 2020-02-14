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


class TraversalDict(object):
    def __init__(self):
        self.result = None

    def traversal(self, input_dict, input_key, is_list_value):
        for k, v in input_dict.items():
            if isinstance(v, list):
                if is_list_value and k == input_key:
                    self.result = v
                    break
                for val in v:
                    if isinstance(val, dict):
                        self.traversal(val, input_key, is_list_value)
                    elif k == input_key:
                        self.result = val
                        break
            elif isinstance(v, dict):
                self.traversal(v, input_key, is_list_value)
            elif k == input_key:
                self.result = v
                break
