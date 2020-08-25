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
from NSFaultManagement.utils.alarm_event import AlarmEvent
from VIMManagement.utils.base_kubernetes import BaseKubernetes
from utils.etcd_client.etcd_client import EtcdClient

is_running = False


class MonitorDeployment(BaseKubernetes):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.etcd_client = EtcdClient()
        self.alarm = AlarmEvent()
        global is_running
        if not is_running:
            threading.Thread(
                target=self._get_replica_event,
                args=(self.app_v1.list_deployment_for_all_namespaces, self.deployment_status),
                daemon=True
            ).start()
            threading.Thread(
                target=partial(self._get_pod_event),
                daemon=True
            ).start()
            threading.Thread(
                target=self._get_replica_event,
                args=(self.kubevirt_api.list_virtual_machine_instance_replica_set_for_all_namespaces,
                      self.virtual_machine_replica_set),
                daemon=True
            ).start()
            threading.Thread(
                target=partial(self._get_virtual_machine_event),
                daemon=True
            ).start()
        is_running = True

    def _get_replica_event(self, events, record: dict):
        while True:
            stream = self.watch.stream(partial(events), timeout_seconds=5)
            for event in stream:
                _type = event['type']
                if 'name' not in event['object']['metadata']:
                    continue

                _name = event['object']['metadata']['name']
                replicas = event['object']['spec']['replicas']
                if _name not in list(record):
                    record[_name] = {'replicas': replicas}

    def _get_virtual_machine_event(self):
        while True:
            for vmi in self.kubevirt_api.list_virtual_machine_instance_for_all_namespaces().items:
                metadata = vmi.metadata
                name = metadata.name
                deletion_timestamp = metadata.deletion_timestamp
                status = vmi.status
                phase = status.phase

                if status.conditions:
                    if 'Failed' == phase:
                        if not deletion_timestamp:
                            error_reason = None
                            error_message = None
                            type_record = list()
                            for conditions in status.conditions:
                                type_record.append(conditions.type)
                                if conditions.type != 'LiveMigratable' and conditions.type != 'Ready':
                                    error_reason = conditions.reason
                                    error_message = conditions.message
                            if 'Ready' not in type_record:
                                self.alarm.create_alarm(name, error_reason, error_message, False)
                                if name in list(self.virtual_machine_status):
                                    self.virtual_machine_status.pop(name)
                        elif name in list(self.virtual_machine_status):
                            self.virtual_machine_status.pop(name)
                    elif phase == 'Running' and name:
                        self.virtual_machine_status[name] = phase

    def _get_pod_event(self):
        while True:
            stream = self.watch.stream(partial(self.core_v1.list_pod_for_all_namespaces), timeout_seconds=5)

            for event in stream:
                _type = event['type']
                _metadata = event['object']['metadata']
                _status = event['object']['status']
                if 'name' not in _metadata:
                    continue

                _name = _metadata['name']
                _phase = _status['phase']
                if _phase == 'Running':
                    self.pod_status[_name] = _phase

                if _type == 'MODIFIED' and 'deletionTimestamp' not in _metadata:
                    if 'containerStatuses' in _status:
                        container_status = _status['containerStatuses']
                        for status in container_status:
                            if 'state' not in status:
                                continue

                            state = status['state']
                            if 'waiting' in state and \
                                    'CrashLoopBackOff' == state['waiting']['reason']:
                                self.alarm.create_alarm(
                                    _name, state['waiting']['reason'], state['waiting']['message'])
                                if _name in list(self.pod_status):
                                    self.pod_crash_event(None, _name)

                elif _type == 'DELETED' and _name in list(self.pod_status) and 'deletionTimestamp' in _metadata:
                    self.pod_crash_event(_name, None)
                    self.pod_status.pop(_name)

    def pod_crash_event(self, instance_name, pod_name):
        self.etcd_client.set_deploy_name(instance_name=instance_name, pod_name=pod_name)
        self.etcd_client.release_pod_ip_address()

    def watch_specific_deployment(self, container_instance_name, vm_instance_name, _status, events):
        _queue = queue.Queue()
        # check two event
        success_count = 2
        threading.Thread(
            target=partial(self._get_deploy_status, _queue=_queue, events=events, success_count=success_count),
            daemon=True
        ).start()

        threading.Thread(
            target=lambda q, deployment_names, status: q.put(
                self._check_status(input_set=deployment_names, status=status, isContainer=True)),
            args=(_queue, container_instance_name, _status),
            daemon=True
        ).start()

        threading.Thread(
            target=lambda q, vm_names, status: q.put(
                self._check_status(input_set=vm_names, status=status, isContainer=False)),
            args=(_queue, vm_instance_name, _status),
            daemon=True
        ).start()

    def _check_status(self, input_set, status, isContainer):
        loop_count = -1
        while len(input_set) != 0:
            if isContainer:
                all_resource = self.deployment_status
                server_set = self.pod_status
            else:
                all_resource = self.virtual_machine_replica_set
                server_set = self.virtual_machine_status

            if loop_count < 0:
                loop_count = len(input_set) - 1

            specific_input_resource = list(input_set)[loop_count]
            if specific_input_resource in list(all_resource):
                if status == 'Terminating':
                    if not any(specific_input_resource in _ for _ in list(server_set)):
                        input_set.remove(specific_input_resource)
                        all_resource.pop(specific_input_resource)
                else:
                    complete_count = 0
                    for name in list(server_set):
                        if specific_input_resource in name:
                            if status == server_set[name]:
                                complete_count += 1
                    if all_resource[specific_input_resource]['replicas'] == complete_count:
                        input_set.remove(specific_input_resource)

            loop_count -= 1
        return True

    def _get_deploy_status(self, _queue, events, success_count):
        while success_count:
            success_status = _queue.get()
            if success_status:
                success_count -= 1
        print('success')
        [event() for event in events]
