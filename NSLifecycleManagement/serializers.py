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
from rest_framework import serializers
from utils.format_tools import transform_representation
from .models import *


class VnffgInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = VnffgInfo
        fields = ('id', 'vnffgdId', 'vnfInstanceId')

    def to_representation(self, instance):
        return transform_representation(super().to_representation(instance))


class NsInstanceLinksSerializer(serializers.ModelSerializer):
    self = serializers.CharField(source='link_self')

    class Meta:
        model = NsInstanceLinks
        fields = ('self', 'nestedNsInstances', 'instantiate', 'terminate', 'update', 'scale', 'heal')


class InstantiatedVnfInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = InstantiatedVnfInfo
        fields = ('vnfState',)


class VnfInstanceSerializer(serializers.ModelSerializer):
    instantiatedVnfInfo = InstantiatedVnfInfoSerializer(required=False,
                                                        source='VnfInstance_instantiatedVnfInfo')

    class Meta:
        model = VnfInstance
        fields = ('id', 'vnfInstanceName', 'vnfdId', 'vnfProvider', 'vnfProductName', 'vnfdVersion',
                  'vnfPkgId', 'instantiationState', 'instantiatedVnfInfo')


class NsInstanceSerializer(serializers.ModelSerializer):
    vnffgInfo = VnffgInfoSerializer(many=True, required=False, source='NsInstance_VnffgInfo')
    vnfInstance = VnfInstanceSerializer(many=True, required=False, source='NsInstance_VnfInstance')
    _links = NsInstanceLinksSerializer(required=False, source='NsInstance_links')

    class Meta:
        model = NsInstance
        fields = '__all__'

    def create(self, validated_data):
        link_value = validated_data.pop('NsInstance_links')
        vnf_Instance_dict = validated_data.pop('NsInstance_VnfInstance', None)
        vnffg_info_list = validated_data.pop('NsInstance_VnffgInfo', None)
        ns = NsInstance.objects.create(**validated_data)

        NsInstanceLinks.objects.create(
            _links=ns, **{'link_self': link_value['link_self'] + str(ns.id)})

        vnf_Instance_id = list()
        if vnf_Instance_dict:
            for vnf_Instance_value in vnf_Instance_dict:
                instantiated_vnfInfo = vnf_Instance_value.pop('VnfInstance_instantiatedVnfInfo')
                vnf_Instance = VnfInstance.objects.create(**vnf_Instance_value)
                InstantiatedVnfInfo.objects.create(instantiatedVnfInfo=vnf_Instance,
                                                   **instantiated_vnfInfo)
                ns.NsInstance_VnfInstance.add(vnf_Instance)
                vnf_Instance_id.append(str(vnf_Instance.id))
        if vnffg_info_list:
            for vnffg_info in vnffg_info_list:
                vnffgd_id = vnffg_info['vnffgdId']
                vnffgd_info = VnffgInfo.objects.create(
                    **{'vnffgdId': vnffgd_id, 'vnfInstanceId': json.dumps(vnf_Instance_id)})
                ns.NsInstance_VnffgInfo.add(vnffgd_info)

        return ns

    def update(self, instance, validated_data):
        return super().update(instance, validated_data)
