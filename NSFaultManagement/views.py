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
from rest_framework import viewsets, status
from rest_framework.exceptions import APIException
from rest_framework.response import Response

from NSFaultManagement.models import Alarm
from NSFaultManagement.serializers import AlarmSerializer


class NSFaultManagementViewSet(viewsets.ModelViewSet):
    queryset = Alarm.objects.all()
    serializer_class = AlarmSerializer

    def create(self, request, *args, **kwargs):
        raise APIException(detail='Method Not Allowed',
                           code=status.HTTP_405_METHOD_NOT_ALLOWED)

    def update(self, request, *args, **kwargs):
        """
            Acknowledge individual alarm.

            Acknowledge Alarm This method modifies an individual alarm resource.
        """
        if 'AlarmModifications' not in request.data:
            raise APIException(detail='ValueError:Request need AlarmModifications',
                               code=status.HTTP_400_BAD_REQUEST)

        if 'ackState' not in request.data['AlarmModifications']:
            raise APIException(detail='ValueError:AlarmModifications need ackState',
                               code=status.HTTP_400_BAD_REQUEST)

        alarm = self.get_object()
        response = request.data.copy()
        request.data['ackState'] = request.data['AlarmModifications']['ackState']
        request.data['managedObjectId'] = alarm.managedObjectId
        super().update(request)
        return Response(response, status=status.HTTP_200_OK)

    def retrieve(self, request, *args, **kwargs):
        """
            Read individual alarm.

            The client can use this method to read an individual alarm.
        """
        return super().retrieve(request)

    def list(self, request, *args, **kwargs):
        """
            Query alarms related to NS instances.

            Get Alarm List. The client can use this method to retrieve information about the alarm list.
        """
        return super().list(request)

    def destroy(self, request, *args, **kwargs):
        raise APIException(detail='Method Not Allowed',
                           code=status.HTTP_405_METHOD_NOT_ALLOWED)
