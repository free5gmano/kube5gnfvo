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
import uuid
from django.db import models


class PkgmSubscription(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    callbackUri = models.TextField()


class PkgmSubscriptionLink(models.Model):
    _links = models.OneToOneField(PkgmSubscription,
                                  on_delete=models.CASCADE,
                                  primary_key=True,
                                  related_name='pkgm_subscription_fk_links')
    link_self = models.URLField()


class PkgmNotificationsFilter(models.Model):
    filter = models.OneToOneField(PkgmSubscription,
                                  on_delete=models.CASCADE,
                                  primary_key=True,
                                  related_name='pkgm_subscription_fk_filter')
    notificationTypes = models.TextField(null=True, blank=True)
    vnfdId = models.TextField(null=True, blank=True)
    vnfPkgId = models.TextField(null=True, blank=True)
    operationalState = models.TextField(null=True, blank=True)
    usageState = models.TextField(null=True, blank=True)


class PkgmNotificationsProviders(models.Model):
    vnfProductsFromProviders = models.ForeignKey(PkgmNotificationsFilter,
                                                 on_delete=models.CASCADE,
                                                 null=True,
                                                 blank=True,
                                                 related_name='pkgm_notifications_fk_providers')
    vnfProvider = models.TextField()


class PkgmNotificationsProducts(models.Model):
    vnfProducts = models.ForeignKey(PkgmNotificationsProviders,
                                    on_delete=models.CASCADE,
                                    null=True,
                                    blank=True,
                                    related_name='pkgm_notifications_providers_fk_products')
    vnfProductName = models.TextField()


class PkgmNotificationsVersions(models.Model):
    versions = models.ForeignKey(PkgmNotificationsProducts,
                                 on_delete=models.CASCADE,
                                 null=True,
                                 blank=True,
                                 related_name='pkgm_notifications_products_fk_versions')
    vnfSoftwareVersion = models.TextField()
    vnfdVersions = models.TextField(null=True, blank=True)
