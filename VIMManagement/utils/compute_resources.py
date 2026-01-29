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
from typing import Dict, Optional, Tuple

from pint import UnitRegistry

from VIMManagement.utils.base_kubernetes import BaseKubernetes, ResourceResult
from utils.base_request import BaseRequest


class ComputeResource(BaseKubernetes):
    """
    主要功能：
    - 監控 Node 事件（watch nodes）
    - 對每個可排程 node（無 NoSchedule taint）收集 pod container 的 request/limit
    - 從 Node Exporter（:9100/metrics）計算 cpu_usage、memory_usage
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.unit_registry = UnitRegistry()
        self.unit_registry.load_definitions(
            os.path.join(os.path.dirname(os.path.abspath(__file__)), "kubernetes_units.txt")
        )
        self.quantity = self.unit_registry.Quantity

        # 注意：base_uri 你原本是 'http://'，而你傳入 _get_resource 的 uri 是 'ip:9100/metrics'
        # 這裡維持你的寫法：request.get(uri) 由 BaseRequest 自行處理拼接/或直接使用完整 URL
        self.request = BaseRequest(base_uri="http://")

        # 你原本用 list，會無限增長；改成 dict 依 hostname 最新覆蓋
        self._nodes_by_name: Dict[str, dict] = {}

        self.pod_key_resource = ["cpu_request", "cpu_limit", "mem_request", "mem_limit"]

        self.resource_result = ResourceResult()

        # 簡單 lock，避免多 thread 同時操作 resource_result / nodes
        self._lock = threading.RLock()

        self._compute_allocated_resources()

    def _compute_allocated_resources(self):
        _queue = queue.Queue()
        get_all_node = partial(self.core_v1.list_node)

        threading.Thread(
            target=self._create_watcher(_queue=_queue, stream=get_all_node),
            daemon=True,
        ).start()

        threading.Thread(
            target=partial(self._get_node_event, _queue=_queue),
            daemon=True,
        ).start()

        threading.Thread(
            target=partial(self._collect_resource),
            daemon=True,
        ).start()

    def _create_watcher(self, _queue, stream):
        def watcher():
            for event in self.watch.stream(stream):
                _queue.put(event)

        return watcher

    def _get_node_event(self, _queue: queue.Queue):
        """
        watch node event，過濾 NoSchedule 的 node，更新 resource_result 中對應 hostname 的基礎資料（含 request/limit）。
        """
        while True:
            node_info = _queue.get()
            try:
                node_obj = node_info.get("object")
                if not node_obj:
                    continue

                node_name = node_obj["metadata"]["name"]

                # 過濾 NoSchedule taint
                node_schedule = True
                taints = node_obj.get("spec", {}).get("taints", [])
                for taint in taints:
                    if taint.get("effect") == "NoSchedule":
                        node_schedule = False
                        break
                if not node_schedule:
                    continue

                with self._lock:
                    # 更新 nodes dict
                    self._nodes_by_name[node_name] = node_info

                    # 取得/建立 result entry
                    result = self._get_or_create_result_entry(node_name)

                # 收集 container request/limit（這段可能較慢，避免長時間持有 lock）
                self._collect_container_resource(node_info, result)

            except Exception:
                # 靜默處理任何錯誤，繼續監控
                continue

    def _get_or_create_result_entry(self, node_name: str) -> dict:
        """
        從 resource_result 找 hostname= node_name 的 entry；找不到就建立一個。
        """
        # ResourceResult 可能是 list-like
        for res in self.resource_result:
            if res.get("hostname") == node_name:
                return res

        # 建立新的 entry
        result = {"hostname": node_name}
        for key in self.pod_key_resource:
            result[key] = 0.0

        # 初始化額外欄位，避免 API 回傳時缺 key
        result["host_ip"] = ""
        result["cpu_usage"] = 0.0
        result["total_cpu"] = 0.0
        result["memory_usage"] = 0.0
        result["total_memory"] = 0.0

        self.resource_result.append(result)
        return result

    def _collect_container_resource(self, node_info: dict, result: dict):
        """
        針對指定 node，列出該 node 上的 pods，累加所有 container requests/limits。
        """
        node_obj = node_info["object"]
        node_name = node_obj["metadata"]["name"]

        # 先把原本累加的值歸零，避免 watch 更新時重複累加
        for key in self.pod_key_resource:
            result[key] = 0.0

        # node 可承載 pods * 1.5：沿用你原本邏輯
        node_allocatable = node_obj["status"]["allocatable"]
        try:
            node_limit = int(int(node_allocatable.get("pods", 0)) * 1.5)
        except Exception:
            node_limit = 0

        field_selector = (
            "status.phase!=Succeeded,status.phase!=Failed," + "spec.nodeName=" + node_name
        )

        pods = self.core_v1.list_pod_for_all_namespaces(
            limit=node_limit if node_limit > 0 else None,
            field_selector=field_selector,
        ).items

        for pod in pods:
            for container in pod.spec.containers:
                res = container.resources
                reqs = defaultdict(lambda: "0", (res.requests or {}))
                limits = defaultdict(lambda: "0", (res.limits or {}))

                # 預設避免 None
                if not reqs.get("cpu"):
                    reqs["cpu"] = "0m"
                if not reqs.get("memory"):
                    reqs["memory"] = "0Mi"
                if not limits.get("cpu"):
                    limits["cpu"] = "0m"
                if not limits.get("memory"):
                    limits["memory"] = "0Mi"

                for key in self.pod_key_resource:
                    if "request" in key:
                        if "cpu" in key:
                            result[key] += self.quantity(reqs["cpu"]).to("m").magnitude
                        else:
                            result[key] += self.quantity(reqs["memory"]).to("Mi").magnitude
                    else:
                        if "cpu" in key:
                            result[key] += self.quantity(limits["cpu"]).to("m").magnitude
                        else:
                            result[key] += self.quantity(limits["memory"]).to("Mi").magnitude

    def _collect_resource(self):
        """
        每 3 秒掃描所有 node，更新 cpu_usage / memory_usage / total_cpu / total_memory / host_ip。
        """
        while True:
            try:
                # 拷貝一份 nodes，避免掃描時 dict 被更新
                with self._lock:
                    nodes_snapshot = list(self._nodes_by_name.values())
                    results_snapshot = list(self.resource_result)

                for node_info in nodes_snapshot:
                    node_name = node_info["object"]["metadata"]["name"]

                    # 找對應 result
                    target = None
                    for r in results_snapshot:
                        if r.get("hostname") == node_name:
                            target = r
                            break
                    if not target:
                        continue

                    self._calculation_resource(node_info, target)

            except Exception:
                # 靜默處理任何錯誤，繼續監控
                pass

            time.sleep(3)

    def _calculation_resource(self, node_info: dict, result: dict):
        """
        計算該 node 的 total_cpu/total_memory/cpu_usage/memory_usage。
        cpu_usage: 透過兩次取樣 node_cpu_seconds_total 差分估算
        memory_usage: 優先用 MemAvailable，否則回退 MemFree
        """
        node_obj = node_info["object"]
        node_allocatable = node_obj["status"]["allocatable"]

        # total_cpu / total_memory（allocatable）
        try:
            # allocatable["cpu"] 通常是整數 core
            result["total_cpu"] = self.quantity(int(node_allocatable["cpu"]), "cpu").to("m").magnitude
        except Exception:
            # 若格式不符，保守設 0
            result["total_cpu"] = 0.0

        try:
            result["total_memory"] = round(self.quantity(node_allocatable["memory"]).to("Mi").magnitude, 2)
        except Exception:
            result["total_memory"] = 0.0

        # host_ip + metrics
        internal_ip = None
        for address in node_obj["status"].get("addresses", []):
            if address.get("type") == "InternalIP":
                internal_ip = address.get("address")
                break

        if not internal_ip:
            result["host_ip"] = ""
            result["cpu_usage"] = 0.0
            result["memory_usage"] = 0.0
            return

        result["host_ip"] = internal_ip

        # 先抓一次 metrics（含 memory）
        try:
            older_idle, older_total, mem_free, mem_total, mem_available = self._get_resource(
                f"{internal_ip}:9100/metrics"
            )
        except Exception:
            result["cpu_usage"] = 0.0
            result["memory_usage"] = 0.0
            return

        # 第二次取樣只需要 CPU 即可（仍可一起抓，但不強求）
        time.sleep(1)
        try:
            newer_idle, newer_total, _, _, _ = self._get_resource(f"{internal_ip}:9100/metrics")
        except Exception:
            newer_idle, newer_total = older_idle, older_total

        # CPU usage（差分）
        try:
            delta_total = newer_total - older_total
            if delta_total > 0:
                delta_idle = newer_idle - older_idle
                cpu_utilization = (delta_total - delta_idle) / delta_total
                # 你原本是 total_cpu * round(util,2) => 相當於「以 millicore 表示使用量」
                result["cpu_usage"] = result["total_cpu"] * round(cpu_utilization, 2)
            else:
                result["cpu_usage"] = 0.0
        except Exception:
            result["cpu_usage"] = 0.0

        # Memory usage（優先 MemAvailable）
        try:
            if mem_total and mem_total > 0:
                if mem_available is not None:
                    used_bytes = mem_total - mem_available
                elif mem_free is not None:
                    used_bytes = mem_total - mem_free
                else:
                    used_bytes = 0.0

                result["memory_usage"] = round(
                    self.quantity(used_bytes, "byte").to("Mi").magnitude, 2
                )
            else:
                result["memory_usage"] = 0.0
        except Exception:
            result["memory_usage"] = 0.0

    def _get_resource(
        self, uri: str
    ) -> Tuple[float, float, Optional[float], Optional[float], Optional[float]]:
        """
        解析 Node Exporter /metrics（Prometheus text format）

        回傳：
        -   
        - cpu_total_seconds_sum
        - mem_free_bytes (可能 None)
        - mem_total_bytes (可能 None)
        - mem_available_bytes (可能 None)
        """
        metrics_data = self.request.get(uri).text.splitlines()

        cpu_idle = 0.0
        cpu_total = 0.0
        mem_free = None
        mem_total = None
        mem_available = None

        for line in metrics_data:
            if not line or line.startswith("#"):
                continue

            parts = line.split()
            if len(parts) < 2:
                continue

            metric = parts[0]
            value_str = parts[-1]

            # 有些行最後一欄可能不是數字（極少見），保守略過
            try:
                value = float(value_str)
            except Exception:
                continue

            # CPU
            if metric.startswith("node_cpu_seconds_total"):
                cpu_total += value
                # 精準判 idle：Prometheus labels 會在 metric 文字中（例如 ...{mode="idle",cpu="0"}）
                if 'mode="idle"' in metric:
                    cpu_idle += value

            # Memory
            elif metric.startswith("node_memory_MemTotal_bytes"):
                mem_total = value
            elif metric.startswith("node_memory_MemAvailable_bytes"):
                mem_available = value
            elif metric.startswith("node_memory_MemFree_bytes"):
                mem_free = value

        return cpu_idle, cpu_total, mem_free, mem_total, mem_available
