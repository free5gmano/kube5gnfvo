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

from utils.tosca_paser.base_template import BaseTemplate
from utils.tosca_paser.vnffg_template import VNFFGTemplate


class GroupTemplate(BaseTemplate):
    def __init__(self, template):
        self.vnffg = list()
        super().__init__(template)

    def _assign_template(self, template, name):
        if self.TOSCA_VNFFG == template.get(self.TYPE):
            self.vnffg.append(VNFFGTemplate(template, name))
