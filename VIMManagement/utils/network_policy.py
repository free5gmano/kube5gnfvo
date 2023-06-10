from VIMManagement.utils.kubernetes_api import KubernetesApi

class NetworkPolicyClient(KubernetesApi):
    def __init__(self, *args, **kwargs):
        self.network_policy = kwargs['network_policy'] if 'network_policy' in kwargs else None
        self.apply_cluster = kwargs['apply_cluster'] if 'apply_cluster' in kwargs else None
        super().__init__(*args, **kwargs)
        if self.apply_cluster:
            self.core_v1 = self.kubernetes_client.CoreV1Api(api_client=self.config.new_client_from_config(context=self.apply_cluster))
    def read_resource(self, **kwargs):
        return self.networking_v1.read_namespaced_network_policy(self.network_policy, self.namespace)
    
    def create_resource(self, **kwargs):
        print(self.network_policy_v1)
        network_policy_v1 = {
            "apiVersion": "networking.k8s.io/v1",
            "kind": "NetworkPolicy",
            "metadata": {
                "name": "test-network-policy",
                "namespace": "tn1"
            },
            "spec": {
                "podSelector": {},
                "policyTypes": [
                "Ingress"
                ],
                "ingress": [
                {
                    "from": [
                    {
                        "ipBlock": {
                        "cidr": "0.0.0.0/0",
                        "except": [
                            "192.168.242.0/24"
                        ]
                        }
                    },
                    {
                        "podSelector": {}
                    }
                    ]
                }
                ]
            }
            }
        # resource = self.resource.to_dict()
        
        # resource['spec']['ports'][0]['node_port'] = random.randrange(30000, 40000)
        if not self.networking_v1.list_namespaced_network_policy(self.namespace):
            self.networking_v1.create_namespaced_network_policy(self.namespace, network_policy_v1)

    # def patch_resource(self, **kwargs):
    #     self.core_v1.patch_namespaced_service(self.instance_name, self.namespace, self.resource)

    # def delete_resource(self, **kwargs):
    #     self.core_v1.delete_namespaced_service(
            # name=self.instance_name, namespace=self.namespace, body=self.delete_options)

    # def instance_specific_resource(self, **kwargs):
    #     service = self.kubernetes_client.V1Service(api_version="v1", kind="Service")
    #     service_match_label={"app":self.instance_name}
    #     service.metadata = self.kubernetes_client.V1ObjectMeta(name=self.instance_name,labels=service_match_label)
    #     if self.node_port != None :
    #         #use cluster_ip='None' is not create Node_Port
    #         service.spec = self.kubernetes_client.V1ServiceSpec(
    #             selector={'app': self.instance_name}, ports=self._get_service_node_port(), type=self.service_type)
    #     else:
    #         service.spec = self.kubernetes_client.V1ServiceSpec(
    #             cluster_ip='None', selector={'app': self.instance_name}, ports=self._get_service_port(), type=self.service_type)
    #     return service

    # def _get_service_port(self):
    #     if self.protocol is None:
    #         protocol = 'TCP'
    #         return [self._create_service_port(protocol, port) for port in self.ports]
    #     else:
    #         i = 0
    #         service_port = list()
    #         for protocol in [self.protocol]:
    #             service_port.append(self._create_service_port(protocol, self.ports[i]))
    #             i = i + 1
    #         return service_port
    # def _get_service_node_port(self):
    #     if self.protocol is None:
    #         protocol = 'TCP'
    #         return [self._create_service_node_port(protocol, port,self.target_port,self.node_port) for port in self.ports]
    #     else:
    #         i = 0
    #         service_port = list()
    #         for protocol in self.protocol:
    #             service_port.append(self._create_service_node_port(protocol, self.ports[i],self.target_port,self.node_port))
    #             i = i + 1
    #         return service_port
    # def _create_service_node_port(self,protocol,port,target_port,node_port):
    #     if target_port is None:
    #         return self.kubernetes_client.V1ServicePort(
    #             name='{}{}'.format(self.instance_name[-10:], port), port=int(port), protocol=protocol,
    #                                 node_port=int(node_port))
    #     else:
    #         return self.kubernetes_client.V1ServicePort(
    #             name='{}{}'.format(self.instance_name[-10:], port), port=int(port), protocol=protocol,
    #                                 target_port=int(target_port),node_port=int(node_port))

    # def _create_service_port(self, protocol, port):
    #     return self.kubernetes_client.V1ServicePort(
    #         name='{}{}'.format(self.instance_name[-10:], port), port=int(port), protocol=protocol)