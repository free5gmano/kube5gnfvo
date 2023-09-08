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
import uuid

from rest_framework import viewsets, status
from rest_framework.exceptions import APIException

from NSFaultSubscription.models import FmSubscription
from NSFaultSubscription.serializers import FmSubscriptionSerializer
from NSLifecycleManagement.models import NsInstance


class NSFaultSubscriptionViewSet(viewsets.ModelViewSet):
    queryset = FmSubscription.objects.all()
    serializer_class = FmSubscriptionSerializer

    def create(self, request, **kwargs):
        """
            Subscribe to alarms related to NSs.

            The POST method creates a new subscription.
            This method shall follow the provisions specified in the Tables 8.4.4.3.1-1 and 8.4.4.3.1-2 \
            for URI query parameters, request and response data structures, and response codes. \
            As the result of successfully executing this method, a new “Individual subscription” resource shall exist \
            as defined in clause 8.4.5. This method shall not trigger any notification.
            Creation of two subscription resources with the same callbackURI \
            and the same filter can result in performance degradation and will provide duplicates of notifications \
            to the OSS, and might make sense only in very rare use cases. \
            Consequently, the NFVO may either allow creating a subscription resource \
            if another subscription resource with the same filter and callbackUri already exists \
            (in which case it shall return the “201 Created” response code), \
            or may decide to not create a duplicate subscription resource \
            (in which case it shall return a “303 See Other” response code referencing the existing subscription \
            resource with the same filter and callbackUri).
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
            Read an individual subscription.

            The client can use this method for reading an individual subscription \
            for alarms related to NSs subscribed by the client. This method shall follow the provisions specified \
            in the Tables 8.4.5.3.2-1 and 8.4.5.3.2-2 for URI query parameters, \
            request and response data structures, and response codes
        """
        return super().retrieve(request)

    def list(self, request, *args, **kwargs):
        """
            Query alarms related to NS instances.

            The client can use this method to retrieve the list of active subscriptions \
            for alarms related to a NS subscribed by the client. \
            It can be used e.g. for resynchronization after error situations.
            This method shall follow the provisions specified in the Tables 8.4.4.3.2-1 \
            and 8.4.4.3.2-2 for URI query parameters, request and response data structures, \
            and response codes. Table 8.4.4.3.2-1: URI query parameters supported.
        """
        return super().list(request)

    def destroy(self, request, *args, **kwargs):
        """
            Terminate a subscription.

            This method terminates an individual subscription.
            As the result of successfully executing this method, \
            the “Individual subscription” resource shall not exist any longer.
            This means that no notifications for that subscription shall be sent to the formerly-subscribed API consumer.
            NOTE: Due to race conditions, some notifications might still be received \
            by the formerly-subscribed API consumer for a certain time period after the deletion.
        """
        return super().destroy(request)
