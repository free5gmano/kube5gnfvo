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

from rest_framework import viewsets
from rest_framework.exceptions import APIException
from NSDManagement.serializers import *
from rest_framework.response import Response
from rest_framework import status
from rest_framework.utils import json
from rest_framework.decorators import action
from VnfPackageManagement.models import VnfPkgInfo
from utils.file_manipulation import remove_file, decompress_zip
from utils.format_tools import set_request_parameter_to_string
from utils.process_package.base_package import on_boarded, disabled, enabled, not_in_use, created
from utils.process_package.ns_descriptor import NetworkServiceDescriptor


class NSDescriptorsViewSet(viewsets.ModelViewSet):
    queryset = NsdInfo.objects.all()
    serializer_class = NsdInfoSerializer

    def create(self, request, *args, **kwargs):
        set_request_parameter_to_string(request, 'userDefinedData')
        request.data['_links'] = {'self': request.build_absolute_uri(),
                                  'nsd_content': request.build_absolute_uri()}
        return super().create(request)

    def get_success_headers(self, data):
        return {'Location': data['_links']['self']}

    def list(self, request, *args, **kwargs):
        if self.get_queryset().__len__() < 1:
            raise APIException(detail='One or more individual NS descriptor resource have been created')

        return super().list(request)

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        if on_boarded != instance.nsdOnboardingState:
            raise APIException(detail='NSD nsdOnboardingState is not {}'.format(on_boarded))

        if disabled == request.data['nsdOperationalState'] or enabled == request.data['nsdOperationalState']:
            raise APIException(detail='ValueError: invalid operationalState',
                               code=status.HTTP_409_CONFLICT)

        response = request.data.copy()
        set_request_parameter_to_string(request, 'userDefinedData')

        super().update(request)
        return Response(response, status=status.HTTP_200_OK)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if disabled != instance.nsdOperationalState:
            raise APIException(detail='NSD nsdOperationalState is not {}'.format(disabled),
                               code=status.HTTP_409_CONFLICT)

        if not_in_use != instance.nsdUsageState:
            raise APIException(detail='NSD nsdUsageState is not {}'.format(not_in_use),
                               code=status.HTTP_409_CONFLICT)

        remove_file('{}{}'.format(nsd_base_path, instance.id))
        super().destroy(request)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['PUT'], url_path='nsd_content')
    def upload_content(self, request, **kwargs):
        instance = self.get_object()
        if created != instance.nsdOnboardingState:
            raise APIException(detail='NSD nsdOnboardingState is not {}'.format(created),
                               code=status.HTTP_409_CONFLICT)

        if 'application/zip' not in request.META['HTTP_ACCEPT']:
            raise APIException(detail='HEAD need to have application/zip value')

        network_service_path = decompress_zip(
            request.data["file"], '{}{}'.format(nsd_base_path, instance.id) + "/nsd_content/")
        process_network_service = NetworkServiceDescriptor(path=network_service_path)
        nsd_content = process_network_service.processing_data()
        vnf_descriptor_list = nsd_content[1]
        vnfPkgIds_list = list()
        for vnfd in vnf_descriptor_list:
            vnfPkgIds_list.append(str(VnfPkgInfo.objects.filter(vnfProductName__iexact=vnfd).last().id))
        nsd_content[0]['vnfPkgIds'] = json.dumps(vnfPkgIds_list)

        serializer = self.get_serializer(instance, data=nsd_content[0])
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(status=status.HTTP_204_NO_CONTENT)
