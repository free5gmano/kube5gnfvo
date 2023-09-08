from utils.tosca_paser.entity_template import EntityTemplate


class ServiceMeshTemplate(EntityTemplate):
    CIRCUIT_BREAKING_PROPERTIES = (MAX_CONNECTIONS, MAX_REQUESTS_PERCONNECTION) = \
            ('maxConnections', 'maxRequestsPerConnection')
    # RETRY_PROPERTIES = (ATTEMPTS, PER_TRY_TIMEOUT, RETRY_ON) = \
    #         ('attempts', 'perTryTimeout', 'retryOn')
    # CANARY_PROPERTIES = (HOSTNAME, subset, WEIGHT) = \
    #         ('hostname', 'subset', 'weight')
    properties_mapping = {
        "circuit_breaking": CIRCUIT_BREAKING_PROPERTIES,
        # "retry_policy": RETRY_PROPERTIES,
        # "canary": CANARY_PROPERTIES
    }
    

    def __init__(self, node_template, name):
        super().__init__(node_template, name)
        self.SERVICE_MESH_MODE = list(self.template.get(self.PROPERTIES).keys())[0]
        self.SERVICE_MESH_PROPERTIES = self.properties_mapping.get(self.SERVICE_MESH_MODE)
        # if self.SERVICE_MESH_MODE == "canary":
        #     self.properties = self._get_properties(properties_list=self.SERVICE_MESH_PROPERTIES)
        # else:
        #     self.properties = self._get_properties(self.SERVICE_MESH_PROPERTIES)
        
    def _validate_properties(self):
        if self.PROPERTIES not in self.template:
            self._value_empty_exception('service_mesh', self.PROPERTIES)
        
        properties = self.template.get(self.PROPERTIES)
        
        if not properties.get(self.SERVICE_MESH_MODE) or not isinstance(properties.get(self.SERVICE_MESH_MODE), dict):
            self._value_empty_exception('service mesh properties', self.SERVICE_MESH_MODE)
        return True

    def _validate_artifacts(self):
        pass

    def _validate_attributes(self):
        pass

    def _validate_requirements(self):
        pass

    def _validate_capabilities(self):
        pass
        