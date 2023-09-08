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


class PkgmSubscriptionLinkSerializer(serializers.ModelSerializer):
    self = serializers.CharField(source='link_self')

    class Meta:
        model = PkgmSubscriptionLink
        fields = ('self',)


class PkgmNotificationsVersionsSerializer(serializers.ModelSerializer):
    class Meta:
        model = PkgmNotificationsVersions
        fields = ('vnfSoftwareVersion', 'vnfdVersions')

    def to_representation(self, instance):
        return transform_representation(super().to_representation(instance))


class PkgmNotificationsProductsSerializer(serializers.ModelSerializer):
    versions = PkgmNotificationsVersionsSerializer(
        many=True, required=False, source='pkgm_notifications_products_fk_versions')

    class Meta:
        model = PkgmNotificationsProducts
        fields = ('vnfProductName', 'versions')


class PkgmNotificationsProvidersSerializer(serializers.ModelSerializer):
    vnfProducts = PkgmNotificationsProductsSerializer(
        many=True, required=False, source='pkgm_notifications_providers_fk_products')

    class Meta:
        model = PkgmNotificationsProviders
        fields = ('vnfProvider', 'vnfProducts')


class PkgmNotificationsFilterSerializer(serializers.ModelSerializer):
    vnfProductsFromProviders = PkgmNotificationsProvidersSerializer(required=False, many=True,
                                                                    source='pkgm_notifications_fk_providers')

    class Meta:
        model = PkgmNotificationsFilter
        fields = ('notificationTypes', 'vnfProductsFromProviders', 'vnfdId', 'vnfPkgId',
                  'operationalState', 'usageState')

    def to_representation(self, instance):
        return transform_representation(super().to_representation(instance))


class PkgmSubscriptionSerializer(serializers.ModelSerializer):
    _links = PkgmSubscriptionLinkSerializer(source='pkgm_subscription_fk_links')
    filter = PkgmNotificationsFilterSerializer(required=False, source='pkgm_subscription_fk_filter')

    class Meta:
        model = PkgmSubscription
        fields = '__all__'

    def create(self, validated_data):
        filter_value = validated_data.pop('pkgm_subscription_fk_filter', None)
        link_value = validated_data.pop('pkgm_subscription_fk_links')
        pkgm = PkgmSubscription.objects.create(**validated_data)
        PkgmSubscriptionLink.objects.create(_links=pkgm,
                                            **{'link_self': link_value['link_self'] + str(pkgm.id)})

        if filter_value:
            pkgm_providers_list = filter_value.pop('pkgm_notifications_fk_providers', None)
            pkgm_filter = PkgmNotificationsFilter.objects.create(filter=pkgm, **filter_value)
            if pkgm_providers_list:
                for providers in pkgm_providers_list:
                    products_list = providers.pop('pkgm_notifications_providers_fk_products', None)
                    pkgm_providers = pkgm_filter.pkgm_notifications_fk_providers.create(**providers)
                    if products_list:
                        for products in products_list:
                            versions_list = products.pop('pkgm_notifications_products_fk_versions', None)
                            pkgm_products = pkgm_providers.pkgm_notifications_providers_fk_products.create(**products)
                            if versions_list:
                                for versions in versions_list:
                                    pkgm_products.pkgm_notifications_products_fk_versions.create(**versions)
        return pkgm
