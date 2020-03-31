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

import queue
import threading
from functools import partial
from VIMManagement.utils.base_kubernetes import BaseKubernetes
from utils.etcd_client.etcd_client import EtcdClient


class MonitorDeployment(BaseKubernetes):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.run_watch_event()
        self.etcd_client = EtcdClient()

    def run_watch_event(self):
        threading.Thread(
            target=partial(self._get_deployment_event),
            daemon=True
        ).start()

        threading.Thread(
            target=partial(self._get_pod_event),
            daemon=True
        ).start()

    def _get_pod_event(self):
        resource_version = None
        while True:
            if resource_version is None:
                stream = self.watch.stream(partial(self.core_v1.list_pod_for_all_namespaces), timeout_seconds=5)
            else:
                stream = self.watch.stream(partial(self.core_v1.list_pod_for_all_namespaces),
                                           resource_version=resource_version, timeout_seconds=5)

            for event in stream:
                _type = event['type']
                _metadata = event['object']['metadata']
                _status = event['object']['status']
                if 'name' not in _metadata:
                    continue

                _name = _metadata['name']
                resource_version = _metadata['resourceVersion']

                _phase = _status['phase']
                if _type == 'MODIFIED' and 'deletionTimestamp' not in _metadata:
                    if 'containerStatuses' in _status:
                        container_status = _status['containerStatuses']
                        for status in container_status:
                            if 'state' not in status:
                                continue

                            state = status['state']
                            if 'waiting' in state and \
                                    'CrashLoopBackOff' == state['waiting']['reason']:
                                # alarm
                                self.pod_crash_event(_name)
                            else:
                                self.pod_status[_name] = status['state']

                elif _type == 'DELETED' and 'deletionTimestamp' in _metadata:
                    self.pod_crash_event(_name)
                else:
                    if 'containerStatuses' in _status:
                        container_status = _status['containerStatuses']
                        for status in container_status:
                            if 'state' not in status:
                                continue
                            self.pod_status[_name] = status['state']

    def pod_crash_event(self, pod_name):
        if pod_name in list(self.pod_status):
            self.pod_status.pop(pod_name)
            self.etcd_client.set_deploy_name(instance_name=None, pod_name=pod_name)
            self.etcd_client.release_pod_ip_address()

    def _get_deployment_event(self):
        resource_version = None
        while True:
            if resource_version is None:
                stream = self.watch.stream(partial(self.app_v1.list_deployment_for_all_namespaces), timeout_seconds=5)
            else:
                stream = self.watch.stream(partial(self.app_v1.list_deployment_for_all_namespaces),
                                           resource_version=resource_version, timeout_seconds=5)

            for event in stream:
                _type = event['type']
                if 'name' not in event['object']['metadata']:
                    continue
                _name = event['object']['metadata']['name']
                resource_version = event['object']['metadata']['resourceVersion']
                replicas = event['object']['spec']['replicas']
                if _type == 'DELETED' and _name in list(self.deployment_status):
                    self.deployment_status.pop(_name)
                else:
                    if _name not in list(self.deployment_status):
                        self.deployment_status[_name] = {'replicas': replicas}

    def watch_specific_deployment(self, container_instance_name, _status, events):
        _queue = queue.Queue()
        threading.Thread(
            target=partial(self._get_deploy_status, _queue=_queue, events=events),
            daemon=True
        ).start()

        threading.Thread(
            target=lambda q, deploy_names, status: q.put(
                self._check_specific_deployment_status(
                    input_deployment_set=deploy_names, status=status)),
            args=(_queue, container_instance_name, _status),
            daemon=True
        ).start()

    def _check_specific_deployment_status(self, input_deployment_set, status):
        loop_count = -1
        while len(input_deployment_set) != 0:
            if loop_count < 0:
                loop_count = len(input_deployment_set) - 1

            all_deployment_key = list(self.deployment_status)
            input_specific_deployment = list(input_deployment_set)[loop_count]
            if status == 'Terminating':
                if input_specific_deployment not in all_deployment_key:
                    input_deployment_set.remove(input_specific_deployment)
            else:
                if input_specific_deployment in all_deployment_key:
                    pod_status_count = 0
                    for pod_name in list(self.pod_status):
                        if input_specific_deployment in pod_name:
                            if status == self.pod_status[pod_name]:
                                pod_status_count += 1
                    if self.deployment_status[input_specific_deployment]['replicas'] == pod_status_count:
                        input_deployment_set.remove(input_specific_deployment)

            loop_count = loop_count - 1
        return True

    def _get_deploy_status(self, _queue, events):
        while _queue.empty():
            pass
        print('success')
        [event() for event in events]
