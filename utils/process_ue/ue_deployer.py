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
import time
import yaml

from kubernetes import client, config

from GnbManagement.models import UeInstance


READY_TIMEOUT_SECONDS = 120
POLL_INTERVAL_SECONDS = 3
FAILED_WAITING_REASONS = {
    'CrashLoopBackOff',
    'CreateContainerConfigError',
    'CreateContainerError',
    'ErrImagePull',
    'ImageInspectError',
    'ImagePullBackOff',
    'InvalidImageName',
    'RunContainerError',
    'Unschedulable',
}
FAILED_TERMINATED_REASONS = {
    'ContainerCannotRun',
    'DeadlineExceeded',
    'Error',
    'OOMKilled',
}


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

    def _get_default_ue_config(self):
        return {
            'supi': 'imsi-208930000000001',
            'mcc': '208',
            'mnc': '93',
            'protectionScheme': 0,
            'homeNetworkPublicKey': '5a8d38864820197c3394b92613b20b91633cbd897119273bf8e4a6f4eec0a650',
            'homeNetworkPublicKeyId': 1,
            'routingIndicator': '0000',
            'key': '8baf473f2f8fd09487cccbd7097c6862',
            'op': '8e27b6af0e692e750f32667a3b14605d',
            'opType': 'OPC',
            'amf': '8000',
            'imei': '356938035643803',
            'imeiSv': '4370816125816151',
            'tunNetmask': '255.255.255.0',
            'gnbSearchList': ['127.0.0.1'],
            'uacAic': {
                'mps': False,
                'mcs': False,
            },
            'uacAcc': {
                'normalClass': 0,
                'class11': False,
                'class12': False,
                'class13': False,
                'class14': False,
                'class15': False,
            },
            'sessions': [
                {
                    'type': 'IPv4',
                    'apn': 'internet',
                    'slice': {
                        'sst': 0x01,
                        'sd': 0x010203,
                    },
                },
            ],
            'configured-nssai': [
                {
                    'sst': 0x01,
                    'sd': 0x010203,
                },
            ],
            'default-nssai': [
                {
                    'sst': 1,
                    'sd': 1,
                },
            ],
            'integrity': {
                'IA1': True,
                'IA2': True,
                'IA3': True,
            },
            'ciphering': {
                'EA1': True,
                'EA2': True,
                'EA3': True,
            },
            'integrityMaxRate': {
                'uplink': 'full',
                'downlink': 'full',
            },
        }

    def _build_intent_docs(self, ue_intent, runtime_prefix):
        ue_config = self._get_default_ue_config()
        ue_config.update(ue_intent or {})
        ue_config.pop('replicas', None)

        if self.gnb_service_name:
            ue_config['gnbSearchList'] = [self.gnb_service_name]

        replicas = int((ue_intent or {}).get('replicas') or 1)
        config_map_name = f'{runtime_prefix}-config'

        return [
            {
                'apiVersion': 'v1',
                'kind': 'ConfigMap',
                'metadata': {
                    'name': config_map_name,
                },
                'data': {
                    'free5gc-ue.yaml': yaml.safe_dump(
                        ue_config,
                        default_flow_style=False,
                        sort_keys=False,
                        allow_unicode=True,
                    ),
                },
            },
            {
                'apiVersion': 'apps/v1',
                'kind': 'Deployment',
                'metadata': {
                    'name': runtime_prefix,
                    'labels': {
                        'app': runtime_prefix,
                    },
                },
                'spec': {
                    'replicas': replicas,
                    'selector': {
                        'matchLabels': {
                            'app': runtime_prefix,
                        },
                    },
                    'template': {
                        'metadata': {
                            'labels': {
                                'app': runtime_prefix,
                            },
                        },
                        'spec': {
                            'containers': [
                                {
                                    'name': runtime_prefix,
                                    'image': 'free5gmano/ueransim:v3.2.7',
                                    'imagePullPolicy': 'IfNotPresent',
                                    'securityContext': {
                                        'privileged': True,
                                    },
                                    'command': ['/bin/sh'],
                                    'args': [
                                        '-c',
                                        (
                                            'cp /UERANSIM/config/free5gc-ue.yaml /tmp/ue.yaml\n'
                                            'echo "=== UE config ==="\n'
                                            'cat /tmp/ue.yaml\n'
                                            './build/nr-ue -c /tmp/ue.yaml\n'
                                        ),
                                    ],
                                    'volumeMounts': [
                                        {
                                            'name': 'ueransim-ue-conf',
                                            'mountPath': '/UERANSIM/config/free5gc-ue.yaml',
                                            'subPath': 'free5gc-ue.yaml',
                                        },
                                        {
                                            'name': 'dev-net-tun',
                                            'mountPath': '/dev/net/tun',
                                        },
                                    ],
                                },
                            ],
                            'volumes': [
                                {
                                    'name': 'ueransim-ue-conf',
                                    'configMap': {
                                        'name': config_map_name,
                                        'items': [
                                            {
                                                'key': 'free5gc-ue.yaml',
                                                'path': 'free5gc-ue.yaml',
                                            },
                                        ],
                                    },
                                },
                                {
                                    'name': 'dev-net-tun',
                                    'hostPath': {
                                        'path': '/dev/net/tun',
                                    },
                                },
                            ],
                        },
                    },
                },
            },
        ]

    def _list_runtime_pods(self, runtime_prefix):
        response = self.core_v1.list_namespaced_pod(
            namespace=self.namespace,
            label_selector=f'app={runtime_prefix}',
        )
        return response.items or []

    def _get_pod_failure_reason(self, pods):
        for pod in pods:
            pod_name = getattr(getattr(pod, 'metadata', None), 'name', 'unknown-pod')
            pod_status = getattr(pod, 'status', None)
            pod_phase = getattr(pod_status, 'phase', '')

            if pod_phase == 'Failed':
                return f'Pod {pod_name} entered Failed phase'

            for condition in getattr(pod_status, 'conditions', None) or []:
                if (
                    getattr(condition, 'type', '') == 'PodScheduled'
                    and getattr(condition, 'status', '') == 'False'
                    and getattr(condition, 'reason', '') == 'Unschedulable'
                ):
                    return getattr(condition, 'message', '') or f'Pod {pod_name} is unschedulable'

            container_statuses = list(getattr(pod_status, 'init_container_statuses', None) or [])
            container_statuses += list(getattr(pod_status, 'container_statuses', None) or [])

            for container_status in container_statuses:
                container_name = getattr(container_status, 'name', pod_name)
                state = getattr(container_status, 'state', None)
                last_state = getattr(container_status, 'last_state', None)
                waiting = getattr(state, 'waiting', None)
                terminated = getattr(state, 'terminated', None)
                last_terminated = getattr(last_state, 'terminated', None)

                if waiting and getattr(waiting, 'reason', '') in FAILED_WAITING_REASONS:
                    message = getattr(waiting, 'message', '') or getattr(waiting, 'reason', '')
                    return f'Container {container_name} is waiting: {message}'

                if terminated and getattr(terminated, 'reason', '') in FAILED_TERMINATED_REASONS:
                    message = getattr(terminated, 'message', '') or getattr(terminated, 'reason', '')
                    return f'Container {container_name} terminated: {message}'

                if last_terminated and getattr(last_terminated, 'reason', '') in FAILED_TERMINATED_REASONS:
                    message = getattr(last_terminated, 'message', '') or getattr(last_terminated, 'reason', '')
                    return f'Container {container_name} crashed previously: {message}'

        return None

    def refresh_runtime_state(self, ue_instance):
        runtime_prefix = self._build_runtime_prefix(ue_instance)
        next_state = 'NOT_INSTANTIATED'
        failure_reason = None

        try:
            deployment = self.apps_v1.read_namespaced_deployment_status(
                name=runtime_prefix,
                namespace=self.namespace,
            )
        except client.exceptions.ApiException as exc:
            if exc.status != 404:
                raise
        else:
            next_state = 'INSTANTIATING'
            deployment_spec = getattr(deployment, 'spec', None)
            deployment_status = getattr(deployment, 'status', None)
            desired_replicas = getattr(deployment_spec, 'replicas', 0) or 0
            ready_replicas = getattr(deployment_status, 'ready_replicas', 0) or 0
            available_replicas = getattr(deployment_status, 'available_replicas', 0) or 0
            updated_replicas = getattr(deployment_status, 'updated_replicas', 0) or 0

            for condition in getattr(deployment_status, 'conditions', None) or []:
                if (
                    getattr(condition, 'type', '') == 'Progressing'
                    and getattr(condition, 'status', '') == 'False'
                ):
                    failure_reason = getattr(condition, 'message', '') or getattr(condition, 'reason', '')
                    next_state = 'FAILED'
                    break

            if next_state != 'FAILED':
                pods = self._list_runtime_pods(runtime_prefix)
                failure_reason = self._get_pod_failure_reason(pods)
                if failure_reason:
                    next_state = 'FAILED'
                elif (
                    desired_replicas > 0
                    and ready_replicas >= desired_replicas
                    and available_replicas >= desired_replicas
                    and updated_replicas >= desired_replicas
                ):
                    next_state = 'INSTANTIATED'

        if ue_instance.deploymentState != next_state:
            ue_instance.deploymentState = next_state
            ue_instance.save(update_fields=['deploymentState', 'updatedAt'])

        return next_state, failure_reason

    def wait_until_runtime_ready(
        self,
        ue_instance,
        timeout_seconds=READY_TIMEOUT_SECONDS,
        poll_interval_seconds=POLL_INTERVAL_SECONDS,
    ):
        deadline = time.monotonic() + timeout_seconds

        while True:
            current_state, failure_reason = self.refresh_runtime_state(ue_instance)
            if current_state in {'INSTANTIATED', 'FAILED'}:
                return current_state, failure_reason
            if time.monotonic() >= deadline:
                return current_state, failure_reason
            time.sleep(poll_interval_seconds)

    def _normalize_yaml_content(self):
        if not isinstance(self.yaml_content, str):
            return self.yaml_content
        return self.yaml_content.replace('|\\n', '|\n')

    def _render_runtime_docs(self, ue_instance):
        runtime_prefix = self._build_runtime_prefix(ue_instance)
        rendered_docs = []
        config_map_name_mapping = {}
        yaml_content = self._normalize_yaml_content()
        source_docs = [document for document in yaml.safe_load_all(yaml_content) if document is not None]

        if (
            len(source_docs) == 1
            and isinstance(source_docs[0], dict)
            and source_docs[0].get('kind') is None
            and isinstance(source_docs[0].get('ue'), dict)
        ):
            rendered_docs = self._build_intent_docs(source_docs[0]['ue'], runtime_prefix)
            if self.node_name:
                rendered_docs[1]['spec']['template']['spec']['nodeName'] = self.node_name
            rendered_yaml = yaml.dump_all(
                rendered_docs,
                default_flow_style=False,
                sort_keys=False,
                allow_unicode=True,
                explicit_start=True,
            )
            return rendered_docs, rendered_yaml

        for document in source_docs:
            manifest = copy.deepcopy(document)
            kind = manifest.get('kind')
            metadata = manifest.setdefault('metadata', {})

            if kind == 'ConfigMap':
                original_name = metadata.get('name')
                rendered_config_name = f'{runtime_prefix}-config'
                metadata['name'] = rendered_config_name
                if original_name:
                    config_map_name_mapping[original_name] = rendered_config_name
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
                    config_map_name = config_map.get('name') if config_map else None
                    if config_map_name in config_map_name_mapping:
                        config_map['name'] = config_map_name_mapping[config_map_name]
                    elif config_map_name and 'ueransim-ue-configmap' in str(config_map_name):
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

            final_state, failure_reason = self.wait_until_runtime_ready(ue_instance)
            if final_state == 'FAILED':
                raise RuntimeError(failure_reason or 'UE pod failed before becoming ready')
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
