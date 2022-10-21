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

from rest_framework import viewsets, status
from rest_framework.exceptions import APIException

from VnfPackageManagement.models import VnfPkgInfo
from VnfPackageSubscription.serializers import *


class VNFPackageSubscriptionViewSet(viewsets.ModelViewSet):
    queryset = PkgmSubscription.objects.all()
    serializer_class = PkgmSubscriptionSerializer

    def create(self, request, **kwargs):
        """
            Subscribe to notifications related to on-boarding and/or changes of VNF packages.

            The POST method creates a new subscription. \
            This method shall follow the provisions specified in the Tables 9.4.8.3.1-1 \
            and 9.4.8.3.1-2 for URI query parameters, request and response data structures, \
            and response codes. As the result of successfully executing this method, \
            a new “Individual subscription” resource shall exist as defined in clause 9.4.9. \
            This method shall not trigger any notification. \
            Creation of two subscription resources with the same callbackURI \
            and the same filter can result in performance degradation \
            and will provide duplicates of notifications to the OSS, \
            and might make sense only in very rare use cases. Consequently, \
            the NFVO may either allow creating a subscription resource \
            if another subscription resource with the same filter \
            and callbackUri already exists (in which case it shall return the “201 Created” response code), \
            or may decide to not create a duplicate subscription resource \
            (in which case it shall return a “303 See Other” response code referencing the existing subscription \
            resource with the same filter and callbackUri).
        """
        if 'filter' not in request.data or 'callbackUri' not in request.data:
            raise APIException(detail='filter or callbackUri is not exists',
                               code=status.HTTP_409_CONFLICT)

        vnf_package_id = request.data['filter'].get('vnfPkgId', None)
        if not vnf_package_id:
            raise APIException(detail='vnfPkgId is not exists',
                               code=status.HTTP_409_CONFLICT)

        if not isinstance(vnf_package_id, list):
            raise APIException(detail='vnfPkgId needs list type',
                               code=status.HTTP_409_CONFLICT)

        for vnf_pk_id in vnf_package_id:
            vnf_package = VnfPkgInfo.objects.filter(id=uuid.UUID(vnf_pk_id)).last()
            if not vnf_package:
                raise APIException(detail='VNF Package({}) not found'.format(vnf_pk_id),
                                   code=status.HTTP_404_NOT_FOUND)

        request.data['filter']['vnfPkgId'] = json.dumps(vnf_package_id)
        request.data['_links'] = {'self': request.build_absolute_uri()}
        return super().create(request)

    def get_success_headers(self, data):
        return {'Location': data['_links']['self']}

    def update(self, request, *args, **kwargs):
        raise APIException(detail='Method Not Allowed',
                           code=status.HTTP_405_METHOD_NOT_ALLOWED)

    def retrieve(self, request, *args, **kwargs):
        """
            Read an individual subscription resource.

            Query Subscription Information The GET method reads an individual subscription.
        """
        return super().retrieve(request)

    def list(self, request, *args, **kwargs):
        """
            Query multiple subscriptions.

            The GET method queries the list of active subscriptions of the functional block that invokes the method. \
            It can be used e.g. for resynchronization after error situations. \
            This method shall follow the provisions specified in the Tables 9.4.7.8.2-1 \
            and 9.4.8.3.2-2 for URI query parameters, request and response data structures, and response codes.
        """
        return super().list(request)

    def destroy(self, request, *args, **kwargs):
        """
            Terminate a subscription.

            The DELETE method terminates an individual subscription. \
            This method shall follow the provisions specified in the Tables 9.4.9.3.5-1 and 9.4.9.3.5-2 \
            for URI query parameters, request and response data structures, and response codes. \
            As the result of successfully executing this method, \
            the “Individual subscription” resource shall not exist any longer. \
            This means that no notifications for that subscription shall be sent to the formerly-subscribed API consumer.\
            NOTE: Due to race conditions, some notifications might still be received \
            by the formerly-subscribed API consumer for a certain time period after the deletion.
        """
        return super().destroy(request)
