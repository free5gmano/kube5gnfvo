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
from abc import abstractmethod


class BaseTemplate(object):
    TOSCA_TYPE = (TOSCA_VNF, TOSCA_VDU, TOSCA_CP, TOSCA_NS, TOSCA_SCALING, TOSCA_VL, TOSCA_FP, TOSCA_VNFFG, TOSCA_SERVICE_MESH) = \
        ('tosca.nodes.nfv.VNF', 'tosca.nodes.nfv.Vdu.Compute', 'tosca.nodes.nfv.Cpd',
         'tosca.nodes.nfv.NS', 'tosca.policies.Scaling', 'tosca.nodes.nfv.VnfVirtualLink',
         'tosca.nodes.nfv.FP', 'tosca.groups.nfv.VNFFG', 'tosca.nodes.nfv.SM')
    ATTRIBUTE = (TYPE, PROPERTIES, CAPABILITIES, REQUIREMENTS, ATTRIBUTES, ARTIFACTS, TARGETS) = \
        ('type', 'properties', 'capabilities', 'requirements', 'attributes', 'artifacts', 'targets')

    def __init__(self, template):
        self.template = template
        self._validate_fields()

    def _validate_fields(self):
        if not self.template:
            self._value_empty_exception('topology template', 'node template')

        for name in self.template:
            specific_template = self.template.get(name)
            if not self._validate_type(name, specific_template.get(self.TYPE)):
                break

            for attribute in list(specific_template):
                if attribute not in self.ATTRIBUTE:
                    self._value_error_exception('node template', attribute)

            self._assign_template(specific_template, name)

    def _validate_type(self, name, template):
        if not template or template not in self.TOSCA_TYPE:
            self._value_error_exception(name, self.TYPE)

        return True

    def _value_error_exception(self, who, what):
        raise ValueError('{who} has illegal {what} attribute'.format(who=who, what=what))

    def _value_empty_exception(self, who, what):
        raise ValueError('{who} need {what} attribute'.format(who=who, what=what))

    @abstractmethod
    def _assign_template(self, template, name):
        pass
