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
from MecAppManagement.models import MecAppInstance


class MecAppDeployer:
    def __init__(self, mec_app_name, namespace, yaml_content):
        self.mec_app_name = mec_app_name
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
        """部署 MEC App 到 Kubernetes"""
        mec_app_instance = MecAppInstance.objects.create(
            mecAppInstanceName=self.mec_app_name,
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
                elif kind == 'StatefulSet':
                    self._deploy_statefulset(doc)
                elif kind == 'PersistentVolumeClaim':
                    self._deploy_pvc(doc)
                elif kind == 'Ingress':
                    self._deploy_ingress(doc)
            
            mec_app_instance.deploymentState = 'INSTANTIATED'
            mec_app_instance.save()
            
            return mec_app_instance
        
        except Exception as e:
            mec_app_instance.deploymentState = 'FAILED'
            mec_app_instance.save()
            raise Exception(f"Failed to deploy MEC App: {str(e)}")
    
    def undeploy(self):
        """從 Kubernetes 刪除 MEC App"""
        try:
            yaml_docs = yaml.safe_load_all(self.yaml_content)
            
            for doc in yaml_docs:
                if doc is None:
                    continue
                
                kind = doc.get('kind')
                name = doc.get('metadata', {}).get('name')
                
                try:
                    if kind == 'Deployment':
                        self.apps_v1.delete_namespaced_deployment(
                            name=name,
                            namespace=self.namespace
                        )
                    elif kind == 'StatefulSet':
                        self.apps_v1.delete_namespaced_stateful_set(
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
                    elif kind == 'PersistentVolumeClaim':
                        self.core_v1.delete_namespaced_persistent_volume_claim(
                            name=name,
                            namespace=self.namespace
                        )
                    elif kind == 'Ingress':
                        networking_v1 = client.NetworkingV1Api()
                        networking_v1.delete_namespaced_ingress(
                            name=name,
                            namespace=self.namespace
                        )
                except client.exceptions.ApiException as e:
                    if e.status != 404:
                        raise
        
        except Exception as e:
            raise Exception(f"Failed to undeploy MEC App: {str(e)}")
    
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
    
    def _deploy_statefulset(self, manifest):
        """部署 StatefulSet"""
        try:
            self.apps_v1.create_namespaced_stateful_set(
                namespace=self.namespace,
                body=manifest
            )
        except client.exceptions.ApiException as e:
            if e.status == 409:
                self.apps_v1.patch_namespaced_stateful_set(
                    name=manifest['metadata']['name'],
                    namespace=self.namespace,
                    body=manifest
                )
            else:
                raise
    
    def _deploy_pvc(self, manifest):
        """部署 PersistentVolumeClaim"""
        try:
            self.core_v1.create_namespaced_persistent_volume_claim(
                namespace=self.namespace,
                body=manifest
            )
        except client.exceptions.ApiException as e:
            if e.status == 409:
                # PVC 通常不能直接 patch，需要刪除重建
                pass
            else:
                raise
    
    def _deploy_ingress(self, manifest):
        """部署 Ingress"""
        try:
            networking_v1 = client.NetworkingV1Api()
            networking_v1.create_namespaced_ingress(
                namespace=self.namespace,
                body=manifest
            )
        except client.exceptions.ApiException as e:
            if e.status == 409:
                networking_v1 = client.NetworkingV1Api()
                networking_v1.patch_namespaced_ingress(
                    name=manifest['metadata']['name'],
                    namespace=self.namespace,
                    body=manifest
                )
            else:
                raise
