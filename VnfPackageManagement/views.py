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
import io
import os

from drf_yasg.utils import swagger_auto_schema
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
from django.http import HttpResponse
from django.utils.encoding import smart_str

from VnfPackageManagement.models import VnfPkgInfo
from VnfPackageManagement.serializers import VnfPkgInfoSerializer, vnf_package_base_path
from utils.base_request import BaseRequest
from utils.file_manipulation import remove_file, decompress_zip, copy_file, compression_dir_zip
from utils.format_tools import set_request_parameter_to_string
from rest_framework.exceptions import APIException

from utils.notification_management.kafka_notification import KafkaNotification
from utils.process_package.base_package import disabled, enabled, not_in_use, created, on_boarded
from utils.process_package.vnf_package import PackageVNF


class VNFPackagesViewSet(viewsets.ModelViewSet):
    queryset = VnfPkgInfo.objects.all()
    serializer_class = VnfPkgInfoSerializer
    kafka_notification = KafkaNotification('vnf_pkg')

    def create(self, request, **kwargs):
        """
            Create a new individual VNF package resource.

            The POST method creates a new individual VNF package resource.
        """
        print('aaa')
        set_request_parameter_to_string(request, 'userDefinedData')
        request.data['_links'] = {'self': request.build_absolute_uri(),
                                  'vnfd': request.build_absolute_uri(),
                                  'packageContent': request.build_absolute_uri()}
        return super().create(request)

    def get_success_headers(self, data):
        return {'Location': data['_links']['self']}

    def list(self, request, *args, **kwargs):
        """
            Query VNF packages information.

            The GET method queries the information of the VNF packages matching the filter. This method shall follow \
            the provisions specified in the Tables 9.4.2.3.2-1 and 9.4.2.3.2-2 for URI query parameters, request and \
            response data structures, and response codes.
        """
        if self.get_queryset().__len__() < 1:
            raise APIException(detail='One or more individual VNF Package resource have been created',
                               code=status.HTTP_409_CONFLICT)

        return super().list(request)

    def retrieve(self, request, *args, **kwargs):
        """
            Read information about an individual VNF package.

            The GET method reads the information of a VNF package.
        """
        return super().retrieve(request)

    def update(self, request, *args, **kwargs):
        """
            Update information about an individual VNF package.

            The PATCH method updates the information of a VNF package.
            This method shall follow the provisions specified in the Tables 9.4.3.3.4-1 and \
            9.4.3.3.4-2 for URI query parameters, request and response data structures, \
            and response codes.
        """
        if disabled != request.data['operationalState'] and enabled != request.data['operationalState']:
            raise APIException(detail='ValueError: invalid operationalState',
                               code=status.HTTP_409_CONFLICT)

        response = request.data.copy()
        set_request_parameter_to_string(request, 'userDefinedData')

        super().update(request)
        self.kafka_notification.notify(kwargs['pk'], 'VNFPackage({}) had been updated'.format(kwargs['pk']))
        return Response(response, status=status.HTTP_200_OK)

    def destroy(self, request, *args, **kwargs):
        """
            Delete an individual VNF package.

            The DELETE method deletes an individual VNF Package resource.
        """
        instance = self.get_object()
        if disabled != instance.operationalState:
            raise APIException(detail='VNF Package operationalState is not {}'.format(disabled),
                               code=status.HTTP_409_CONFLICT)

        if not_in_use != instance.usageState:
            raise APIException(detail='VNF Package usageState is not {}'.format(not_in_use),
                               code=status.HTTP_409_CONFLICT)

        remove_file('{}{}'.format(vnf_package_base_path, instance.id))
        super().destroy(request)
        self.kafka_notification.notify(kwargs['pk'], 'VNFPackage({}) had been destroy'.format(kwargs['pk']))
        return Response(status=status.HTTP_204_NO_CONTENT)

    @swagger_auto_schema(method='PUT',
                         operation_summary="""Upload the content of a NSD.""",
                         operation_description="""The PUT method uploads the content of a VNF package. \
                         This method shall follow the provisions specified in the Tables 9.4.5.3.3-1 \
                         and 9.4.5.3.3-2 for URI query parameters, request and response data structures, \
                         and response codes.""")
    @swagger_auto_schema(method='GET',
                         operation_summary="""Fetch an on-boarded VNF package.""",
                         operation_description="""The GET method fetches the content of a VNF package identified \
                         by the VNF package identifier allocated by the NFVO. \
                         This method shall follow the provisions specified in the Tables 9.4.5.3.2-1 \
                         and 9.4.5.3.2-2 for URI query parameters, request and response data structures, \
                         and response codes.""")
    @action(detail=True, methods=['PUT', 'GET'], url_path='package_content')
    def upload_content(self, request, **kwargs):
        instance = self.get_object()
        if request.method == 'PUT':
            print('000')
            if created != instance.onboardingState:
                raise APIException(detail='VNF Package onboardingState is not {}'.format(created),
                                   code=status.HTTP_409_CONFLICT)

            if 'application/zip' not in request.META['HTTP_ACCEPT']:
                raise APIException(detail='HEAD need to have application/zip value')

            vnf_package_path = '{}{}'.format(vnf_package_base_path, instance.id)
            print('111')
            vnf_package_content_path = decompress_zip(
                request.data['file'], vnf_package_path + '/package_content/')
            print('222')
            copy_file(vnf_package_path + "/package_content/", vnf_package_path + "/vnfd/", 'Definitions')
            print('333')
            process_vnf_instance = PackageVNF(path=vnf_package_content_path)
            print('444')
            input_value = process_vnf_instance.processing_data()
            print('555')

            serializer = self.get_serializer(instance, data=input_value)
            print('666')
            serializer.is_valid(raise_exception=True)
            print('777')
            serializer.save()
            print('999')

            self.kafka_notification.notify(kwargs['pk'], 'VNFPackage({}) had been upload'.format(kwargs['pk']))
            return Response(status=status.HTTP_202_ACCEPTED)
        elif request.method == 'GET':
            if on_boarded != instance.onboardingState:
                raise APIException(detail='VNF Package onboardingState is not {}'.format(on_boarded),
                                   code=status.HTTP_409_CONFLICT)

            if 'application/zip' not in request.META['HTTP_ACCEPT']:
                raise APIException(detail='HEAD need to have application/zip value')

            compression_result = compression_dir_zip(
                'package_content', '{}{}/package_content'.format(vnf_package_base_path, instance.id))
            response = HttpResponse(compression_result[0].getvalue(),
                                    content_type="application/x-zip-compressed",
                                    status=status.HTTP_200_OK)
            response['Content-Disposition'] = 'attachment; filename=%s' % compression_result[1]
            return response

    @action(detail=True, methods=['POST'], url_path='package_content/upload_from_uri')
    def upload_uri(self, request, **kwargs):
        """
            Upload a VNF package by providing the address information of the VNF package.

            The POST method provides the information for the NFVO to get the content of a VNF package. \
            This method shall follow the provisions specified in the Tables 9.4.6.3.1-1 and \
            9.4.6.3.1-2 for URI query parameters, request and response data structures, and response codes.
        """
        instance = self.get_object()
        if created != instance.onboardingState:
            raise APIException(detail='VNF Package onboardingState is not {]'.format(created))

        request = BaseRequest('').get(request.data['UploadVnfPackageFromUriRequest']['addressInformation'])
        if request:
            raise APIException(detail='Uri Connection Refused')

        vnf_package_path = "{}{}".format(vnf_package_base_path, instance.id)
        file_path = decompress_zip(
            io.BytesIO(request.content),
            vnf_package_path + '/package_content/')
        copy_file(file_path + '/package_content/', file_path + '/vnfd/', 'Definitions')
        process_vnf_instance = PackageVNF(path=vnf_package_path)
        input_value = process_vnf_instance.processing_data()

        serializer = self.get_serializer(instance, data=input_value)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        self.kafka_notification.notify(kwargs['pk'], 'VNFPackage({}) had been upload'.format(kwargs['pk']))
        return Response(status=status.HTTP_202_ACCEPTED)

    @action(detail=True, methods=['GET'], url_path='artifacts/(?P<artifactPath>.+)')
    def fetch_artifact(self, request, **kwargs):
        """
            Fetch individual VNF package artifact.

            The GET method fetches the content of an artifact within a VNF package. \
            This method shall follow the provisions specified in the Tables 9.4.7.3.2-1 and \
            9.4.7.3.2-2 for URI query parameters, request and response data structures, and response codes.
        """
        instance = self.get_object()
        if on_boarded != instance.onboardingState:
            raise APIException(detail='VNF Package OnboardingState is not {}'.format(on_boarded),
                               code=status.HTTP_409_CONFLICT)

        if 'application/zip' not in request.META['HTTP_ACCEPT']:
            raise APIException(detail='HEAD need to have application/zip value')

        artifact_path = '{}{}/package_content/{}'.format(vnf_package_base_path, instance.id, kwargs['artifactPath'])
        if not os.path.exists(artifact_path):
            raise APIException(detail='artifact path is not exists')

        response = HttpResponse(
            content_type='application/force-download', status=status.HTTP_200_OK)
        response['Content-Disposition'] = 'attachment; filename=%s' % smart_str(os.path.split(artifact_path)[1])
        response['X-Sendfile'] = smart_str(artifact_path)
        return response

    @action(detail=True, methods=['GET'], url_path='vnfd')
    def fetch_vnfd(self, request, **kwargs):
        """
            Read VNFD of an on-boarded VNF package.

            The GET method reads the content of the VNFD within a VNF package.
            The VNFD can be implemented as a single file or as a collection of multiple files. \
            If the VNFD is implemented in the form of multiple files, \
            a ZIP file embedding these files shall be returned.
            If the VNFD is implemented as a single file, either that file or a ZIP file embedding
            that file shall be returned. \
            The selection of the format is controlled by the “Accept” HTTP header passed in the GET request.\
            • If the “Accept” header contains only “text/plain” and the VNFD is implemented as a single file, \
            the file shall be returned; otherwise, an error message shall be returned. \
            • If the “Accept” header contains only "application/zip", \
            the single file or the multiple files that make up the VNFD shall be returned embedded in a ZIP file.\
            • If the “Accept” header contains both “text/plain” and "application/zip", \
            it is up to the NFVO to choose the format to return for a single-file VNFD; for a multi-file VNFD, \
            a ZIP file shall be returned. \
            The default format of the ZIP file shall be the one specified in ETSI GS NFV-SOL 004 [5] \
            where only the YAML files representing the VNFD, and information necessary to navigate the ZIP file \
            and to identify the file that is the entry point for parsing the VNFD (such as TOSCA-meta or manifest files \
            or naming conventions) are included. This method shall follow the provisions specified \
            in the Tables 9.4.4.3.2-1 and 9.4.4.3.2-2 for URI query parameters, request and response data structures, \
            and response codes.
        """
        instance = self.get_object()
        if on_boarded != instance.onboardingState:
            raise APIException(detail='VNF Package onboardingState is not {}'.format(on_boarded))

        if 'application/zip' not in request.META['HTTP_ACCEPT']:
            raise APIException(detail='HEAD need to have application/zip value')

        vnfd_path = '{}{}/vnfd'.format(vnf_package_base_path, instance.id)
        compression_result = compression_dir_zip('vnfd', vnfd_path)

        response = HttpResponse(compression_result[0].getvalue(),
                                content_type="application/x-zip-compressed",
                                status=status.HTTP_200_OK)
        response['Content-Disposition'] = 'attachment; filename=%s' % compression_result[1]
        return response
