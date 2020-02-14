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
from rest_framework import viewsets
from rest_framework.exceptions import APIException
from django.utils import timezone
from NSDManagement.models import NsdInfo
from NSLCMOperationOccurrences.models import NsLcmOpOcc, Links, ResourceChanges
from NSLifecycleManagement.models import NsInstance
from NSLifecycleManagement.serializers import NsInstanceSerializer
from NSLifecycleManagement.utils.monitor_vnf import MonitorVnf
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
from utils.process_package.process_fp_instance import ProcessFPInstance
from utils.process_package.process_vnf_instance import ProcessVNFInstance

monitor_deployment = MonitorDeployment()
# Run kubernetes Utils
monitor_deployment.run_watch_event()


def get_vnffg(nsd_id) -> list:
    vnffg_list = list()
    process_vnffg = ProcessFPInstance(nsd_id)
    instance_info = process_vnffg.instance_info
    if instance_info:
        for vnffg in instance_info:
            vnffg_info = dict()
            vnffg_info['vnffgdId'] = vnffg['vnffgdId']
            vnffg_info['vnfInstanceId'] = json.dumps(vnffg['constituent_vnfd'])
            vnffg_info['nsCpHandle'] = list()
            for cp in vnffg['connection_point']:
                ns_cp_handle = dict()
                ns_cp_handle['vnfExtCpInstanceId'] = cp
                vnffg_info['nsCpHandle'].append(ns_cp_handle)
            vnffg_list.append(vnffg_info)
    return vnffg_list


def get_vnf_Instance(vnf_pkg_ids) -> list:
    vnf_instances = list()
    for vnf_pkg_id in vnf_pkg_ids:
        vnf_package_info = VnfPkgInfo.objects.filter(id=vnf_pkg_id).last()
        vnfdId = vnf_package_info.vnfdId.lower()
        vnfInstanceName = '{}-{}'.format(vnfdId, randomString())
        process_vnf_instance = ProcessVNFInstance(vnf_pkg_id)
        vnf_info = process_vnf_instance.instance_info
        ext_cp_info = list()
        for vnf in vnf_info:
            cp_info = dict()
            cp_info['cpProtocolInfo'] = list()
            cpProtocolInfo = dict()
            for cp in vnf['cp']:
                cp_info['cpdId'] = cp.name
                cpProtocolInfo['layerProtocol'] = cp.properties['layer_protocol']
                cp_info['cpProtocolInfo'].append(cpProtocolInfo)
            ext_cp_info.append(cp_info)

        vnf_instances.append({'vnfdId': vnf_package_info.vnfdId,
                              'vnfInstanceName': vnfInstanceName,
                              'vnfProvider': vnf_package_info.vnfProvider,
                              'vnfProductName': vnf_package_info.vnfProductName,
                              'vnfSoftwareVersion': vnf_package_info.vnfSoftwareVersion,
                              'vnfdVersion': vnf_package_info.vnfdVersion,
                              'vnfPkgId': vnf_pkg_id,
                              'metadata': vnf_package_info.userDefinedData,
                              'instantiatedVnfInfo': {'vnfState': 'STARTED',
                                                      'extCpInfo': ext_cp_info}})

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


class NSLifecycleManagementViewSet(viewsets.ModelViewSet):
    queryset = NsInstance.objects.all()
    serializer_class = NsInstanceSerializer
    monitor_vnf = MonitorVnf()
    etcd_client = EtcdClient()

    def create(self, request, **kwargs):
        ns_descriptors_info = NsdInfo.objects.filter(nsdId=request.data['nsdId']).last()
        vnf_pkg_Ids = json.loads(ns_descriptors_info.vnfPkgIds)
        nsd_info_id = str(ns_descriptors_info.id)
        request.data['nsdInfoId'] = nsd_info_id
        request.data['nsInstanceName'] = request.data['nsName']
        request.data['nsInstanceDescription'] = request.data['nsDescription']
        request.data['nsdId'] = request.data['nsdId']
        request.data['vnfInstance'] = get_vnf_Instance(vnf_pkg_Ids)
        request.data['_links'] = {'self': request.build_absolute_uri()}
        request.data['vnffgInfo'] = get_vnffg(nsd_info_id)

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

        vnf_instance_list = list()
        vnf_instance_data = request.data.pop('vnfInstanceData')
        process_vnffg = None
        if ns_instance.NsInstance_VnffgInfo.last() is not None:
            process_vnffg = ProcessFPInstance(str(ns_instance.nsdInfoId))

        for vnf_instance_info in vnf_instance_data:
            vnf_instance = ns_instance \
                .NsInstance_VnfInstance.filter(id=vnf_instance_info['vnfInstanceId']).last()
            create_network_service = \
                CreateService(vnf_instance.vnfPkgId, vnf_instance.vnfInstanceName)
            create_network_service.process()

            vnf_instance_list.append(vnf_instance)
            if process_vnffg:
                process_vnffg.mapping_rsp(vnf_instance.vnfdId, vnf_instance.vnfInstanceName)

        set_ns_lcm_op_occ(ns_instance, request, vnf_instance_list, self.monitor_vnf.instantiate)
        self.monitor_vnf.monitoring_vnf(kwargs['pk'], self.monitor_vnf.instantiate,
                                        vnf_instances=vnf_instance_list,
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

        vnf_instance_list = list()
        process_vnffg = None
        if ns_instance.NsInstance_VnffgInfo.last() is not None:
            process_vnffg = ProcessFPInstance(str(ns_instance.nsdInfoId))

        for vnf_instance in ns_instance.NsInstance_VnfInstance.all():
            delete_network_service = \
                DeleteService(vnf_instance.vnfPkgId, vnf_instance.vnfInstanceName)
            delete_network_service.process()
            self.etcd_client.set_deploy_name(instance_name=vnf_instance.vnfInstanceName.lower(), pod_name=None)
            self.etcd_client.release_pod_ip_address()
            vnf_instance_list.append(vnf_instance)
            if process_vnffg:
                process_vnffg.mapping_rsp(vnf_instance.vnfdId, vnf_instance.vnfInstanceName)

        set_ns_lcm_op_occ(ns_instance, request, vnf_instance_list, self.monitor_vnf.terminate)
        self.monitor_vnf.monitoring_vnf(kwargs['pk'], self.monitor_vnf.terminate,
                                        vnf_instances=vnf_instance_list,
                                        container_phase='Terminating',
                                        ns_state=not_instantiated,
                                        usage_state=not_in_use)
        if process_vnffg:
            process_vnffg.remove_vnffg()
        return Response(status=status.HTTP_202_ACCEPTED, headers={'Location': ns_instance.NsInstance_links.link_self})
