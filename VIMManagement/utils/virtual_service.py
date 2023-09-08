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
import json
import os
import uuid
from VIMManagement.utils.kubernetes_api import KubernetesApi
from utils.tosca_paser.cp_template import SR_IOV


class VirtualServiceClient(KubernetesApi):
    group = 'networking.istio.io' 
    version = 'v1alpha3'
    plural = 'virtualservices'
    kind = 'VirtualService'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.name_of_service = kwargs['name_of_service']
        self.specific_info = kwargs['specific_info']
        # self.attempts = kwargs['attempts']
        # self.perTryTimeout = "{}s".format(kwargs['perTryTimeout'])
        # self.retryOn = kwargs['retryOn']
        self.apply_cluster = kwargs['apply_cluster'] if 'apply_cluster' in kwargs else None
        if self.apply_cluster:
            self.api_crd = self.kubernetes_client.CustomObjectsApi(api_client=self.config.new_client_from_config(context=self.apply_cluster))
            
    def read_resource(self, **kwargs):
        return self.api_crd.list_namespaced_custom_object(self.group, self.version, self.plural, self.namespace)

    def create_resource(self, **kwargs):
        self.api_crd.create_namespaced_custom_object(group=self.group, version=self.version,  plural=self.plural, 
                                                     namespace=self.namespace, body=self.resource)

    def patch_resource(self, **kwargs):
        pass

    def delete_resource(self, **kwargs):
        self.api_crd.delete_namespaced_custom_object(self.group, self.version, self.plural, self.namespace, 
                                                     self.name_of_service, body=self.delete_options)
    def parser_spec_resource(self, **kwargs):
        spec_info = {"hosts": [self.name_of_service if self.name_of_service else self.instance_name]}
        if "canary" in self.specific_info:
            destination = list()
            specific = self.specific_info['canary']
            # for i in range(len(specific['hostname'])):
            for host, subset, weight in zip(specific['hostname'], specific['subset'], specific['weight']):
                destination_value = {
                    "destination": {
                        "host": host, 
                        "subset": subset,
                    },
                    "weight": weight
                }
                destination.append(destination_value)
            
            spec_info["http"] = [{"route": destination}]
        if "retry_policy" in self.specific_info:
            specific = self.specific_info['retry_policy']
            spec_info["http"] = [{
                "route": [{
                    "destination": {
                        "host": self.name_of_service if self.name_of_service else self.instance_name
                    }
                }],
                "retries": {
                    "attempts": specific['attempts'] ,
                    "perTryTimeout": "{}s".format(specific['perTryTimeout']),
                    "retryOn": specific['retryOn']
                }
            }]
        return spec_info

    def instance_specific_resource(self, **kwargs):
        spec_info = self.parser_spec_resource()
        service_id = uuid.uuid4()
        virtual_service = {
            "apiVersion": "{}/{}".format(self.group, self.version),
            "kind": self.kind,
            "metadata": {
                "name": self.name_of_service + str(service_id)
            },
            "spec": spec_info
        }

        return virtual_service
   