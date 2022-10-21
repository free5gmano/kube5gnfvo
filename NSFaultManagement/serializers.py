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
from rest_framework import serializers

from NSFaultManagement.models import AlarmLinks, Alarm, FaultyComponentInfo, ResourceHandle, FaultyResourceInfo
from utils.format_tools import transform_representation


class AlarmLinksSerializer(serializers.ModelSerializer):
    self = serializers.CharField(source='link_self')

    class Meta:
        model = AlarmLinks
        fields = ('objectInstance', 'self')

    def to_representation(self, instance):
        return transform_representation(super().to_representation(instance))


class ResourceHandleSerializer(serializers.ModelSerializer):
    class Meta:
        model = ResourceHandle
        fields = '__all__'
        ref_name = "AlarmSerializer_ResourceHandleSerializer"


class FaultyResourceInfoSerializer(serializers.ModelSerializer):
    _links = ResourceHandleSerializer(required=False, source='alarm_fk_link')

    class Meta:
        model = FaultyResourceInfo
        fields = '__all__'


class FaultyComponentInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = FaultyComponentInfo
        fields = '__all__'


class AlarmSerializer(serializers.ModelSerializer):
    _links = AlarmLinksSerializer(required=False, source='alarm_fk_link')
    rootCauseFaultyResource = FaultyResourceInfoSerializer(required=False,
                                                           source='alarm_fk_root_cause_faulty_resource')
    rootCauseFaultyComponent = FaultyComponentInfoSerializer(required=False,
                                                             source='alarm_fk_root_cause_faulty_component')

    class Meta:
        model = Alarm
        fields = '__all__'

    def to_representation(self, instance):
        return transform_representation(super().to_representation(instance))
