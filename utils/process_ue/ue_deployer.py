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

from GnbManagement.models import UeInstance


class UeDeployer:
    def __init__(self, ue_name, namespace, yaml_content, node_name=None, gnb_service_name=None):
        self.ue_name = ue_name
        self.namespace = namespace
        self.yaml_content = yaml_content
        self.node_name = node_name.strip() if node_name else None
        self.gnb_service_name = gnb_service_name.strip() if gnb_service_name else None

        try:
            config.load_incluster_config()
        except Exception:
            config.load_kube_config()

        self.core_v1 = client.CoreV1Api()
        self.apps_v1 = client.AppsV1Api()

    def _build_runtime_prefix(self, ue_instance):
        instance_id = str(getattr(ue_instance, 'id', '') or '').strip().lower()
        short_id = instance_id.split('-')[0] if instance_id else ''
        if not short_id:
            raise ValueError('Failed to derive runtime id for UE instance')
        return f'ue-{short_id}'

    def _render_runtime_docs(self, ue_instance):
        runtime_prefix = self._build_runtime_prefix(ue_instance)
        rendered_docs = []

        for document in yaml.safe_load_all(self.yaml_content):
            if document is None:
                continue

            manifest = copy.deepcopy(document)
            kind = manifest.get('kind')
            metadata = manifest.setdefault('metadata', {})

            if kind == 'ConfigMap':
                metadata['name'] = f'{runtime_prefix}-config'
                data = manifest.get('data') or {}
                for key, value in list(data.items()):
                    if not isinstance(value, str) or key != 'free5gc-ue.yaml':
                        continue
                    ue_config = yaml.safe_load(value) or {}
                    if self.gnb_service_name:
                        ue_config['gnbSearchList'] = [self.gnb_service_name]
                    data[key] = yaml.safe_dump(
                        ue_config,
                        default_flow_style=False,
                        sort_keys=False,
                        allow_unicode=True,
                    )

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
                    if config_map and config_map.get('name') == 'ueransim-ue-configmap':
                        config_map['name'] = f'{runtime_prefix}-config'

                for container in template_spec.get('containers', []) or []:
                    if container.get('name') == 'ueransim-ue':
                        container['name'] = runtime_prefix

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
        ue_instance = UeInstance.objects.create(
            ueInstanceName=self.ue_name,
            namespace=self.namespace,
            yamlContent=self.yaml_content,
            gnbServiceName=self.gnb_service_name,
            deploymentState='INSTANTIATING',
        )

        try:
            yaml_docs, rendered_yaml = self._render_runtime_docs(ue_instance)
            ue_instance.yamlContent = rendered_yaml
            ue_instance.save(update_fields=['yamlContent', 'updatedAt'])

            for doc in yaml_docs:
                kind = doc.get('kind')
                if kind == 'ConfigMap':
                    self._deploy_configmap(doc)
                elif kind == 'Deployment':
                    self._deploy_deployment(doc)

            ue_instance.deploymentState = 'INSTANTIATED'
            ue_instance.save(update_fields=['deploymentState', 'updatedAt'])
            return ue_instance
        except Exception as e:
            ue_instance.deploymentState = 'FAILED'
            ue_instance.save(update_fields=['deploymentState', 'updatedAt'])
            raise Exception(f"Failed to deploy UE: {str(e)}")

    def undeploy(self):
        try:
            for doc in yaml.safe_load_all(self.yaml_content):
                if doc is None:
                    continue

                kind = doc.get('kind')
                name = doc.get('metadata', {}).get('name')

                try:
                    if kind == 'Deployment':
                        self.apps_v1.delete_namespaced_deployment(
                            name=name,
                            namespace=self.namespace,
                        )
                    elif kind == 'ConfigMap':
                        self.core_v1.delete_namespaced_config_map(
                            name=name,
                            namespace=self.namespace,
                        )
                except client.exceptions.ApiException as e:
                    if e.status != 404:
                        raise
        except Exception as e:
            raise Exception(f"Failed to undeploy UE: {str(e)}")

    def _deploy_configmap(self, manifest):
        try:
            self.core_v1.create_namespaced_config_map(
                namespace=self.namespace,
                body=manifest,
            )
        except client.exceptions.ApiException as e:
            if e.status == 409:
                self.core_v1.patch_namespaced_config_map(
                    name=manifest['metadata']['name'],
                    namespace=self.namespace,
                    body=manifest,
                )
            else:
                raise

    def _deploy_deployment(self, manifest):
        if self.node_name:
            template_spec = manifest.setdefault('spec', {}).setdefault('template', {}).setdefault('spec', {})
            template_spec['nodeName'] = self.node_name
        try:
            self.apps_v1.create_namespaced_deployment(
                namespace=self.namespace,
                body=manifest,
            )
        except client.exceptions.ApiException as e:
            if e.status == 409:
                self.apps_v1.patch_namespaced_deployment(
                    name=manifest['metadata']['name'],
                    namespace=self.namespace,
                    body=manifest,
                )
            else:
                raise
