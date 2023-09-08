import random
from VIMManagement.utils.kubernetes_api import KubernetesApi


class NodePortClient(KubernetesApi):
    def __init__(self, *args, **kwargs):
        self.service_type = kwargs['service_type'] if 'service_type' in kwargs else None
        self.protocol = kwargs['protocol'] if 'protocol' in kwargs else None
        self.virtualport = kwargs['virtualport'] if 'virtualport' in kwargs else None
        self.nodeport = kwargs['nodeport'] if 'nodeport' in kwargs else None
        self.nodeport_protocol = kwargs['nodeport_protocol'] if 'nodeport_protocol' in kwargs else None
        self.apply_cluster = kwargs['apply_cluster'] if 'apply_cluster' in kwargs else None

        super().__init__(*args, **kwargs)
        if self.apply_cluster:
            self.core_v1 = self.kubernetes_client.CoreV1Api(api_client=self.config.new_client_from_config(context=self.apply_cluster))

    def read_resource(self, **kwargs):
        return self.core_v1.read_namespaced_service(self.instance_name, self.namespace)

    def create_resource(self, **kwargs):
        try:
            self.core_v1.create_namespaced_service(self.namespace, self.resource)
        except Exception as e:
            print(e)
            resource = self.resource.to_dict()

            resource['spec']['ports'][0]['nodeport'] = self.nodeport
            self.core_v1.create_namespaced_service(self.namespace, resource)

    def patch_resource(self, **kwargs):
        self.core_v1.patch_namespaced_service(self.instance_name, self.namespace, self.resource)

    def delete_resource(self, **kwargs):
        self.core_v1.delete_namespaced_service(
            name=self.instance_name, namespace=self.namespace, body=self.delete_options)

    def _get_service_nodeport(self):
        i = 0
        service_port = list()
        for protocol in self.nodeport_protocol:
            service_port.append(
                self.kubernetes_client.V1ServicePort(
                    name=self.instance_name+str(self.nodeport[i]),
                    protocol=self.nodeport_protocol[i],
                    port=self.virtualport[i],
                    node_port=self.nodeport[i],
                    target_port=self.virtualport[i]
                )
            )
            i = i + 1
        return service_port 

    def instance_specific_resource(self, **kwargs):
        service = self.kubernetes_client.V1Service(api_version="v1", kind="Service")
        service_match_label={"nodeport":self.instance_name}
        service.metadata = self.kubernetes_client.V1ObjectMeta(name=self.instance_name,labels=service_match_label)
        service.spec = self.kubernetes_client.V1ServiceSpec(selector={'nodeport': self.instance_name}, ports=ports, type=self.service_type)
        return service

    

    def _create_service_nodeport(self,protocol,port,nodeport):
        return self.kubernetes_client.V1ServicePort(
            name='{}{}'.format(self.instance_name[-10:], port), port=int(port), protocol=protocol, node_port=int(nodeport), target_port=int(port))

