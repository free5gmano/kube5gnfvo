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
from utils.format_tools import transform_representation
from .models import *


class ResourceHandleSerializer(serializers.ModelSerializer):
    class Meta:
        model = ResourceHandle
        fields = ('vimId', 'resourceProviderId', 'resourceId', 'vimLevelResourceType')


class ExtLinkPortInfoSerializer(serializers.ModelSerializer):
    resourceHandle = ResourceHandleSerializer(source='extLinkPortInfo_resourceHandle')

    class Meta:
        model = ExtLinkPortInfo
        fields = ('id', 'resourceHandle', 'cpInstancedId')


class ExtVirtualLinkInfoSerializer(serializers.ModelSerializer):
    resourceHandle = ResourceHandleSerializer(source='resourceHandle')
    extLinkPorts = ExtLinkPortInfoSerializer(required=False, many=True)

    class Meta:
        model = ExtVirtualLinkInfo
        fields = ('id', 'resourceHandle', 'extLinkPorts')


class ModifyVnfInfoDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = ModifyVnfInfoData
        fields = ('vnfInstanceId', 'vnfInstanceName', 'vnfInstanceDescription', 'vnfdId',
                  'vnfConfigurableProperties', 'metadata', 'extensions')


class ChangedInfoSerializer(serializers.ModelSerializer):
    changedVnfInfo = ModifyVnfInfoDataSerializer(required=False)
    changedExtConnectivity = ExtVirtualLinkInfoSerializer(required=False, many=True)

    class Meta:
        model = ChangedInfo
        fields = ('changedVnfInfo', 'changedExtConnectivity')


class AffectedSapSerializer(serializers.ModelSerializer):
    class Meta:
        model = AffectedSap
        fields = ('sapInstanceId', 'sapdId', 'sapName', 'changeType', 'changeResult')


class AffectedNsSerializer(serializers.ModelSerializer):
    class Meta:
        model = AffectedNs
        fields = ('nsInstanceId', 'nsdId', 'changeType', 'changeResult')


class AffectedVnffgSerializer(serializers.ModelSerializer):
    class Meta:
        model = AffectedVnffg
        fields = ('vnffgInstanceId', 'vnffgdId', 'changeType', 'changeResult')


class AffectedVirtualLinkSerializer(serializers.ModelSerializer):
    class Meta:
        model = AffectedVirtualLink
        fileds = ('nsVirtualLinkInstanceId', 'nsVirtualLinkDescId', 'vlProfiled', 'changeType', 'changeResult')


class AffectedVnfSerializer(serializers.ModelSerializer):
    changedInfo = ChangedInfoSerializer(required=False)

    class Meta:
        model = AffectedVnf
        fields = ('vnfInstanceId', 'vnfdId', 'vnfProfileId', 'vnfName', 'changeType', 'changeResult', 'changedInfo')


class LinkSerializer(serializers.ModelSerializer):
    self = serializers.CharField(source='link_self')

    class Meta:
        model = Links
        fields = ('self', 'nsInstance', 'cancel', 'retry', 'rollback', '_continue', 'fail')

    def to_representation(self, instance):
        return transform_representation(super().to_representation(instance))


class ResourceChangesSerializer(serializers.ModelSerializer):
    affectedVnfs = AffectedVnfSerializer(required=False, many=True)
    affectedVls = AffectedVirtualLinkSerializer(required=False, many=True)
    affectedVnffgs = AffectedVnffgSerializer(required=False, many=True)
    affectedNss = AffectedNsSerializer(required=False, many=True)
    affectedSaps = AffectedSapSerializer(required=False, many=True)

    class Meta:
        model = ResourceChanges
        fields = ('affectedVnfs', 'affectedVls', 'affectedVnffgs', 'affectedNss', 'affectedSaps')


class NsLcmOpOccSerializer(serializers.ModelSerializer):
    resourceChanges = ResourceChangesSerializer(required=False)
    _links = LinkSerializer(required=False)

    def to_representation(self, instance):
        return transform_representation(super().to_representation(instance))

    class Meta:
        model = NsLcmOpOcc
        fields = '__all__'
