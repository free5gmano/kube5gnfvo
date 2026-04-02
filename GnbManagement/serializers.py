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
from .models import GnbInstance, GnbTemplate


class GnbTemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = GnbTemplate
        fields = ['id', 'templateName', 'templateDescription', 'namespace',
                  'yamlContent', 'createdAt', 'updatedAt']
        read_only_fields = ['id', 'createdAt', 'updatedAt']


class GnbTemplateCreateSerializer(serializers.Serializer):
    templateName = serializers.CharField(max_length=255)
    templateDescription = serializers.CharField(required=False, allow_blank=True)
    namespace = serializers.CharField(default='default')
    yamlContent = serializers.CharField()


class GnbInstanceSerializer(serializers.ModelSerializer):
    class Meta:
        model = GnbInstance
        fields = ['id', 'gnbInstanceName', 'gnbInstanceDescription', 'namespace', 
                  'deploymentState', 'createdAt', 'updatedAt']
        read_only_fields = ['id', 'createdAt', 'updatedAt']


class GnbInstanceCreateSerializer(serializers.Serializer):
    gnbInstanceName = serializers.CharField(max_length=255)
    gnbInstanceDescription = serializers.CharField(required=False, allow_blank=True)
    namespace = serializers.CharField(default='default')
    yamlContent = serializers.CharField()


class GnbTemplateDeploySerializer(serializers.Serializer):
    gnbInstanceName = serializers.CharField(max_length=255, required=False, allow_blank=True)
    gnbInstanceDescription = serializers.CharField(required=False, allow_blank=True)
    namespace = serializers.CharField(required=False, allow_blank=True)
