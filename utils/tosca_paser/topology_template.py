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
from utils.tosca_paser.group_template import GroupTemplate
from utils.tosca_paser.node_template import NodeTemplate
from utils.tosca_paser.policy_template import PolicyTemplate


class TopologyTemplate(object):
    ATTRIBUTE = (NODE_TEMPLATES, POLICIES, GROUP) = ('node_templates', 'policies', 'groups')

    def __init__(self, topology_template):
        self.template = topology_template
        self._validate_field()
        self.node_templates = self._node_templates()
        self.policies = self._policies_template()
        self.group = self._group()

    def _validate_field(self):
        if not self.template:
            raise ValueError('topology template is None')

        for field in self.template:
            if field not in self.ATTRIBUTE:
                raise ValueError('topology template has illegal value')

    def _validate_node_templates(self):
        node_templates = self.template.get(self.NODE_TEMPLATES)
        if node_templates and not isinstance(node_templates, dict):
            raise ValueError("node templates type must is dict")

        return node_templates

    def _validate_group_templates(self):
        group_templates = self.template.get(self.GROUP)
        if not group_templates:
            return None

        if not isinstance(group_templates, dict):
            raise ValueError("groups templates type must is dict")

        return group_templates

    def _validate_policy_templates(self):
        policies_templates = self.template.get(self.POLICIES)
        if not policies_templates:
            return None

        if not isinstance(policies_templates, dict):
            raise ValueError("policies templates type must is dict")

        return policies_templates

    def _node_templates(self):
        node_templates = self._validate_node_templates()
        return NodeTemplate(node_templates)

    def _group(self):
        group_templates = self._validate_group_templates()
        if not group_templates:
            return None

        return GroupTemplate(group_templates)

    def _policies_template(self):
        policy_templates = self._validate_policy_templates()
        if not policy_templates:
            return None

        return PolicyTemplate(policy_templates)
