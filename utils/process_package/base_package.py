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

from utils.file_manipulation import read_yaml_file
from utils.tosca_paser.tosca_template import ToscaTemplate

on_boarding_state = (created, uploading, processing, on_boarded) = \
    ('CREATED', 'UPLOADING', 'PROCESSING', 'ONBOARDED')

operational_state = (enabled, disabled) = ('ENABLED', 'DISABLED')

usage_state = (in_use, not_in_use) = ('IN_USE', 'NOT_IN_USE')

instantiated_state = (instantiated, not_instantiated) = ('INSTANTIATED', 'NOT_INSTANTIATED')


class BasePackage(object):
    def __init__(self, path):
        self.root_path = path
        self.tosca_metadata = read_yaml_file('{}TOSCA-Metadata/TOSCA.meta'.format(self.root_path))
        self.entry_definitions = self.tosca_metadata['Entry-Definitions']
        self.entry_manifest = read_yaml_file(self.root_path + self.tosca_metadata['ETSI-Entry-Manifest'])
        self.tosca_template = ToscaTemplate(read_yaml_file(self.root_path + self.entry_definitions))
        self.topology_template = self.tosca_template.topology_template
