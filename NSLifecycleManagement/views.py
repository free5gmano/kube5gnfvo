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

import json
from functools import partial
from rest_framework import viewsets
from rest_framework.exceptions import APIException
from django.utils import timezone
from NSDManagement.models import NsdInfo
from NSLCMOperationOccurrences.models import NsLcmOpOcc, Links, ResourceChanges
from NSLifecycleManagement.models import NsInstance
from NSLifecycleManagement.serializers import NsInstanceSerializer
from VIMManagement.utils.monitor_deployment import MonitorDeployment
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import action
from VnfPackageManagement.models import VnfPkgInfo
from utils.etcd_client.etcd_client import EtcdClient
from utils.format_tools import randomString
from utils.process_package.base_package import not_instantiated, instantiated, in_use, not_in_use
from utils.process_package.create_vnf import CreateService
from utils.process_package.delete_vnf import DeleteService
from utils.process_package.process_vnf_instance import ProcessVNFInstance

monitor_deployment = MonitorDeployment()
# Run kubernetes Utils
monitor_deployment.run_watch_event()


def monitoring_vnf(ns_instance_id, lcm_operation_type, ns_state, usage_state, **kwargs):
    events = [partial(set_state, ns_id=ns_instance_id, lcm_operation_type=lcm_operation_type,
                      ns_state=ns_state, usage_state=usage_state)]
    container_list = list()
    for vnf_instances_container in kwargs['vnf_instances_container']:
        container_list.append(vnf_instances_container.vnfInstanceName.lower())

    monitor_deployment.watch_specific_deployment(container_list, kwargs['container_phase'], events)


def get_vnf_Instance(vnf_pkg_ids) -> list:
    vnf_instances = list()
    for vnf_pkg_id in vnf_pkg_ids:
        vnf_package_info = VnfPkgInfo.objects.filter(id=vnf_pkg_id).last()
        vnf_package = ProcessVNFInstance(vnf_package_info.id)
        vnf_package.process_definitions()
        for vdu_info in vnf_package.vdu:
            vnfProductName = vnf_package_info.vnfProductName.lower()
            vnfInstanceName = '{}-{}-{}'.format(vnfProductName,
                                                vdu_info.node_name.lower(),
                                                randomString(10))
            vnf_instances.append({'vnfdId': vnf_package_info.vnfdId,
                                  'vnfInstanceName': vnfInstanceName,
                                  'vnfProvider': vnf_package_info.vnfProvider,
                                  'vnfProductName': vnfProductName,
                                  'vnfSoftwareVersion': vnf_package_info.vnfSoftwareVersion,
                                  'vnfdVersion': vnf_package_info.vnfdVersion,
                                  'vnfPkgId': vnf_pkg_id,
                                  'metadata': vnf_package_info.userDefinedData,
                                  'instantiatedVnfInfo': {'vnfState': 'STARTED'}})

    return vnf_instances


def set_ns_lcm_op_occ(ns_instance, request, vnf_instances, lcm_operation_type):
    ns_lcm_op_occ = NsLcmOpOcc.objects.filter(nsInstanceId=ns_instance.id, lcmOperationType=lcm_operation_type).last()
    if ns_lcm_op_occ:
        ns_lcm_op_occ.operationState = 'PROCESSING'
        ns_lcm_op_occ.save()
    else:
        ns_lcm_op_occ = NsLcmOpOcc.objects.create(
            **{'nsInstanceId': ns_instance.id,
               'statusEnteredTime': timezone.now(),
               'lcmOperationType': lcm_operation_type,
               'isAutomaticInvocation': False,
               'isCancelPending': False,
               'operationParams': json.dumps(request.data)})
        resource_changes = ResourceChanges.objects.create(resourceChanges=ns_lcm_op_occ)
        for vnf in vnf_instances:
            resource_changes.affectedVnfs.create(vnfInstanceId=str(vnf.id),
                                                 vnfdId=vnf.vnfdId,
                                                 vnfProfileId=vnf.vnfPkgId,
                                                 vnfName=vnf.vnfInstanceName,
                                                 changeType='INSTANTIATE',
                                                 changeResult='COMPLETED')
        Links.objects.create(
            _links=ns_lcm_op_occ,
            **{'link_self': 'http://{}/nslcm/v1/ns_lcm_op_occs/{}'.format(request.get_host(), ns_lcm_op_occ.id),
               'nsInstance': ns_instance.NsInstance_links.link_self})


