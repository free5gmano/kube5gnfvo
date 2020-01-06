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

from utils.tosca_paser.cp_template import CPTemplate
from utils.tosca_paser.ns_template import NSTemplate
from utils.tosca_paser.policies_template import PoliciesTemplate
from utils.tosca_paser.vdu_template import VDUTemplate


class TopologyTemplate(object):
    ATTRIBUTE = (NODE_TEMPLATES, POLICIES) = ('node_templates', 'policies')

    def __init__(self, topology_template):
        self.template = topology_template
        self.policies = None
        if self.template:
            self.node_templates = self._node_templates()
            if self.template.get(self.POLICIES):
                self.policies = self._policeies_template()

    def _validate_node_templates(self):
        node_templates = self.template.get(self.NODE_TEMPLATES)
        if node_templates and not isinstance(node_templates, dict):
            raise ValueError("node templates type must is dict")
        return node_templates

    def _validate_policies_templates(self):
        policies_templates = self.template.get(self.POLICIES)
        if policies_templates and not isinstance(policies_templates, dict):
            raise ValueError("policies templates type must is dict")
        return policies_templates

    # TODO multiple
    def _node_templates(self):
        node_templates = list()
        node_template = self._validate_node_templates()
        if node_template:
            for name in node_template:
                node_type = node_template[name]["type"]
                template = None
                if 'tosca.nodes.nfv.VduCpd' in node_type:
                    template = CPTemplate(name, node_template)
                elif 'tosca.nodes.nfv.Vdu.Compute' in node_type:
                    template = VDUTemplate(name, node_template)
                elif 'tosca.nodes.nfv.NS' in node_type:
                    template = NSTemplate(name, node_template)
                node_templates.append(template)
            return node_templates

    def _policeies_template(self):
        policies_templates = list()
        policies_template = self._validate_policies_templates()
        if policies_template:
            for name in policies_template:
                if 'tosca.capabilities.Scalable' == policies_template[name]["type"]:
                    policies_templates.append(PoliciesTemplate(name, policies_template))
            return policies_templates
