from VIMManagement.utils.kubernetes_api import KubernetesApi


class ServiceClient(KubernetesApi):
    def __init__(self, *args, **kwargs):
        self.service_type = kwargs['service_type'] if 'service_type' in kwargs else None
        self.ports = kwargs['ports'] if 'ports' in kwargs else None
        self.protocol = kwargs['protocol'] if 'protocol' in kwargs else None
        self.target_port = kwargs['target_port'] if 'target_port' in kwargs else None
        self.node_port = kwargs['node_port'] if 'node_port' in kwargs else None
        super().__init__(*args, **kwargs)

    def read_resource(self, **kwargs):
        return self.core_v1.read_namespaced_service(self.instance_name, self.namespace)

    def create_resource(self, **kwargs):
        try:
            self.core_v1.create_namespaced_service(self.namespace, self.resource)
        except:
            resource = self.resource.to_dict()
            resource['spec']['ports'][0]['node_port'] = 31111
            self.core_v1.create_namespaced_service(self.namespace, resource)

    def patch_resource(self, **kwargs):
        self.core_v1.patch_namespaced_service(self.instance_name, self.namespace, self.resource)

    def delete_resource(self, **kwargs):
        self.core_v1.delete_namespaced_service(
            name=self.instance_name, namespace=self.namespace, body=self.delete_options)

    def instance_specific_resource(self, **kwargs):
        service = self.kubernetes_client.V1Service(api_version="v1", kind="Service")
        service_match_label={"app":self.instance_name}
        service.metadata = self.kubernetes_client.V1ObjectMeta(name=self.instance_name,labels=service_match_label)
        if self.node_port != None :
            #use cluster_ip='None' is not create Node_Port
            service.spec = self.kubernetes_client.V1ServiceSpec(
                selector={'app': self.instance_name}, ports=self._get_service_node_port(), type=self.service_type)
        else:
            service.spec = self.kubernetes_client.V1ServiceSpec(
                cluster_ip='None', selector={'app': self.instance_name}, ports=self._get_service_port(), type=self.service_type)
        return service

    def _get_service_port(self):
        if self.protocol is None:
            protocol = 'TCP'
            return [self._create_service_port(protocol, port) for port in self.ports]
        else:
            i = 0
            service_port = list()
            # print(self.protocol)
            # print(self.protocol)
            for protocol in [self.protocol]:
                # print("=============================")
                # print(protocol)
                # print("=============================")
                # print(self.ports[i])
                service_port.append(self._create_service_port(protocol, self.ports[i]))
                i = i + 1
            return service_port
    def _get_service_node_port(self):
        if self.protocol is None:
            protocol = 'TCP'
            return [self._create_service_node_port(protocol, port,self.target_port,self.node_port) for port in self.ports]
        else:
            i = 0
            service_port = list()
            for protocol in self.protocol:
                service_port.append(self._create_service_node_port(protocol, self.ports[i],self.target_port,self.node_port))
                i = i + 1
            return service_port
    def _create_service_node_port(self,protocol,port,target_port,node_port):
        if target_port is None:
            return self.kubernetes_client.V1ServicePort(
                name='{}{}'.format(self.instance_name[-10:], port), port=int(port), protocol=protocol,
                                    node_port=int(node_port))
        else:
            return self.kubernetes_client.V1ServicePort(
                name='{}{}'.format(self.instance_name[-10:], port), port=int(port), protocol=protocol,
                                    target_port=int(target_port),node_port=int(node_port))

    def _create_service_port(self, protocol, port):
        return self.kubernetes_client.V1ServicePort(
            name='{}{}'.format(self.instance_name[-10:], port), port=int(port), protocol=protocol)
