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

    def _get_properties(self, properties=None, properties_list=None):
        if not self._validate_properties():
            return None

        _properties = dict()
        if properties:
            self.traversal_value(properties, self.PROPERTIES, _properties, False)

        if properties_list:
            self.traversal_value(properties_list, self.PROPERTIES, _properties, True)

        return _properties

    @abstractmethod
    def _validate_properties(self):
        pass

    def _get_capabilities(self, capabilities=None, capabilities_list=None):
        if not self._validate_capabilities():
            return None

        _capabilities = dict()
        if capabilities:
            self.traversal_value(capabilities, self.CAPABILITIES, _capabilities, False)

        if capabilities_list:
            self.traversal_value(capabilities_list, self.CAPABILITIES, _capabilities, True)

        return _capabilities

    @abstractmethod
    def _validate_capabilities(self):
        pass

    def _get_requirements(self, requirements=None, requirements_list=None):
        if not self._validate_requirements():
            return None

        _requirements = dict()
        if requirements:
            self.traversal_value(requirements, self.REQUIREMENTS, _requirements, False)

        if requirements_list:
            self.traversal_value(requirements_list, self.REQUIREMENTS, _requirements, True)

        return _requirements

    @abstractmethod
    def _validate_requirements(self):
        pass

    def _get_attributes(self, attributes=None, attributes_list=None):
        if not self._validate_attributes():
            return None

        _attributes = dict()
        if attributes:
            self.traversal_value(attributes, self.ATTRIBUTES, _attributes, False)

        if attributes_list:
            self.traversal_value(attributes_list, self.ATTRIBUTES, _attributes, True)

        return _attributes

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

    def traversal_value(self, input_value, range_key, result_dict, is_list):
        if isinstance(input_value, tuple) or isinstance(input_value, list):
            for key in input_value:
                traversal_dict = TraversalDict()
                traversal_dict.traversal(self.template.get(range_key), key, is_list)
                result_dict[key] = traversal_dict.result
        else:
            traversal_dict = TraversalDict()
            traversal_dict.traversal(self.template.get(range_key), input_value, is_list)
            result_dict[input_value] = traversal_dict.result
