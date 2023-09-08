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

from drf_yasg.utils import swagger_auto_schema
from rest_framework import viewsets
from rest_framework.exceptions import APIException
from rest_framework.utils import json

from NSDManagement.serializers import *
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import action
from django.http import HttpResponse
from VnfPackageManagement.models import *
from utils.file_manipulation import remove_file, decompress_zip, compression_dir_zip
from utils.format_tools import set_request_parameter_to_string
from utils.notification_management.kafka_notification import KafkaNotification
from utils.process_package.base_package import on_boarded, disabled, not_in_use, created, enabled
from utils.process_package.ns_descriptor import NetworkServiceDescriptor


class NSDescriptorsViewSet(viewsets.ModelViewSet):
    queryset = NsdInfo.objects.all()
    serializer_class = NsdInfoSerializer
    kafka_notification = KafkaNotification('ns_descriptor')

    def create(self, request, *args, **kwargs):
        """
            Create a new NS descriptor resource.

            The POST method is used to create a new NS descriptor resource.
        """
        set_request_parameter_to_string(request, 'userDefinedData')
        request.data['_links'] = {'self': request.build_absolute_uri(),
                                  'nsd_content': request.build_absolute_uri()}
        return super().create(request)

    def get_success_headers(self, data):
        return {'Location': data['_links']['self']}

    def list(self, request, *args, **kwargs):
        """
            Query information about multiple NS descriptor resources.

            The GET method queries information about multiple NS descriptor resources.
        """
        if self.get_queryset().__len__() < 1:
            raise APIException(detail='One or more individual NS descriptor resource have been created')

        return super().list(request)

    def retrieve(self, request, *args, **kwargs):
        """
            Read information about an individual NS descriptor resource.

            The GET method reads information about an individual NS descriptor.
        """
        return super().retrieve(request)

    def update(self, request, *args, **kwargs):
        """
            Modify the operational state and/or the user defined data of an individual NS descriptor resource.

            The PATCH method modifies the operational state and/or user defined data \
            of an individual NS descriptor resource. \
            This method can be used to: 1) Enable a previously disabled individual NS descriptor resource, \
            allowing again its use for instantiation of new network service with this descriptor. \
            The usage state (i.e. “IN_USE/NOT_IN_USE”) shall not change as a result. 2) \
            Disable a previously enabled individual NS descriptor resource, \
            preventing any further use for instantiation of new network service(s) with this descriptor. \
            The usage state (i.e. “IN_USE/NOT_IN_USE”) shall not change as a result. 3)\
            Modify the user defined data of an individual NS descriptor resource.
        """
        instance = self.get_object()
        if on_boarded != instance.nsdOnboardingState:
            raise APIException(detail='NSD nsdOnboardingState is not {}'.format(on_boarded))

        if disabled != request.data['nsdOperationalState'] and enabled != request.data['nsdOperationalState']:
            raise APIException(detail='ValueError: invalid operationalState',
                               code=status.HTTP_409_CONFLICT)

        response = request.data.copy()
        set_request_parameter_to_string(request, 'userDefinedData')

        super().update(request)
        self.kafka_notification.notify(kwargs['pk'], 'NSD({}) had been update'.format(kwargs['pk']))
        return Response(response, status=status.HTTP_200_OK)

    def destroy(self, request, *args, **kwargs):
        """
            Delete an individual NS descriptor resource.

            The DELETE method deletes an individual NS descriptor resource. \
            An individual NS descriptor resource can only be deleted when there is no NS instance using it \
            (i.e. usageState = NOT_IN_USE) and has been disabled already (i.e. operationalState = DISABLED). \
            Otherwise, the DELETE method shall fail.
        """
        instance = self.get_object()
        if disabled != instance.nsdOperationalState:
            raise APIException(detail='NSD nsdOperationalState is not {}'.format(disabled),
                               code=status.HTTP_409_CONFLICT)

        if not_in_use != instance.nsdUsageState:
            raise APIException(detail='NSD nsdUsageState is not {}'.format(not_in_use),
                               code=status.HTTP_409_CONFLICT)

        remove_file('{}{}'.format(nsd_base_path, instance.id))
        super().destroy(request)
        self.kafka_notification.notify(kwargs['pk'], 'NSD({}) had been delete'.format(kwargs['pk']))
        return Response(status=status.HTTP_204_NO_CONTENT)

    @swagger_auto_schema(method='PUT',
                         operation_summary="""Upload the content of a NSD.""",
                         operation_description="""The PUT method is used to upload the content of a NSD. \
                         The NSD to be uploaded can be implemented as a single file or as a collection of multiple files,\
                         as defined in clause 5.4.4.3.2. If the NSD is implemented in the form of multiple files, \
                         a ZIP file embedding these files shall be uploaded. If the NSD is implemented as a single file,\
                         either that file or a ZIP file embedding that file shall be uploaded. \
                         ETSI 47 ETSI GS NFV-SOL 005 V2.6.1 (2019-04) \
                         The “Content-Type” HTTP header in the PUT request shall be set accordingly based on the format selection of the NSD: \
                         • If the NSD to be uploaded is a text file, the “Content-Type” header is set to "text/plain".\
                         • If the NSD to be uploaded is a zip file, the “Content-Type” header is set to "application/zip".""")
    @swagger_auto_schema(method='GET',
                         operation_summary="""Fetch the content of a NSD.""",
                         operation_description="""The GET method fetches the content of the NSD. \
                         The NSD can be implemented as a single file or as a collection of multiple files. \
                         If the NSD is implemented in the form of multiple files,\
                         a ZIP file embedding these files shall be returned. \
                         If the NSD is implemented as a single file, \
                         either that file or a ZIP file embedding that file shall be returned. \
                         The selection of the format is controlled by the “Accept” HTTP header passed in the GET request:\
                         • If the “Accept” header contains only “text/plain” and the NSD is implemented as a single file,\
                         the file shall be returned; otherwise, an error message shall be returned.\
                         • If the “Accept” header contains only "application/zip", \
                         the single file or the multiple files that make up the NSD shall be returned embedded in a ZIP file. \
                         • If the “Accept” header contains both “text/plain” and "application/zip", \
                         it is up to the NFVO to choose the format to return for a single-file NSD; \
                         for a multi-file NSD, a ZIP file shall be returned.""")
    @action(detail=True, methods=['PUT', 'GET'], url_path='nsd_content')
    def upload_content(self, request, **kwargs):
        instance = self.get_object()
        if request.method == 'PUT':
            if created != instance.nsdOnboardingState:
                raise APIException(detail='NSD nsdOnboardingState is not {}'.format(created),
                                   code=status.HTTP_409_CONFLICT)

            if 'application/zip' not in request.META['HTTP_ACCEPT']:
                raise APIException(detail='HEAD need to have application/zip value')

            network_service_path = decompress_zip(
                request.data["file"], '{}{}'.format(nsd_base_path, instance.id) + '/nsd_content/')
            network_service_descriptor = NetworkServiceDescriptor(path=network_service_path)
            nsd_content = network_service_descriptor.processing_data()
            vnf_pkg_ids_list = list()
            for vnfd in network_service_descriptor.get_constituent_vnfd():
                vnf_pkg_ids_list.append(str(VnfPkgInfo.objects.filter(vnfdId__iexact=vnfd['vnfd_id']).last().id))

            nsd_content['vnfPkgIds'] = json.dumps(vnf_pkg_ids_list)
            serializer = self.get_serializer(instance, data=nsd_content)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            self.kafka_notification.notify(kwargs['pk'], 'NSD({}) had been upload'.format(kwargs['pk']))
            return Response(status=status.HTTP_202_ACCEPTED)
        elif request.method == 'GET':
            if on_boarded != instance.nsdOnboardingState:
                raise APIException(detail='NSD nsdOnboardingState is not {}'.format(on_boarded),
                                   code=status.HTTP_409_CONFLICT)

            if 'application/zip' not in request.META['HTTP_ACCEPT']:
                raise APIException(detail='HEAD need to have application/zip value')

            compression_result = compression_dir_zip(
                'packageContent', '{}{}'.format(nsd_base_path, instance.id) + '/nsd_content/')
            response = HttpResponse(compression_result[0].getvalue(),
                                    content_type="application/x-zip-compressed",
                                    status=status.HTTP_200_OK)
            response['Content-Disposition'] = 'attachment; filename=%s' % compression_result[1]
            return response
