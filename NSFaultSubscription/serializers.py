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


class NsInstanceSubscriptionFilterSerializer(serializers.ModelSerializer):
    class Meta:
        model = NsInstanceSubscriptionFilter
        fields = ('nsdIds', 'vnfdIds', 'pnfdIds', 'nsInstanceIds', 'nsInstanceNames')
        ref_name = 'FmSubscriptionSerializer_NsInstanceSubscriptionFilterSerializer'

    def to_representation(self, instance):
        return transform_representation(super().to_representation(instance))


class FmSubscriptionsFilterSerializer(serializers.ModelSerializer):
    nsInstanceSubscriptionFilter = NsInstanceSubscriptionFilterSerializer(
        required=False, source='fm_subscription_filter_fk_ns_instance_subscription_filter')

    class Meta:
        model = FmSubscriptionsFilter
        fields = ('nsInstanceSubscriptionFilter', 'notificationTypes', 'faultyResourceTypes',
                  'perceivedSeverities', 'eventTypes', 'probableCauses')


class FmSubscriptionLinkSerializer(serializers.ModelSerializer):
    self = serializers.CharField(source='link_self')

    class Meta:
        model = FmSubscriptionLink
        fields = ('self',)


class FmSubscriptionSerializer(serializers.ModelSerializer):
    _links = FmSubscriptionLinkSerializer(required=False, source='fm_subscription_fk_fm_subscription_link')
    filter = FmSubscriptionsFilterSerializer(required=False, source='fm_subscription_fk_fm_subscriptions_filter')

    class Meta:
        model = FmSubscription
        fields = '__all__'

    def create(self, validated_data):
        filter_dict = validated_data.pop('fm_subscription_fk_fm_subscriptions_filter', None)
        link_dict = validated_data.pop('fm_subscription_fk_fm_subscription_link')
        fm_subscription = FmSubscription.objects.create(**validated_data)
        FmSubscriptionLink.objects.create(_links=fm_subscription,
                                          **{'link_self': link_dict['link_self'] + str(fm_subscription.id)})
        if filter_dict:
            ns_instance_filter = filter_dict.pop('fm_subscription_filter_fk_ns_instance_subscription_filter')
            fm_subscriptions_filter = FmSubscriptionsFilter.objects.create(
                filter=fm_subscription, **filter_dict)
            NsInstanceSubscriptionFilter.objects.create(
                nsInstanceSubscriptionFilter=fm_subscriptions_filter,
                **ns_instance_filter)
        return fm_subscription