def set_state(ns_id, lcm_operation_type, ns_state, usage_state):
    ns_instance = NsInstance.objects.filter(id=ns_id).last()
    for vnf_instance in ns_instance.NsInstance_VnfInstance.all():
        vnf_package_info = VnfPkgInfo.objects.filter(id=vnf_instance.vnfPkgId).last()
        vnf_package_info.usageState = usage_state
        vnf_package_info.save()

    nsd_info = NsdInfo.objects.filter(id=ns_instance.nsdInfoId).last()
    nsd_info.nsdUsageState = usage_state
    nsd_info.save()

    ns_instance.nsState = ns_state
    ns_instance.save()

    ns_lcm_op_occ = NsLcmOpOcc.objects.filter(nsInstanceId=ns_id, lcmOperationType=lcm_operation_type).last()
    ns_lcm_op_occ.operationState = 'COMPLETED'
    ns_lcm_op_occ.save()


class NSLifecycleManagementViewSet(viewsets.ModelViewSet):
    queryset = NsInstance.objects.all()
    serializer_class = NsInstanceSerializer

    def create(self, request, **kwargs):
        ns_descriptors_info = NsdInfo.objects.filter(nsdId=request.data['nsdId']).last()
        vnf_pkg_Ids = json.loads(ns_descriptors_info.vnfPkgIds)
        request.data['nsdInfoId'] = str(ns_descriptors_info.id)
        request.data['nsInstanceName'] = request.data['nsName']
        request.data['nsInstanceDescription'] = request.data['nsDescription']
        request.data['nsdId'] = request.data['nsdId']
        request.data['vnfInstance'] = get_vnf_Instance(vnf_pkg_Ids)
        request.data['_links'] = {'self': request.build_absolute_uri()}
        return super().create(request)

    def get_success_headers(self, data):
        return {'Location': data['_links']['self']}

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if not_instantiated != instance.nsState:
            raise APIException(detail='nsState is not {}'.format(not_instantiated),
                               code=status.HTTP_409_CONFLICT)

        super().destroy(request)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['POST'], url_path='instantiate')
    def instantiate_ns(self, request, **kwargs):
        ns_instance = self.get_object()
        if not_instantiated != ns_instance.nsState:
            raise APIException(detail='Network Service Instance State have been {}'.format(not_instantiated),
                               code=status.HTTP_409_CONFLICT)

        vnf_instance_container = list()
        vnf_instance_data = request.data.pop('vnfInstanceData')
        for vnf_instance_info in vnf_instance_data:
            vnf_instance = ns_instance \
                .NsInstance_VnfInstance.filter(id=vnf_instance_info['vnfInstanceId']).last()
            vnf_instance_name = vnf_instance.vnfInstanceName.lower()
            create_network_service = \
                CreateService(vnf_instance.vnfPkgId, vnf_instance_name)
            create_network_service.process_definitions()
            create_network_service.process_deploy(etcd_client=EtcdClient(instance_name=vnf_instance_name))
            vnf_instance_container.append(vnf_instance)

        set_ns_lcm_op_occ(ns_instance, request, vnf_instance_container, 'INSTANTIATE')
        monitoring_vnf(kwargs['pk'], 'INSTANTIATE',
                       vnf_instances_container=vnf_instance_container,
                       container_phase='Running',
                       ns_state=instantiated,
                       usage_state=in_use)

        return Response(status=status.HTTP_202_ACCEPTED, headers={'Location': ns_instance.NsInstance_links.link_self})

    @action(detail=True, methods=['POST'], url_path='terminate')
    def terminate_ns(self, request, **kwargs):
        ns_instance = self.get_object()
        if instantiated != ns_instance.nsState:
            raise APIException(detail='Network Service instance State have been {}'.format(instantiated),
                               code=status.HTTP_409_CONFLICT)

        vnf_instance_container = list()
        for vnf_instance in ns_instance.NsInstance_VnfInstance.all():
            vnf_instance_name = vnf_instance.vnfInstanceName.lower()
            delete_network_service = \
                DeleteService(vnf_instance.vnfPkgId, vnf_instance_name)
            delete_network_service.process_definitions()
            delete_network_service.process_delete()
            etcd_client = EtcdClient(instance_name=vnf_instance_name)
            etcd_client.release_pod_ip_address()
            vnf_instance_container.append(vnf_instance)

        set_ns_lcm_op_occ(ns_instance, request, vnf_instance_container, 'TERMINATE')
        monitoring_vnf(kwargs['pk'], 'TERMINATE',
                       vnf_instances_container=vnf_instance_container,
                       container_phase='Terminating',
                       ns_state=not_instantiated,
                       usage_state=not_in_use)
        return Response(status=status.HTTP_202_ACCEPTED, headers={'Location': ns_instance.NsInstance_links.link_self})
