# All Rights Reserved.
#
# Resource pressure monitor: periodically polls metrics-server for pod
# CPU/Memory usage and creates alarms when usage exceeds thresholds.
#
# Detects three new fault types beyond CrashLoopBackOff:
#   - MemoryPressure: pod memory usage > 85% of limit
#   - CPUPressure:    pod CPU usage > 80% of limit (CPU throttling)
#   - TrafficSurge:   sustained high CPU on multiple VNFs in same slice
#
import time
import traceback
from collections import defaultdict
from typing import Dict, List, Optional, Tuple

from kubernetes import client


# Thresholds
MEMORY_THRESHOLD_PCT = 85.0   # memory usage > 85% of limit → MemoryPressure
CPU_THRESHOLD_PCT = 80.0      # cpu usage > 80% of limit → CPUPressure
TRAFFIC_SURGE_THRESHOLD_PCT = 70.0  # cpu > 70% on multiple VNFs simultaneously
TRAFFIC_SURGE_MIN_VNF_COUNT = 3      # at least 3 VNFs hot at same time
SUSTAINED_CHECKS = 2  # need 2 consecutive checks to confirm pressure (avoid flapping)

# Polling interval
POLL_INTERVAL_SECONDS = 30


def _parse_cpu_to_millicores(value: str) -> int:
    """Convert K8s CPU string to millicores int.
    Examples: '250m' -> 250, '1' -> 1000, '500000000n' -> 500
    """
    if not value:
        return 0
    value = str(value).strip()
    try:
        if value.endswith("m"):
            return int(value[:-1])
        if value.endswith("n"):
            # nanocores → millicores
            return int(int(value[:-1]) / 1_000_000)
        if value.endswith("u"):
            return int(int(value[:-1]) / 1_000)
        return int(float(value) * 1000)
    except (ValueError, TypeError):
        return 0


def _parse_memory_to_mi(value: str) -> int:
    """Convert K8s memory string to MiB int.
    Examples: '256Mi' -> 256, '1Gi' -> 1024, '134217728' -> 128
    """
    if not value:
        return 0
    value = str(value).strip()
    try:
        if value.endswith("Gi"):
            return int(float(value[:-2]) * 1024)
        if value.endswith("Mi"):
            return int(float(value[:-2]))
        if value.endswith("Ki"):
            return int(float(value[:-2]) / 1024)
        if value.endswith("G"):
            return int(float(value[:-1]) * 1000)
        if value.endswith("M"):
            return int(float(value[:-1]))
        if value.endswith("K"):
            return int(float(value[:-1]) / 1000)
        # raw bytes
        return int(int(value) / (1024 * 1024))
    except (ValueError, TypeError):
        return 0


