from VIMManagement.utils.kubernetes_api import KubernetesApi


class NameSpaceClient(KubernetesApi):
    def __init__(self, *args, **kwargs):
        self.apply_cluster = kwargs['apply_cluster'] if 'apply_cluster' in kwargs else None

        

        super().__init__(*args, **kwargs)
        if self.apply_cluster:
            self.core_v1 = self.kubernetes_client.CoreV1Api(api_client=self.config.new_client_from_config(context=self.apply_cluster))

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
