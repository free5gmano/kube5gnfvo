from VIMManagement.utils.kubernetes_api import KubernetesApi


class NameSpaceClient(KubernetesApi):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def read_resource(self, **kwargs):
        return self.core_v1.read_namespace(self.namespace)

    def create_resource(self, **kwargs):
        self.core_v1.create_namespace(self.resource)

    def patch_resource(self, **kwargs):
        print("can't patch")

    def delete_resource(self, **kwargs):
        self.core_v1.delete_namespaced_config_map(
            name=self.instance_name, namespace=self.namespace, body=self.delete_options)

    def instance_specific_resource(self, **kwargs):
        namespace = self.kubernetes_client.V1Namespace()
        namespace.metadata = self.kubernetes_client.V1ObjectMeta(name=self.namespace)
        return namespace
