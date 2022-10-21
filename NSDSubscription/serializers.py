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


class NsdmNotificationsFilterSerializer(serializers.ModelSerializer):
    class Meta:
        model = NsdmNotificationsFilter
        fields = ('notificationTypes', 'nsdInfoId', 'nsdId', 'nsdName', 'nsdVersion', 'nsdDesigner',
                  'nsdInvariantId', 'vnfPkgIds', 'pnfdInfoIds', 'nestedNsdInfoIds', 'nsdOnboardingState',
                  'nsdOperationalState', 'nsdUsageState', 'pnfdId', 'pnfdName', 'pnfdVersion', 'pnfdProvider',
                  'pnfdInvariantId', 'pnfdOnboardingState', 'pnfdUsageState')

    def to_representation(self, instance):
        return transform_representation(super().to_representation(instance))


class NsdmSubscriptionLinkSerializer(serializers.ModelSerializer):
    self = serializers.CharField(source='link_self')

    class Meta:
        model = NsdmSubscriptionLink
        fields = ('self',)


class NsdmSubscriptionSerializer(serializers.ModelSerializer):
    _links = NsdmSubscriptionLinkSerializer(required=False, source='nsdm_subscription_fk_links')
    filter = NsdmNotificationsFilterSerializer(required=False, source='nsdm_subscription_fk_filter')

    class Meta:
        model = NsdmSubscription
        fields = '__all__'

    def create(self, validated_data):
        filter_value = validated_data.pop('nsdm_subscription_fk_filter', None)
        link_value = validated_data.pop('nsdm_subscription_fk_links')
        nsdm = NsdmSubscription.objects.create(**validated_data)
        NsdmSubscriptionLink.objects.create(
            _links=nsdm, **{'link_self': link_value['link_self'] + str(nsdm.id)})

        if filter_value:
            NsdmNotificationsFilter.objects.create(filter=nsdm, **filter_value)
        return nsdm
