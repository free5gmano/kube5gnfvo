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

import copy
import yaml

from kubernetes import client, config
from GnbManagement.models import GnbInstance


class GnbDeployer:
    def __init__(self, gnb_name, namespace, yaml_content, node_name=None):
        self.gnb_name = gnb_name
        self.namespace = namespace
        self.yaml_content = yaml_content
        self.node_name = node_name.strip() if node_name else None
        
        try:
            config.load_incluster_config()
        except:
            config.load_kube_config()
        
        self.api_client = client.ApiClient()
        self.core_v1 = client.CoreV1Api()
        self.apps_v1 = client.AppsV1Api()

    def _build_runtime_prefix(self, gnb_instance):
        instance_id = str(getattr(gnb_instance, 'id', '') or '').strip().lower()
        short_id = instance_id.split('-')[0] if instance_id else ''
        if not short_id:
            raise ValueError('Failed to derive runtime id for gNB instance')
        # Kubernetes Service names must start with an alphabetic character.
        return f'gnb-{short_id}'

    def _render_runtime_docs(self, gnb_instance):
        runtime_prefix = self._build_runtime_prefix(gnb_instance)
        rendered_docs = []

        for document in yaml.safe_load_all(self.yaml_content):
            if document is None:
                continue

            manifest = copy.deepcopy(document)
            kind = manifest.get('kind')
            metadata = manifest.setdefault('metadata', {})
            original_name = metadata.get('name', '')

            if kind == 'ConfigMap':
                metadata['name'] = f'{runtime_prefix}-config'

            elif kind == 'Deployment':
                metadata['name'] = runtime_prefix
                labels = metadata.setdefault('labels', {})
                labels['app'] = runtime_prefix

                spec = manifest.setdefault('spec', {})
                selector = spec.setdefault('selector', {})
                match_labels = selector.setdefault('matchLabels', {})
                match_labels['app'] = runtime_prefix

                template = spec.setdefault('template', {})
                template_metadata = template.setdefault('metadata', {})
                template_labels = template_metadata.setdefault('labels', {})
                template_labels['app'] = runtime_prefix

                template_spec = template.setdefault('spec', {})
                if self.node_name:
                    template_spec['nodeName'] = self.node_name

                for volume in template_spec.get('volumes', []) or []:
                    config_map = volume.get('configMap')
                    if config_map and config_map.get('name') == 'ueransim-gnb-configmap':
                        config_map['name'] = f'{runtime_prefix}-config'

            elif kind == 'Service':
                spec = manifest.setdefault('spec', {})
                if spec.get('type') == 'NodePort':
                    # NodePort is optional for gNB templates; skip it entirely so
                    # incomplete or cluster-specific NodePort definitions do not
                    # block the main gNB deployment flow.
                    continue

                selector = spec.setdefault('selector', {})
                selector['app'] = runtime_prefix

                if original_name == 'ueransim-gnb-svc':
                    metadata['name'] = f'{runtime_prefix}-svc'
                elif original_name == 'ueransim-gnb-svc-nodeport':
                    metadata['name'] = f'{runtime_prefix}-nodeport'
                    for port in spec.get('ports', []) or []:
                        # Let Kubernetes auto-assign a unique nodePort so multiple gNB instances can coexist.
                        port.pop('nodePort', None)

            rendered_docs.append(manifest)

        rendered_yaml = yaml.dump_all(
            rendered_docs,
            default_flow_style=False,
            sort_keys=False,
            allow_unicode=True,
            explicit_start=True,
        )
        return rendered_docs, rendered_yaml
    
    def deploy(self):
        """部署 gNB 到 Kubernetes"""
        gnb_instance = GnbInstance.objects.create(
            gnbInstanceName=self.gnb_name,
            namespace=self.namespace,
            yamlContent=self.yaml_content,
            deploymentState='INSTANTIATING'
        )
        
        try:
            yaml_docs, rendered_yaml = self._render_runtime_docs(gnb_instance)
            gnb_instance.yamlContent = rendered_yaml
            gnb_instance.save(update_fields=['yamlContent', 'updatedAt'])
            
            for doc in yaml_docs:
                kind = doc.get('kind')
                
                if kind == 'ConfigMap':
                    self._deploy_configmap(doc)
                elif kind == 'Service':
                    self._deploy_service(doc)
                elif kind == 'Deployment':
                    self._deploy_deployment(doc)
            
            gnb_instance.deploymentState = 'INSTANTIATED'
            gnb_instance.save(update_fields=['deploymentState', 'updatedAt'])
            
            return gnb_instance
        
        except Exception as e:
            gnb_instance.deploymentState = 'FAILED'
            gnb_instance.save(update_fields=['deploymentState', 'updatedAt'])
            raise Exception(f"Failed to deploy gNB: {str(e)}")
    
    def migrate(self, target_node_name):
        """
        Migrate an already-deployed gNB to a different node by patching
        the existing K8s Deployment's nodeName.
        """
        if not target_node_name:
            raise ValueError('target_node_name is required')

        gnb_instance = GnbInstance.objects.filter(gnbInstanceName=self.gnb_name).last()
        if gnb_instance is None:
            raise Exception(f'GnbInstance "{self.gnb_name}" not found')

        runtime_prefix = self._build_runtime_prefix(gnb_instance)

        patch_body = {
            'spec': {
                'template': {
                    'spec': {
                        'nodeName': target_node_name,
                    }
                }
            }
        }
        try:
            self.apps_v1.patch_namespaced_deployment(
                name=runtime_prefix,
                namespace=self.namespace,
                body=patch_body,
            )
        except client.exceptions.ApiException as e:
            raise Exception(f'Failed to patch gNB deployment {runtime_prefix}: {e.reason}')

        # Update stored yamlContent so future redeploys remember the new node
        try:
            updated_docs = []
            for document in yaml.safe_load_all(gnb_instance.yamlContent):
                if document is None:
                    continue
                if document.get('kind') == 'Deployment':
                    template_spec = (
                        document.setdefault('spec', {})
                        .setdefault('template', {})
                        .setdefault('spec', {})
                    )
                    template_spec['nodeName'] = target_node_name
                updated_docs.append(document)
            gnb_instance.yamlContent = yaml.dump_all(
                updated_docs,
                default_flow_style=False,
                sort_keys=False,
                allow_unicode=True,
                explicit_start=True,
            )
            gnb_instance.save(update_fields=['yamlContent', 'updatedAt'])
        except Exception:
            pass

        return {
            'gnb_instance_id': str(gnb_instance.id),
            'gnb_instance_name': gnb_instance.gnbInstanceName,
            'deployment_name': runtime_prefix,
            'target_node_name': target_node_name,
        }

    def scale_resources(self, num_virtual_cpu=None, virtual_mem_size=None):
        """
        Adjust CPU / memory resources of a deployed gNB by patching
        the existing K8s Deployment's container resource limits/requests.
        """
        if not num_virtual_cpu and not virtual_mem_size:
            raise ValueError('At least one of num_virtual_cpu or virtual_mem_size is required')

        gnb_instance = GnbInstance.objects.filter(gnbInstanceName=self.gnb_name).last()
        if gnb_instance is None:
            raise Exception(f'GnbInstance "{self.gnb_name}" not found')

        runtime_prefix = self._build_runtime_prefix(gnb_instance)

        # Read current deployment to get container names
        deployment = self.apps_v1.read_namespaced_deployment(
            name=runtime_prefix,
            namespace=self.namespace,
        )

        resource_patch = {}
        if num_virtual_cpu:
            resource_patch['cpu'] = num_virtual_cpu
        if virtual_mem_size:
            resource_patch['memory'] = virtual_mem_size

        containers_patch = [
            {
                'name': c.name,
                'resources': {
                    'requests': resource_patch,
                    'limits': resource_patch,
                },
            }
            for c in deployment.spec.template.spec.containers
        ]

        patch_body = {
            'spec': {
                'template': {
                    'spec': {
                        'containers': containers_patch,
                    }
                }
            }
        }

        try:
            self.apps_v1.patch_namespaced_deployment(
                name=runtime_prefix,
                namespace=self.namespace,
                body=patch_body,
            )
        except client.exceptions.ApiException as e:
            raise Exception(f'Failed to patch gNB deployment {runtime_prefix}: {e.reason}')

        return {
            'gnb_instance_id': str(gnb_instance.id),
            'gnb_instance_name': gnb_instance.gnbInstanceName,
            'deployment_name': runtime_prefix,
            'resources': resource_patch,
        }

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
        if self.node_name:
            template_spec = manifest.setdefault('spec', {}).setdefault('template', {}).setdefault('spec', {})
            template_spec['nodeName'] = self.node_name
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
