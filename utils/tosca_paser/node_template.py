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
from VIMManagement.utils.network_attachment import NetworkAttachment
from utils.tosca_paser.base_template import BaseTemplate
from utils.tosca_paser.cp_template import CPTemplate
from utils.tosca_paser.fp_template import FPTemplate
from utils.tosca_paser.ns_template import NSTemplate
from utils.tosca_paser.vdu_template import VDUTemplate
from utils.tosca_paser.vl_template import VLTemplate
from utils.tosca_paser.vnf_template import VNFTemplate


class NodeTemplate(BaseTemplate):

    def __init__(self, template):
        self.vnf = list()
        self.vdu = list()
        self.vl = list()
        self.cp = list()
        self.ns = list()
        self.fp = list()
        super().__init__(template)
        self._validate_vl()
        self.integration_vnf = self._Integration_vnf()

    def _assign_template(self, template, name):
        if self.TOSCA_CP == template.get(self.TYPE):
            self.cp.append(CPTemplate(template, name))
        elif self.TOSCA_VDU == template.get(self.TYPE):
            self.vdu.append(VDUTemplate(template, name))
        elif self.TOSCA_VNF == template.get(self.TYPE):
            self.vnf.append(VNFTemplate(template, name))
        elif self.TOSCA_VL == template.get(self.TYPE):
            self.vl.append(VLTemplate(template, name))
        elif self.TOSCA_NS == template.get(self.TYPE):
            self.ns.append(NSTemplate(template, name))
        elif self.TOSCA_FP == template.get(self.TYPE):
            self.fp.append(FPTemplate(template, name))

    def _validate_vl(self):
        network_attachment = NetworkAttachment()
        multus_network_name = network_attachment.list_resource()
        if self.vnf.__len__() > 0:
            for vl in self.vl:
                network_name = vl.properties['network_name']
                if 'management' != network_name and network_name not in multus_network_name:
                    self._value_error_exception('VLTemplate', 'network name')

    def _Integration_vnf(self) -> dict:
        vnf = dict()
        vl = self.vl.copy()
        for cp_info in self.cp:
            for vdu_info in self.vdu:
                if cp_info.requirements['virtual_binding'] == vdu_info.name:
                    if vdu_info.name not in vnf:
                        vnf[vdu_info.name] = dict()
                        vnf[vdu_info.name]['info'] = vdu_info
                        vnf[vdu_info.name]['net'] = list()

                    for vl_info in vl:
                        if cp_info.requirements['virtual_link'] == vl_info.name:
                            integration_net = dict()
                            integration_net[vl_info] = cp_info
                            vnf[vdu_info.name]['net'].append(integration_net)
                            vl.remove(vl_info)
        return vnf
