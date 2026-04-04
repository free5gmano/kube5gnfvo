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

from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.views.decorators.csrf import csrf_exempt
from VIMManagement.utils.base_kubernetes import ResourceResult
from VIMManagement.utils.compute_resources import ComputeResource
from VIMManagement.utils.service import ServiceClient

ComputeResource()
@csrf_exempt
@api_view(['GET'])
def kubernetes_resource(request):
    return Response(status=status.HTTP_200_OK, data=ResourceResult())


@csrf_exempt
@api_view(['GET'])
def kubernetes_service_detail(request, namespace, service_name):
    service_client = ServiceClient(instance_name=service_name, namespace=namespace)
    try:
        service = service_client.read_resource()
    except service_client.ApiException as exc:
        if exc.status == 404:
            return Response(
                {'error': f'Service {service_name} not found in namespace {namespace}'},
                status=status.HTTP_404_NOT_FOUND
            )
        return Response(
            {'error': f'Failed to load service {service_name}: {exc.reason}'},
            status=status.HTTP_502_BAD_GATEWAY
        )
    except Exception as exc:
        return Response(
            {'error': f'Failed to load service {service_name}: {str(exc)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

    endpoint_addresses = []
    try:
        endpoints = service_client.core_v1.read_namespaced_endpoints(service_name, namespace)
        for subset in (endpoints.subsets or []):
            for address in (subset.addresses or []):
                endpoint_addresses.append({
                    'ip': address.ip,
                    'nodeName': getattr(address, 'node_name', None),
                    'targetRef': {
                        'kind': getattr(getattr(address, 'target_ref', None), 'kind', None),
                        'name': getattr(getattr(address, 'target_ref', None), 'name', None),
                        'namespace': getattr(getattr(address, 'target_ref', None), 'namespace', None),
                    } if getattr(address, 'target_ref', None) else None,
                })
    except service_client.ApiException:
        endpoint_addresses = []

    return Response({
        'name': service.metadata.name,
        'namespace': service.metadata.namespace,
        'type': getattr(service.spec, 'type', None),
        'clusterIP': getattr(service.spec, 'cluster_ip', None),
        'headless': getattr(service.spec, 'cluster_ip', None) in (None, 'None'),
        'endpointAddresses': endpoint_addresses,
        'ports': [
            {
                'name': port.name,
                'protocol': port.protocol,
                'port': port.port,
                'targetPort': port.target_port,
                'nodePort': getattr(port, 'node_port', None),
            }
            for port in (service.spec.ports or [])
        ],
    }, status=status.HTTP_200_OK)
