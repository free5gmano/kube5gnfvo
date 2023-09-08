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
from utils.tosca_paser.base_template import BaseTemplate
from utils.tosca_paser.traversal_dict import TraversalDict


class EntityTemplate(BaseTemplate):
    def __init__(self, template, name):
        super().__init__(template)
        self.name = name

    def _validate_fields(self):
        pass

    def _assign_template(self, template, name):
        pass

    def _get_properties(self, properties=None, properties_list=None, properties_dict=None):
        if not self._validate_properties():
            return None

        return self.collect_resquest(properties, self.PROPERTIES, properties_list, properties_dict)

    @abstractmethod
    def _validate_properties(self):
        pass

    def _get_capabilities(self, capabilities=None, capabilities_list=None, capabilities_dict=None):
        if not self._validate_capabilities():
            return None

        return self.collect_resquest(capabilities, self.CAPABILITIES, capabilities_list, capabilities_dict)

    @abstractmethod
    def _validate_capabilities(self):
        pass

    def _get_requirements(self, requirements=None, requirements_list=None, requirements_dict=None):
        if not self._validate_requirements():
            return None

        return self.collect_resquest(requirements, self.REQUIREMENTS, requirements_list, requirements_dict)

    @abstractmethod
    def _validate_requirements(self):
        pass

    def _get_attributes(self, attributes=None, attributes_list=None, attributes_dict=None):
        if not self._validate_attributes():
            return None

        return self.collect_resquest(attributes, self.ATTRIBUTES, attributes_list, attributes_dict)

    @abstractmethod
    def _validate_attributes(self):
        pass

    def _get_artifacts(self):
        if not self._validate_artifacts():
            return None

        _artifacts = dict()
        for _artifact in self.template.get(self.ARTIFACTS):
            _artifacts[_artifact] = dict()
            specific_artifact = self.template.get(self.ARTIFACTS).get(_artifact)
            for _artifact_value in specific_artifact:
                _artifacts[_artifact][_artifact_value] = specific_artifact.get(_artifact_value)

        return _artifacts

    @abstractmethod
    def _validate_artifacts(self):
        pass

    def traversal_value(self, input_value, range_key, result_dict, is_list, is_dict):
        if isinstance(input_value, tuple) or isinstance(input_value, list):
            for key in input_value:
                traversal_dict = TraversalDict()
                traversal_dict.traversal(self.template.get(range_key), key, is_list, is_dict)
                result_dict[key] = traversal_dict.result
        else:
            traversal_dict = TraversalDict()
            traversal_dict.traversal(self.template.get(range_key), input_value, is_list, is_dict)
            result_dict[input_value] = traversal_dict.result

    def collect_resquest(self, data=None, _attribute=None, data_list=None, data_dict=None):
        result = dict()
        if data:
            self.traversal_value(data, _attribute, result, False, False)

        if data_list:
            self.traversal_value(data_list, _attribute, result, True, False)

        if data_dict:
            self.traversal_value(data_dict, _attribute, result, False, True)

        return result
