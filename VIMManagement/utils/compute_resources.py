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

import os
import queue
import threading
import time
from collections import defaultdict
from functools import partial
from pint import UnitRegistry
from VIMManagement.utils.base_kubernetes import BaseKubernetes, ResourceResult
from utils.base_request import BaseRequest


class ComputeResource(BaseKubernetes):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.unit_registry = UnitRegistry()
        self.unit_registry.load_definitions(os.path.dirname(os.path.abspath(__file__)) + "/kubernetes_units.txt")
        self.quantity = self.unit_registry.Quantity
        self.request = BaseRequest(base_uri='http://')
        self.node_list = list()
        self.pod_key_resource = ['cpu_request', 'cpu_limit', 'mem_request', 'mem_limit']
        self.memory_free = float()
        self.memory_total = float()
        self._compute_allocated_resources()
        self.resource_result = ResourceResult()

    def _compute_allocated_resources(self):
        _queue = queue.Queue()
        get_all_node = partial(self.core_v1.list_node)
        threading.Thread(
            target=self._create_watcher(_queue=_queue, stream=get_all_node),
            daemon=True
        ).start()
        threading.Thread(
            target=partial(self._get_node_event, _queue=_queue),
            daemon=True
        ).start()

    def _create_watcher(self, _queue, stream):
        def watcher():
            for event in self.watch.stream(stream):
                _queue.put(event)

        return watcher

    def _get_node_event(self, _queue):
        while True:
            node_info = _queue.get()
            node_schedule = True
            if 'taints' in node_info['object']['spec']:
                for taint in node_info['object']['spec']['taints']:
                    if taint['effect'] == 'NoSchedule':
                        node_schedule = False
                        break
            if not node_schedule:
                continue
            resource_result_len = len(self.resource_result)
            for resource in self.resource_result:
                if resource['hostname'] == node_info['object']['metadata']['name']:
                    self._collect_container_resource(node_info, resource)
                    break
                resource_result_len -= 1
            if resource_result_len == 0:
                result = dict()
                for key in self.pod_key_resource:
                    result[key] = float()
                self.resource_result.append(result)
                self._collect_container_resource(node_info, result)

            self.node_list.append(node_info)

    def _collect_container_resource(self, node_info, result):
        node_name = node_info['object']['metadata']['name']
        result['hostname'] = node_name
        node_limit = int(int(node_info['object']['status']['allocatable']["pods"]) * 1.5)
        field_selector = ("status.phase!=Succeeded,status.phase!=Failed," +
                          "spec.nodeName=" + node_name)
        pods = self.core_v1.list_pod_for_all_namespaces(limit=node_limit,
                                                        field_selector=field_selector).items
        for pod in pods:
            for container in pod.spec.containers:
                res = container.resources
                reqs = defaultdict(lambda: 0, res.requests or {'cpu': '0m', 'memory': '0Mi'})
                limits = defaultdict(lambda: 0, res.limits or {'cpu': '0m', 'memory': '0Mi'})
                for key in self.pod_key_resource:
                    if 'request' in key:
                        if 'cpu' in key:
                            result[key] += self.quantity(reqs['cpu']).to('m').magnitude
                        else:
                            result[key] += self.quantity(reqs['memory']).to('Mi').magnitude
                    else:
                        if 'cpu' in key:
                            result[key] += self.quantity(limits['cpu']).to('m').magnitude
                        else:
                            result[key] += self.quantity(limits['memory']).to('Mi').magnitude