class ResourceMonitor(object):
    """
    Polls Kubernetes metrics-server every POLL_INTERVAL_SECONDS and creates
    alarms for pods whose resource usage exceeds thresholds.
    Designed to be run in a daemon thread.
    """

    def __init__(self, core_v1_api, alarm_event):
        self.core_v1 = core_v1_api
        self.alarm = alarm_event
        # custom objects API for metrics-server
        self.custom_api = client.CustomObjectsApi()
        # cache pod limits to avoid repeatedly fetching pod specs
        self._pod_limits_cache: Dict[str, Dict[str, Tuple[int, int]]] = {}
        # track consecutive pressure observations per pod (avoid flapping)
        self._pressure_streak: Dict[str, int] = defaultdict(int)
        # track high-cpu pods per slice for traffic-surge detection
        self._cpu_high_streak: Dict[str, int] = defaultdict(int)

    def run_forever(self):
        """Main polling loop. Runs until process exit."""
        print("[ResourceMonitor] starting polling loop")
        while True:
            try:
                self._poll_once()
            except Exception:
                traceback.print_exc()
            time.sleep(POLL_INTERVAL_SECONDS)

    def _poll_once(self):
        """Single polling cycle: fetch metrics, compare, raise alarms."""
        try:
            metrics = self.custom_api.list_cluster_custom_object(
                group="metrics.k8s.io",
                version="v1beta1",
                plural="pods",
            )
        except Exception as e:
            # metrics-server not installed or unreachable; skip silently
            print(f"[ResourceMonitor] metrics-server unreachable: {e}")
            return

        items = metrics.get("items", []) if isinstance(metrics, dict) else []

        # Track per-pod-cpu-percentage for traffic surge detection
        per_pod_cpu_pct: Dict[str, float] = {}

        for pod_metric in items:
            try:
                self._check_pod(pod_metric, per_pod_cpu_pct)
            except Exception:
                traceback.print_exc()

        self._check_traffic_surge(per_pod_cpu_pct)

    def _check_pod(self, pod_metric: dict, per_pod_cpu_pct: dict):
        """Check one pod's metrics against its limits."""
        meta = pod_metric.get("metadata", {})
        pod_name = meta.get("name", "")
        namespace = meta.get("namespace", "")
        if not pod_name or not namespace:
            return

        containers = pod_metric.get("containers", [])
        if not containers:
            return

        # Sum usage across all containers in this pod
        total_cpu_usage_m = 0
        total_mem_usage_mi = 0
        for c in containers:
            usage = c.get("usage", {})
            total_cpu_usage_m += _parse_cpu_to_millicores(usage.get("cpu", "0"))
            total_mem_usage_mi += _parse_memory_to_mi(usage.get("memory", "0"))

        # Get pod limits
        cpu_limit_m, mem_limit_mi = self._get_pod_limits(pod_name, namespace)
        if cpu_limit_m <= 0 and mem_limit_mi <= 0:
            return  # no limits set, can't compute percentage

        cpu_pct = (total_cpu_usage_m / cpu_limit_m * 100) if cpu_limit_m > 0 else 0
        mem_pct = (total_mem_usage_mi / mem_limit_mi * 100) if mem_limit_mi > 0 else 0

        per_pod_cpu_pct[pod_name] = cpu_pct

        # MemoryPressure check
        if mem_pct >= MEMORY_THRESHOLD_PCT:
            key = f"{pod_name}:mem"
            self._pressure_streak[key] += 1
            if self._pressure_streak[key] >= SUSTAINED_CHECKS:
                self._raise_alarm(
                    pod_name,
                    "MemoryPressure",
                    f"Pod memory usage {total_mem_usage_mi}Mi / limit {mem_limit_mi}Mi ({mem_pct:.1f}%)",
                )
                self._pressure_streak[key] = 0
        else:
            self._pressure_streak[f"{pod_name}:mem"] = 0

        # CPUPressure check
        if cpu_pct >= CPU_THRESHOLD_PCT:
            key = f"{pod_name}:cpu"
            self._pressure_streak[key] += 1
            if self._pressure_streak[key] >= SUSTAINED_CHECKS:
                self._raise_alarm(
                    pod_name,
                    "CPUPressure",
                    f"Pod CPU usage {total_cpu_usage_m}m / limit {cpu_limit_m}m ({cpu_pct:.1f}%) — likely throttled",
                )
                self._pressure_streak[key] = 0
        else:
            self._pressure_streak[f"{pod_name}:cpu"] = 0

    def _check_traffic_surge(self, per_pod_cpu_pct: Dict[str, float]):
        """
        Detect traffic surge: when many pods sharing a slice prefix have
        high CPU at the same time, treat it as load-driven.
        """
        # group pods by their VNF prefix (first 8 chars = slice/workspace prefix)
        slice_hot_pods: Dict[str, List[str]] = defaultdict(list)
        for pod_name, cpu_pct in per_pod_cpu_pct.items():
            if cpu_pct >= TRAFFIC_SURGE_THRESHOLD_PCT:
                # use first 8 chars as slice key (matches workspace UUID prefix)
                prefix = pod_name[:8] if len(pod_name) >= 8 else pod_name
                slice_hot_pods[prefix].append(pod_name)

        for prefix, hot_pods in slice_hot_pods.items():
            if len(hot_pods) < TRAFFIC_SURGE_MIN_VNF_COUNT:
                continue
            # need to confirm sustained
            self._cpu_high_streak[prefix] += 1
            if self._cpu_high_streak[prefix] >= SUSTAINED_CHECKS:
                # raise traffic surge alarm on the most representative VNF
                # (pick first hot pod as the representative)
                representative = sorted(hot_pods)[0]
                self._raise_alarm(
                    representative,
                    "TrafficSurge",
                    f"Slice {prefix}: {len(hot_pods)} VNFs hot simultaneously: {', '.join(hot_pods)}",
                )
                self._cpu_high_streak[prefix] = 0

        # decay streaks for slices that are now cool
        for prefix in list(self._cpu_high_streak.keys()):
            if prefix not in slice_hot_pods:
                self._cpu_high_streak[prefix] = 0

    def _get_pod_limits(self, pod_name: str, namespace: str) -> Tuple[int, int]:
        """Return (cpu_limit_millicores, memory_limit_mi) for the pod."""
        cache_key = f"{namespace}/{pod_name}"
        if cache_key in self._pod_limits_cache:
            cached = self._pod_limits_cache[cache_key]
            return cached.get("cpu", 0), cached.get("mem", 0)

        try:
            pod = self.core_v1.read_namespaced_pod(name=pod_name, namespace=namespace)
        except Exception:
            return 0, 0

        total_cpu = 0
        total_mem = 0
        for c in pod.spec.containers or []:
            limits = (c.resources.limits if c.resources else {}) or {}
            total_cpu += _parse_cpu_to_millicores(limits.get("cpu", "0"))
            total_mem += _parse_memory_to_mi(limits.get("memory", "0"))

        self._pod_limits_cache[cache_key] = {"cpu": total_cpu, "mem": total_mem}
        return total_cpu, total_mem

    def _raise_alarm(self, pod_name: str, reason: str, message: str):
        """Create an alarm via the existing AlarmEvent infrastructure."""
        try:
            self.alarm.create_alarm(pod_name, reason, message, True)
            print(f"[ResourceMonitor] alarm raised: {reason} on {pod_name}")
        except Exception:
            traceback.print_exc()
