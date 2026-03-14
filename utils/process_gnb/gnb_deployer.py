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

import yaml
from kubernetes import client, config
from GnbManagement.models import GnbInstance


class GnbDeployer:
    def __init__(self, gnb_name, namespace, yaml_content):
        self.gnb_name = gnb_name
        self.namespace = namespace
        self.yaml_content = yaml_content
        
        try:
            config.load_incluster_config()
        except:
            config.load_kube_config()
        
        self.api_client = client.ApiClient()
        self.core_v1 = client.CoreV1Api()
        self.apps_v1 = client.AppsV1Api()
    
    def deploy(self):
        """部署 gNB 到 Kubernetes"""
        gnb_instance = GnbInstance.objects.create(
            gnbInstanceName=self.gnb_name,
            namespace=self.namespace,
            yamlContent=self.yaml_content,
            deploymentState='INSTANTIATING'
        )
        
        try:
            yaml_docs = yaml.safe_load_all(self.yaml_content)
            
            for doc in yaml_docs:
                if doc is None:
                    continue
                
                kind = doc.get('kind')
                
                if kind == 'ConfigMap':
                    self._deploy_configmap(doc)
                elif kind == 'Service':
                    self._deploy_service(doc)
                elif kind == 'Deployment':
                    self._deploy_deployment(doc)
            
            gnb_instance.deploymentState = 'INSTANTIATED'
            gnb_instance.save()
            
            return gnb_instance
        
        except Exception as e:
            gnb_instance.deploymentState = 'FAILED'
            gnb_instance.save()
            raise Exception(f"Failed to deploy gNB: {str(e)}")
    
    def undeploy(self):
        """從 Kubernetes 刪除 gNB"""
        try:
            yaml_docs = yaml.safe_load_all(self.yaml_content)
            
            for doc in yaml_docs:
                if doc is None:
                    continue
                
                kind = doc.get('kind')
                name = doc.get('metadata', {}).get('name')
                
                if kind == 'Deployment':
                    self.apps_v1.delete_namespaced_deployment(
                        name=name,
                        namespace=self.namespace
                    )
                elif kind == 'Service':
                    self.core_v1.delete_namespaced_service(
                        name=name,
                        namespace=self.namespace
                    )
                elif kind == 'ConfigMap':
                    self.core_v1.delete_namespaced_config_map(
                        name=name,
                        namespace=self.namespace
                    )
        
        except Exception as e:
            raise Exception(f"Failed to undeploy gNB: {str(e)}")
    
    def _deploy_configmap(self, manifest):
        """部署 ConfigMap"""
        try:
            self.core_v1.create_namespaced_config_map(
                namespace=self.namespace,
                body=manifest
            )
        except client.exceptions.ApiException as e:
            if e.status == 409:
                self.core_v1.patch_namespaced_config_map(
                    name=manifest['metadata']['name'],
                    namespace=self.namespace,
                    body=manifest
                )
            else:
                raise
    
    def _deploy_service(self, manifest):
        """部署 Service"""
        try:
            self.core_v1.create_namespaced_service(
                namespace=self.namespace,
                body=manifest
            )
        except client.exceptions.ApiException as e:
            if e.status == 409:
                self.core_v1.patch_namespaced_service(
                    name=manifest['metadata']['name'],
                    namespace=self.namespace,
                    body=manifest
                )
            else:
                raise
    
    def _deploy_deployment(self, manifest):
        """部署 Deployment"""
        try:
            self.apps_v1.create_namespaced_deployment(
                namespace=self.namespace,
                body=manifest
            )
        except client.exceptions.ApiException as e:
            if e.status == 409:
                self.apps_v1.patch_namespaced_deployment(
                    name=manifest['metadata']['name'],
                    namespace=self.namespace,
                    body=manifest
                )
            else:
                raise
