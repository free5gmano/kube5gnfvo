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
from rest_framework.exceptions import APIException

from NSLifecycleManagement.models import NsInstance
from NSLifecycleSubscriptions.serializers import *
from rest_framework import viewsets, status
from rest_framework.utils import json


class NSLifecycleSubscriptionsViewSet(viewsets.ModelViewSet):
    queryset = LccnSubscription.objects.all()
    serializer_class = LccnSubscriptionSerializer

    def create(self, request, **kwargs):
        """
            Subscribe to NS lifecycle change notifications.

            The POST method creates a new subscription. \
            This method shall support the URI query parameters, request and response data structures, \
            and response codes, as specified in the Tables 6.4.16.3.1-1 and 6.4.16.3.1-2. \
            Creation of two subscription resources with the same callbackURI \
            and the same filter can result in performance degradation \
            and will provide duplicates of notifications to the OSS, \
            and might make sense only in very rare use cases. Consequently, \
            the NFVO may either allow creating a subscription resource \
            if another subscription resource with the same filter and callbackUri already exists (in which case \
            it shall return the “201 Created” response code), \
            or may decide to not create a duplicate subscription resource \
            (in which case it shall return a “303 See Other” response code \
            referencing the existing subscription resource with the same filter and callbackUri).
        """
        if 'filter' not in request.data or 'callbackUri' not in request.data:
            raise APIException(detail='filter or callbackUri is not exists',
                               code=status.HTTP_409_CONFLICT)

        ns_instance_subscription_filter = request.data['filter'].get('nsInstanceSubscriptionFilter', None)
        if not ns_instance_subscription_filter:
            raise APIException(detail='nsInstanceSubscriptionFilter is not exists',
                               code=status.HTTP_409_CONFLICT)

        if not isinstance(ns_instance_subscription_filter, dict):
            raise APIException(detail='nsInstanceSubscriptionFilter needs dict type',
                               code=status.HTTP_409_CONFLICT)

        ns_instance_id = ns_instance_subscription_filter.get('nsInstanceIds', None)
        if not ns_instance_id:
            raise APIException(detail='nsInstanceIds is not exists',
                               code=status.HTTP_409_CONFLICT)

        if not isinstance(ns_instance_id, list):
            raise APIException(detail='nsInstanceIds needs list type',
                               code=status.HTTP_409_CONFLICT)

        for ns_id in ns_instance_id:
            ns_instance = NsInstance.objects.filter(id=uuid.UUID(ns_id)).last()
            if not ns_instance:
                raise APIException(detail='Network Service Instance not found',
                                   code=status.HTTP_404_NOT_FOUND)

        request.data['filter']['nsInstanceSubscriptionFilter']['nsInstanceIds'] = json.dumps(ns_instance_id)
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

            The GET method retrieves information about a subscription by reading an individual subscription resource. \
            This method shall support the URI query parameters, request and response data structures, \
            and response codes, as specified in the Tables 6.4.17.3.2-1 and 6.4.17.3.2-2
        """
        return super().retrieve(request)

    def list(self, request, *args, **kwargs):
        """
            Query multiple subscriptions.

            Query Subscription Information. \
            The GET method queries the list of active subscriptions of the functional block that invokes the method. \
            It can be used e.g. for resynchronization after error situations.
        """
        return super().list(request)

    def destroy(self, request, *args, **kwargs):
        """
            Terminate a subscription.

            The DELETE method terminates an individual subscription. \
            This method shall support the URI query parameters, request and response data structures, \
            and response codes, as specified in the Tables 6.4.17.3.5-1 and 6.4.17.3.5-2.
        """
        return super().destroy(request)
