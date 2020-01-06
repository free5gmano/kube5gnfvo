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

from utils.tosca_paser.node_template import NodeTemplate
from utils.tosca_paser.traversal_dict import TraversalDict


class NSTemplate(NodeTemplate):
    def get_attributes(self, key):
        pass

    NS_ATTRIBUTE = (DESCRIPTOR_ID, DESIGNER, NAME, INVARIANT_ID, VERSION, CONSTITUENT_VNFD) = \
        ('descriptor_id', 'designer', 'name', 'invariant_id', 'version', 'constituent_vnfd')

    def __init__(self, name, node_templates):
        super().__init__(name, node_templates)
        self.descriptor_id = self.get_properties(self.DESCRIPTOR_ID)
        self.designer = self.get_properties(self.DESIGNER)
        self.name = self.get_properties(self.NAME)
        self.invariant_id = self.get_properties(self.INVARIANT_ID)
        self.version = self.get_properties(self.VERSION)
        self.constituent_vnfd = self.get_properties(self.CONSTITUENT_VNFD)

    def get_type(self):
        return self.TOSCA_NS

    def get_requirements(self, key):
        pass

    def get_capabilities(self, key):
        pass

    def get_properties(self, key):
        traversal_dict = TraversalDict(True) if key == self.CONSTITUENT_VNFD else TraversalDict(False)
        traversal_dict.traversal(self.templates.get(self.PROPERTIES), key)
        return traversal_dict.result
