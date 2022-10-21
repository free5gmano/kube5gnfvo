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
from utils.tosca_paser.vdu_scaling_template import VduScalingTemplate


class PolicyTemplate(BaseTemplate):
    def __init__(self, template):
        self.vdu_scaling = list()
        super().__init__(template)

    def _assign_template(self, template, name):
        if self.TOSCA_SCALING == template.get(self.TYPE):
            self.vdu_scaling.append(VduScalingTemplate(template, name))
