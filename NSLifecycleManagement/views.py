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
import threading
from functools import partial
from rest_framework import viewsets
from rest_framework.exceptions import APIException
from NSDManagement.models import NsdInfo
from NSLifecycleManagement.models import NsInstance
from NSLifecycleManagement.serializers import NsInstanceSerializer
from NSLifecycleManagement.utils.monitor_vnf import MonitorVnf
from django.utils import timezone
from NSLCMOperationOccurrences.models import Links, NsLcmOpOcc, ResourceChanges
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import action
from NSLifecycleManagement.utils.process_vnf_model import get_vnf_instance, create_vnf_instance
from utils.etcd_client.etcd_client import EtcdClient
from utils.notification_management.kafka_notification import KafkaNotification
from utils.process_package.base_package import not_instantiated, not_in_use, instantiated, in_use
from utils.process_package.create_vnf import CreateService
from utils.process_package.delete_vnf import DeleteService
from utils.process_package.process_fp_instance import ProcessFPInstance


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
    kafka_notification = KafkaNotification('ns_instance')

    def create(self, request, **kwargs):
        """
            Create a NS instance resource.

            The POST method creates a new NS instance resource.
        """
        if 'nsdId' not in request.data:
            raise APIException(detail='nsdId is not existing',
                               code=status.HTTP_409_CONFLICT)

        if 'nsName' not in request.data:
            raise APIException(detail='nsName is not existing',
                               code=status.HTTP_409_CONFLICT)

        if 'nsDescription' not in request.data:
            raise APIException(detail='nsDescription is not existing',
                               code=status.HTTP_409_CONFLICT)

        ns_descriptors_info = NsdInfo.objects.filter(nsdId=request.data['nsdId']).last()
        if ns_descriptors_info is None:
            raise APIException(detail='nsdId is not existing',
                               code=status.HTTP_409_CONFLICT)

        vnf_pkg_Ids = json.loads(ns_descriptors_info.vnfPkgIds)
        nsd_info_id = str(ns_descriptors_info.id)
        request.data['nsdInfoId'] = nsd_info_id
        request.data['nsInstanceName'] = request.data['nsName']
        request.data['nsInstanceDescription'] = request.data['nsDescription']
        request.data['nsdId'] = request.data['nsdId']
        request.data['vnfInstance'] = get_vnf_instance(vnf_pkg_Ids)
        request.data['_links'] = {'self': request.build_absolute_uri()}

        return super().create(request)

    def get_success_headers(self, data):
        return {'Location': data['_links']['self']}

    def retrieve(self, request, *args, **kwargs):
        """
            Read an individual NS instance resource.

            The GET method retrieves information about a NS instance by reading an individual NS instance resource.
        """
        return super().retrieve(request)

    def update(self, request, *args, **kwargs):
        raise APIException(detail='Method Not Allowed',
                           code=status.HTTP_405_METHOD_NOT_ALLOWED)

    def list(self, request, *args, **kwargs):
        """
            Query multiple NS instances.

            Query NS Instances.\
            The GET method queries information about multiple NS instances. \
            This method shall support the URI query parameters, request and response data structures, \
            and response codes, as specified in the Tables 6.4.2.3.2-1 and 6.4.2.3.2-2.
        """
        return super().list(request)

    def destroy(self, request, *args, **kwargs):
        """
            Delete NS instance resource.

            Delete NS Identifier This method deletes an individual NS instance resource.
        """
        instance = self.get_object()
        if not_instantiated != instance.nsState:
            raise APIException(detail='nsState is not {}'.format(not_instantiated),
                               code=status.HTTP_409_CONFLICT)

        super().destroy(request)
        self.kafka_notification.notify(kwargs['pk'], 'NS Instance({}) had been destroy'.format(kwargs['pk']))
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['POST'], url_path='instantiate')
    def instantiate_ns(self, request, **kwargs):
        """
            Instantiate a NS.

            The POST method requests to instantiate a NS instance resource.
        """
        ns_instance = self.get_object()

        if 'vnfInstanceData' not in request.data:
            raise APIException(detail='vnfInstanceData is not existing',
                               code=status.HTTP_409_CONFLICT)

        vnf_instance_list = list()
        vnf_instance_data = request.data.pop('vnfInstanceData')

        for vnf_instance_info in vnf_instance_data:
            if 'vnfInstanceId' not in vnf_instance_info:
                raise APIException(detail='vnfInstanceId is not existing',
                                   code=status.HTTP_409_CONFLICT)

            vnf_instance = ns_instance.NsInstance_VnfInstance.get(id=vnf_instance_info['vnfInstanceId'])
            if vnf_instance is None:
                raise APIException(detail='vnf_instance is not existing',
                                   code=status.HTTP_409_CONFLICT)

            vnf_instance.VnfInstance_instantiatedVnfInfo.vnfState = 'STARTED'
            vnf_instance.VnfInstance_instantiatedVnfInfo.save()
            create_network_service = \
                CreateService(vnf_instance.vnfPkgId, vnf_instance.vnfInstanceName)
            # threading.Thread(
            #     target=partial(create_network_service.process_instance),
            #     daemon=True
            # ).start()

            vnf_instance_list.append(vnf_instance)

        set_ns_lcm_op_occ(ns_instance, request, vnf_instance_list, self.monitor_vnf.instantiate)
        self.monitor_vnf.monitoring_vnf(kwargs['pk'], self.monitor_vnf.instantiate,
                                        vnf_instances=vnf_instance_list,
                                        container_phase='Running',
                                        ns_state=instantiated,
                                        usage_state=in_use)

        ns_instance.nsState = instantiated
        ns_instance.save()

        return Response(status=status.HTTP_202_ACCEPTED, headers={'Location': ns_instance.NsInstance_links.link_self})

    @action(detail=True, methods=['POST'], url_path='scale')
    def scale_ns(self, request, **kwargs):
        """
            Scale a NS instance.

            The POST method requests to instantiate a NS instance resource.
        """
        ns_instance = self.get_object()
        if 'INSTANTIATED' != ns_instance.nsState:
            raise APIException(detail='Network Service instance State have been INSTANTIATE')

        if 'scaleType' not in request.data:
            raise APIException(detail='scaleType parameter is necessary')

        vnf_instance_list = list()
        if 'SCALE_VNF' == request.data['scaleType']:
            for scale_vnf_data in request.data['scaleVnfData']:
                vnf_instance = ns_instance.NsInstance_VnfInstance.get(id=scale_vnf_data['vnfInstanceId'])
                if 'SCALE_OUT' == scale_vnf_data['scaleVnfType']:
                    if 'additionalParams' in scale_vnf_data['scaleByStepData']:
                        additional_params = scale_vnf_data['scaleByStepData']['additionalParams']
                        replicas = int(additional_params['replicas']) if 'replicas' in additional_params else None
                        virtual_mem_size = additional_params[
                            'virtual_mem_size'] if 'virtual_mem_size' in additional_params else None
                        num_virtual_cpu = additional_params[
                            'num_virtual_cpu'] if 'num_virtual_cpu' in additional_params else None
                        create_network_service = CreateService(vnf_instance.vnfPkgId, vnf_instance.vnfInstanceName)
                        create_network_service.process_instance(
                            replicas=replicas, virtual_mem_size=virtual_mem_size, num_virtual_cpu=num_virtual_cpu)
                        vnf_instance_list.append(vnf_instance)
            set_ns_lcm_op_occ(ns_instance, request, vnf_instance_list, 'SCALE')
            self.monitor_vnf.monitoring_vnf(kwargs['pk'], self.monitor_vnf.scale,
                                            vnf_instances=vnf_instance_list,
                                            container_phase='Running',
                                            ns_state=instantiated,
                                            usage_state=in_use)
            return Response(status=status.HTTP_202_ACCEPTED,
                            headers={'Location': ns_instance.NsInstance_links.link_self})

    # TODO
    @action(detail=True, methods=['POST'], url_path='heal')
    def heal_ns(self, request, **kwargs):
        """
            Heal a NS instance.

            The POST method requests to heal a NS instance resource. \
            This method shall follow the provisions specified in the Tables 6.4.7.3.1-1 and 6.4.7.3.1-2 \
            for URI query parameters, request and response data structures, and response codes.
        """
        ns_instance = self.get_object()
        if 'INSTANTIATED' != ns_instance.nsState:
            raise APIException(detail='Network Service instance State have been INSTANTIATE')

        return Response(status=status.HTTP_202_ACCEPTED,
                        headers={'Location': ns_instance.NsInstance_links.link_self})

    @action(detail=True, methods=['POST'], url_path='update')
    def update_ns(self, request, **kwargs):
        """
            Updates a NS instance.

            Scale NS instance. The POST method requests to scale a NS instance resource.
        """
        ns_instance = self.get_object()
        if 'INSTANTIATED' != ns_instance.nsState:
            raise APIException(detail='Network Service instance State have been INSTANTIATE')

        if 'updateType' not in request.data:
            raise APIException(detail='updateType parameter is necessary')

        vnf_instance_list = list()
        if request.data['updateType'] == 'ADD_VNF':
            if 'addVnfInstance' not in request.data and isinstance(request.data['addVnfInstance'], list):
                raise APIException(detail='Not found removeVnfInstanceId parameter')

            add_vnf_instance = request.data['addVnfInstance']
            for vnf_instance_request in add_vnf_instance:
                if 'vnfInstanceId' not in vnf_instance_request:
                    raise APIException(detail='Error parameter vnfInstanceId')

                # vnfInstanceId (nm -> vnfpkgid)
                vnf_info = get_vnf_instance([vnf_instance_request['vnfInstanceId']]).pop(0)
                vnf_instance = create_vnf_instance(vnf_info)
                ns_instance.NsInstance_VnfInstance.add(vnf_instance)
                create_network_service = CreateService(vnf_instance.vnfPkgId, vnf_instance.vnfInstanceName)
                create_network_service.process_instance()
                vnf_instance_list.append(vnf_instance)
        elif request.data['updateType'] == 'REMOVE_VNF':
            if 'removeVnfInstanceId' not in request.data:
                raise APIException(detail='Not found removeVnfInstanceId parameter')
            vnf_instance = ns_instance.NsInstance_VnfInstance.get(id=request.data['removeVnfInstanceId'])
            vnf_instance.delete()
            delete_network_service = DeleteService(vnf_instance.vnfPkgId, vnf_instance.vnfInstanceName)
            delete_network_service.process_instance()
            vnf_instance_list.append(vnf_instance)

        set_ns_lcm_op_occ(ns_instance, request, vnf_instance_list, self.monitor_vnf.update)
        self.monitor_vnf.monitoring_vnf(kwargs['pk'], self.monitor_vnf.update,
                                        vnf_instances=vnf_instance_list,
                                        container_phase='Running',
                                        ns_state=instantiated,
                                        usage_state=in_use)
        return Response(status=status.HTTP_202_ACCEPTED, headers={'Location': ns_instance.NsInstance_links.link_self})

    @action(detail=True, methods=['POST'], url_path='terminate')
    def terminate_ns(self, request, **kwargs):
        """
            Terminate a NS instance.

            Terminate NS task. The POST method terminates a NS instance. \
            This method can only be used with a NS instance in the INSTANTIATED state. \
            Terminating a NS instance does not delete the NS instance identifier, \
            but rather transitions the NS into the NOT_INSTANTIATED state. \
            This method shall support the URI query parameters, request and response data structures, \
            and response codes, as specified in the Tables 6.4.8.3.1-1 and 6.8.8.3.1-2.
        """
        ns_instance = self.get_object()
        if 'INSTANTIATED' != ns_instance.nsState:
            raise APIException(detail='Network Service instance State have been INSTANTIATE',
                               code=status.HTTP_409_CONFLICT)

        vnf_instance_list = list()

        for vnf_instance in ns_instance.NsInstance_VnfInstance.all():
            vnf_instance.VnfInstance_instantiatedVnfInfo.vnfState = 'STOPPED'
            vnf_instance.VnfInstance_instantiatedVnfInfo.save()
            delete_network_service = DeleteService(vnf_instance.vnfPkgId, vnf_instance.vnfInstanceName)
            threading.Thread(
                target=partial(delete_network_service.process_instance),
                daemon=True
            ).start()
            self.etcd_client.set_deploy_name(instance_name=vnf_instance.vnfInstanceName.lower(), pod_name=None)
            self.etcd_client.release_pod_ip_address()
            vnf_instance_list.append(vnf_instance)

        set_ns_lcm_op_occ(ns_instance, request, vnf_instance_list, self.monitor_vnf.terminate)
        self.monitor_vnf.monitoring_vnf(kwargs['pk'], self.monitor_vnf.terminate,
                                        vnf_instances=vnf_instance_list,
                                        container_phase='Terminating',
                                        ns_state=not_instantiated,
                                        usage_state=not_in_use)

        ns_instance.nsState = not_instantiated
        ns_instance.save()

        return Response(status=status.HTTP_202_ACCEPTED, headers={'Location': ns_instance.NsInstance_links.link_self})
