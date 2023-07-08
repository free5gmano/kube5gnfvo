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

import functools
import os
import threading
from kubernetes import client, config, watch
from kubernetes.client.rest import ApiException
from pick import pick
from os_ma_nfvo.settings import MASTER_CLUSTER, WORKER_CLUSTER

lock = threading.Lock()


def synchronized(_lock):
    def wrapper(func):
        @functools.wraps(func)
        def inner_wrapper(*args, **kwargs):
            with _lock:
                return func(*args, **kwargs)

        return inner_wrapper

    return wrapper


class Singleton(type):
    _instances = {}

    @synchronized(lock)
    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


class ResourceResult(list, metaclass=Singleton):
    pass


class DeploymentStatus(dict, metaclass=Singleton):
    pass


class PodStatus(dict, metaclass=Singleton):
    def __setitem__(self, *args, **kwargs):
        if args[0] in self and self[args[0]] == 'Terminating':
            return

        super().__setitem__(*args, **kwargs)


class VirtualMachineStatus(dict, metaclass=Singleton):
    pass


class VirtualMachineReplicaSetStatus(dict, metaclass=Singleton):
    pass


class BaseKubernetes(object):
    def __init__(self, *args, **kwargs):
        self.kubernetes_client = client
        self.kubeconfig = os.path.expanduser("~/.kube/config")
        self.config = config
        self.config.load_kube_config(config_file=self.kubeconfig)
        kube_config_loader = self.config.kube_config._get_kube_config_loader_for_yaml_file(self.kubeconfig)
        
        self.core_v1 = self.kubernetes_client.CoreV1Api()
        # self.core_v1 = {"master_cluster": self.kubernetes_client.CoreV1Api(api_client=config.new_client_from_config(context=MASTER_CLUSTER))}
        # for worker_cluster in WORKER_CLUSTER:
        #     self.core_v1[worker_cluster] = self.kubernetes_client.CoreV1Api(api_client=config.new_client_from_config(context=worker_cluster))
        # self.configuration = kubernetes.client.Configuration()
        # self.ApiClient = kubernetes_client.ApiClient()
        self.app_v1 = self.kubernetes_client.AppsV1Api()
        self.api_crd = self.kubernetes_client.CustomObjectsApi()
        self.ApiException = ApiException
        self.service_instance = None
        self.watch = watch.Watch()
        self.lock = threading.Lock()
        self.rbac_authorization_v1 = self.kubernetes_client.RbacAuthorizationV1Api()
        self.auto_scaling_v1 = self.kubernetes_client.AutoscalingV1Api()
        self.deployment_status = DeploymentStatus()
        self.pod_status = PodStatus()
        self.virtual_machine_status = VirtualMachineStatus()
        self.virtual_machine_replica_set = VirtualMachineReplicaSetStatus()
        self.networking_v1 = self.kubernetes_client.NetworkingV1Api()
        self.network_policy_v1 = self.kubernetes_client.V1NetworkPolicy()
