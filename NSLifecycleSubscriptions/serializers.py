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
        ref_name = 'LccnSubscriptionSerializer_NsInstanceSubscriptionFilterSerializer'

    def to_representation(self, instance):
        return transform_representation(super().to_representation(instance))


class LifecycleChangeNotificationsFilterSerializer(serializers.ModelSerializer):
    nsInstanceSubscriptionFilter = NsInstanceSubscriptionFilterSerializer(
        required=False, source='lccn_subscription_filter_fk_filter')

    class Meta:
        model = LifecycleChangeNotificationsFilter
        fields = ('nsInstanceSubscriptionFilter', 'notificationTypes', 'operationTypes', 'operationStates',
                  'nsComponentTypes', 'lcmOpNameImpactingNsComponent', 'lcmOpOccStatusImpactingNsComponent')

    def to_representation(self, instance):
        return transform_representation(super().to_representation(instance))


class LccnSubscriptionLinkSerializer(serializers.ModelSerializer):
    self = serializers.CharField(source='link_self')

    class Meta:
        model = LccnSubscriptionLink
        fields = ('self',)


class LccnSubscriptionSerializer(serializers.ModelSerializer):
    _links = LccnSubscriptionLinkSerializer(required=False, source='lccn_subscription_fk_links')
    filter = LifecycleChangeNotificationsFilterSerializer(required=False, source='lccn_subscription_fk_filter')

    class Meta:
        model = LccnSubscription
        fields = '__all__'

    def create(self, validated_data):
        filter_value = validated_data.pop('lccn_subscription_fk_filter')
        link_value = validated_data.pop('lccn_subscription_fk_links')
        nsdm = LccnSubscription.objects.create(**validated_data)
        LccnSubscriptionLink.objects.create(
            _links=nsdm, **{'link_self': link_value['link_self'] + str(nsdm.id)})
        ns_instance_subscription_value = filter_value.pop('lccn_subscription_filter_fk_filter')
        lifecycle_change_notifications_filter = LifecycleChangeNotificationsFilter.objects.create(
            filter=nsdm, **filter_value)
        NsInstanceSubscriptionFilter.objects.create(
            nsInstanceSubscriptionFilter=lifecycle_change_notifications_filter, **ns_instance_subscription_value)
        return nsdm
