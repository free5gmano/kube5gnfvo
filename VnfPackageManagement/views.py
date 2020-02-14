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
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
from rest_framework.exceptions import APIException
from VnfPackageManagement.models import VnfPkgInfo
from VnfPackageManagement.serializers import VnfPkgInfoSerializer, vnf_package_base_path
from utils.file_manipulation import decompress_zip, copy_file, remove_file
from utils.format_tools import set_request_parameter_to_string
from utils.process_package.base_package import created, disabled, not_in_use, enabled
from utils.process_package.vnf_package import PackageVNF


class VNFPackagesViewSet(viewsets.ModelViewSet):
    queryset = VnfPkgInfo.objects.all()
    serializer_class = VnfPkgInfoSerializer

    def create(self, request, **kwargs):
        set_request_parameter_to_string(request, 'userDefinedData')

        request.data['_links'] = {'self': request.build_absolute_uri(),
                                  'vnfd': request.build_absolute_uri(),
                                  'packageContent': request.build_absolute_uri()}
        return super().create(request)

    def get_success_headers(self, data):
        return {'Location': data['_links']['self']}

    def list(self, request, *args, **kwargs):
        if self.get_queryset().__len__() < 1:
            raise APIException(detail='One or more individual VNF Package resource have been created')

        return super().list(request)

    def update(self, request, *args, **kwargs):
        if disabled == request.data['operationalState'] or enabled == request.data['operationalState']:
            raise APIException(detail='ValueError: invalid operationalState',
                               code=status.HTTP_409_CONFLICT)

        response = request.data.copy()
        set_request_parameter_to_string(request, 'userDefinedData')

        super().update(request)
        return Response(response, status=status.HTTP_200_OK)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if disabled != instance.operationalState:
            raise APIException(detail='VNF Package operationalState is not {}'.format(disabled),
                               code=status.HTTP_409_CONFLICT)

        if not_in_use != instance.usageState:
            raise APIException(detail='VNF Package usageState is not {}'.format(not_in_use),
                               code=status.HTTP_409_CONFLICT)

        remove_file('{}{}'.format(vnf_package_base_path, instance.id))
        super().destroy(request)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['PUT'], url_path='package_content')
    def upload_content(self, request, **kwargs):
        instance = self.get_object()
        if created != instance.onboardingState:
            raise APIException(detail='VNF Package onboardingState is not {}'.format(created),
                               code=status.HTTP_409_CONFLICT)

        if 'application/zip' not in request.META['HTTP_ACCEPT']:
            raise APIException(detail='HEAD need to have application/zip value')

        vnf_package_path = '{}{}'.format(vnf_package_base_path, instance.id)
        vnf_package_content_path = decompress_zip(
            request.data['file'], vnf_package_path + '/package_content/')
        copy_file(vnf_package_path + "/package_content/", vnf_package_path + "/vnfd/", 'Definitions')
        process_vnf_instance = PackageVNF(path=vnf_package_content_path)
        input_value = process_vnf_instance.processing_data()

        serializer = self.get_serializer(instance, data=input_value)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(status=status.HTTP_202_ACCEPTED)
