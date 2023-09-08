import os
import docker
from os_ma_nfvo.settings import WORKER_CLUSTER

class DockerClient():
    def __init__(self, *args, **kwargs):
        self.virtualport = kwargs['virtualport'] if 'virtualport' in kwargs else None
        self.nodeport = kwargs['nodeport'] if 'nodeport' in kwargs else None
        self.nodeport_protocol = kwargs['nodeport_protocol'] if 'nodeport_protocol' in kwargs else None
        self.apply_cluster = kwargs['apply_cluster'] if 'apply_cluster' in kwargs else None
        self.image = kwargs['image'] if 'image' in kwargs else None
        
        os.environ["DOCKER_HOST"] = 'tcp://'+WORKER_CLUSTER[self.apply_cluster]+':2375'
        self.client = docker.from_env()


    def handle_create_or_update(self):
        self.create_resource()

    def read_resource(self, **kwargs):
        pass

    def create_resource(self, **kwargs):
        self.client.containers.run(self.image, ports={str(self.nodeport[0])+'/'+self.nodeport_protocol[0]: self.virtualport[0]})

    def patch_resource(self, **kwargs):
        return
        self.core_v1.patch_namespaced_service(self.instance_name, self.namespace, self.resource)

    def delete_resource(self, **kwargs):
        return
        self.core_v1.delete_namespaced_service(
            name=self.instance_name, namespace=self.namespace, body=self.delete_options)

    def instance_specific_resource(self, **kwargs):
        return
        service = self.kubernetes_client.V1Service(api_version="v1", kind="Service")
        service_match_label={"nodeport":self.instance_name}
        service.metadata = self.kubernetes_client.V1ObjectMeta(name=self.instance_name,labels=service_match_label)
        service.spec = self.kubernetes_client.V1ServiceSpec(selector={'nodeport': self.instance_name}, ports=[self.kubernetes_client.V1ServicePort(protocol="TCP", port=8080, target_port=8080, node_port=30080)], type=self.service_type)
        return service


