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

import os

from rest_framework import serializers
from utils.file_manipulation import create_dir
from utils.format_tools import transform_representation
from .models import *

nsd_base_path = os.getcwd() + "/NSD/"
create_dir(nsd_base_path)


class ProblemDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = NsdInfoProblemDetails
        fields = ('type', 'title', 'status', 'detail', 'instance')


class NSDLinksSerializer(serializers.ModelSerializer):
    self = serializers.CharField(source='link_self')

    class Meta:
        model = NsdInfoLinks
        fields = ('nsd_content', 'self')


class NsdInfoSerializer(serializers.ModelSerializer):
    _links = NSDLinksSerializer(required=False, source='nsd_info_fk_link')
    onboardingFailureDetails = ProblemDetailsSerializer(required=False, source='nsd_info_fk_problem_details')

    class Meta:
        model = NsdInfo
        fields = '__all__'

    def to_representation(self, instance):
        return transform_representation(super().to_representation(instance))

    def create(self, validated_data):
        link_value = validated_data.pop('nsd_info_fk_link')
        nsd = NsdInfo.objects.create(**validated_data)
        path = '{}{}'.format(nsd_base_path, nsd.id)
        content_path = 'nsd_content'
        create_dir(path + "/" + content_path)
        NsdInfoLinks.objects.create(
            _links=nsd,
            **{'link_self': link_value['link_self'] + str(nsd.id),
               'nsd_content': link_value[content_path] + str(nsd.id) + "/" + content_path})
        return nsd

    def update(self, instance, validated_data):
        if 'nsdId' in validated_data:
            instance.nsdId = validated_data['nsdId']
            instance.nsdName = validated_data['nsdName']
            instance.nsdVersion = validated_data['nsdVersion']
            instance.nsdDesigner = validated_data['nsdDesigner']
            instance.nsdInvariantId = validated_data['nsdInvariantId']
            instance.vnfPkgIds = validated_data['vnfPkgIds']
            instance.nsdOnboardingState = 'ONBOARDED'
            instance.nsdOperationalState = 'ENABLED'
            instance.nsdUsageState = 'NOT_IN_USE'
            instance.save()
        else:
            instance.nsdOperationalState = validated_data['nsdOperationalState']
            instance.userDefinedData = validated_data['userDefinedData']
            instance.save()
        return instance
