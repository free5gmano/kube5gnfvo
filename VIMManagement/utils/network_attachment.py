from VIMManagement.utils.base_kubernetes import BaseKubernetes


class NetworkAttachment(BaseKubernetes):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def list_resource(self) -> list:
        resource = self.api_crd.list_cluster_custom_object(
            group='k8s.cni.cncf.io',
            version='v1',
            plural='network-attachment-definitions')
        return [_['metadata']['name'] for _ in resource['items']]
