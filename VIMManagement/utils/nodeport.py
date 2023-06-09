import random
from VIMManagement.utils.kubernetes_api import KubernetesApi


class NodePortClient(KubernetesApi):
    def __init__(self, *args, **kwargs):
        self.service_type = kwargs['service_type'] if 'service_type' in kwargs else None

        # self.virtualport = kwargs['nodeport'] if 'nodeport' in kwargs else None
        self.protocol = kwargs['protocol'] if 'protocol' in kwargs else None
        self.target_port = kwargs['target_port'] if 'target_port' in kwargs else None
        self.virtualport = kwargs['virtualport'] if 'virtualport' in kwargs else None
        self.nodeport = kwargs['nodeport'] if 'nodeport' in kwargs else None
        self.nodeport_protocol = kwargs['nodeport_protocol'] if 'nodeport_protocol' in kwargs else None
        super().__init__(*args, **kwargs)

    def read_resource(self, **kwargs):
        return self.core_v1.read_namespaced_service(self.instance_name, self.namespace)

    def create_resource(self, **kwargs):
        try:
            self.core_v1.create_namespaced_service(self.instance_name, self.resource)
        except:
            resource = self.resource.to_dict()
            resource['spec']['ports'][0]['nodeport'] = self.nodeport
            self.core_v1.create_namespaced_service(self.namespace, resource)

    def patch_resource(self, **kwargs):
        self.core_v1.patch_namespaced_service(self.instance_name, self.namespace, self.resource)

    def delete_resource(self, **kwargs):
        self.core_v1.delete_namespaced_service(
            name=self.instance_name, namespace=self.namespace, body=self.delete_options)

    def instance_specific_resource(self, **kwargs):
        service = self.kubernetes_client.V1Service(api_version="v1", kind="Service")
        service_match_label={"nodeport":self.instance_name}
        service.metadata = self.kubernetes_client.V1ObjectMeta(name=self.instance_name,labels=service_match_label)
        print(self.service_type)
        service.spec = self.kubernetes_client.V1ServiceSpec(selector={'nodeport': self.instance_name}, ports=self._get_service_nodeport(), type=self.service_type)
        return service

    def _get_service_nodeport(self):
        i = 0
        service_port = list()
        for protocol in self.nodeport_protocol:
            print(self.nodeport[i])
            service_port.append(self._create_service_nodeport(protocol, self.virtualport[i],self.nodeport[i]))
            i = i + 1
        return service_port

    def _create_service_nodeport(self,protocol,port,nodeport):
        return self.kubernetes_client.V1ServicePort(
            name='{}{}'.format(self.instance_name[-10:], port), port=int(port), protocol=protocol, node_port=int(nodeport))

