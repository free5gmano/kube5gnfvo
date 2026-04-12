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
from datetime import datetime
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
            # 只有在 kubevirt_api 可用時才啟動相關線程
            if self.kubevirt_api is not None:
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
        if self.kubevirt_api is None:
            return
        while True:
            try:
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
            except Exception:
                # 如果 kubevirt 不可用或出現錯誤，靜默處理
                pass

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
                _namespace = _metadata.get('namespace', 'default')
                _phase = _status.get('phase')
                if _phase == 'Running':
                    self.pod_status[_name] = _phase

                if _type in ('MODIFIED', 'ADDED') and 'deletionTimestamp' not in _metadata:

                    # Case A: Pending + Unschedulable → 排程失敗
                    if _phase == 'Pending':
                        conditions = _status.get('conditions') or []
                        for cond in conditions:
                            if (cond.get('type') == 'PodScheduled'
                                    and cond.get('status') == 'False'
                                    and cond.get('reason') == 'Unschedulable'):
                                # event-driven 收到，事件原因附在 condition.message
                                self.alarm.create_alarm(
                                    _name,
                                    'Unschedulable',
                                    cond.get('message') or 'Pod cannot be scheduled',
                                    True,
                                )
                                break

                    # Case B: Container 終止/重啟相關 → 抓真正的終止原因
                    # 三個觸發條件：
                    #   1. 當前 state.terminated.reason = 'OOMKilled' (剛被 OOMKill)
                    #   2. lastState.terminated.reason 有值 + restartCount >= 2 (重啟至少 2 次)
                    #   3. waiting.reason = 'CrashLoopBackOff' (backoff 階段)
                    container_statuses = _status.get('containerStatuses') or []
                    for status in container_statuses:
                        state = status.get('state')
                        if not isinstance(state, dict):
                            continue

                        restart_count = status.get('restartCount', 0)
                        waiting = state.get('waiting') or {}
                        terminated_now = state.get('terminated') or {}
                        last_state = status.get('lastState') or {}
                        terminated_last = last_state.get('terminated') or {}

                        trigger_reason = None
                        trigger_message = ''
                        trigger_exit_code = None

                        # 條件 1: 當前就是 terminated (通常很短暫，但如果抓到就是即時)
                        if terminated_now.get('reason'):
                            trigger_reason = terminated_now.get('reason')
                            trigger_message = terminated_now.get('message') or ''
                            trigger_exit_code = terminated_now.get('exitCode')

                        # 條件 2: lastState 有 OOMKilled 且 restart >= 1 (已經重啟過，lastState 穩定)
                        elif terminated_last.get('reason') == 'OOMKilled' and restart_count >= 1:
                            trigger_reason = 'OOMKilled'
                            trigger_message = terminated_last.get('message') or ''
                            trigger_exit_code = terminated_last.get('exitCode')

                        # 條件 3: 進入 CrashLoopBackOff (連續失敗，使用 lastState 判斷)
                        elif waiting.get('reason') == 'CrashLoopBackOff':
                            trigger_reason = terminated_last.get('reason') or 'Unknown'
                            trigger_message = (
                                terminated_last.get('message')
                                or waiting.get('message')
                                or ''
                            )
                            trigger_exit_code = terminated_last.get('exitCode')

                        if not trigger_reason:
                            continue

                        detail = (
                            f"{trigger_message} (exitCode={trigger_exit_code}, restartCount={restart_count})"
                            if trigger_exit_code is not None
                            else f"{trigger_message} (restartCount={restart_count})"
                        )
                        self.alarm.create_alarm(_name, trigger_reason, detail, True)
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
