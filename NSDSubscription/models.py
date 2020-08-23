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
from django.db import models
import uuid


class NsdmSubscription(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    callbackUri = models.TextField()


class NsdmSubscriptionLink(models.Model):
    _links = models.OneToOneField(
        NsdmSubscription, on_delete=models.CASCADE, primary_key=True, related_name='nsdm_subscription_fk_links')
    link_self = models.URLField()


class NsdmNotificationsFilter(models.Model):
    filter = models.OneToOneField(
        NsdmSubscription, on_delete=models.CASCADE, primary_key=True, related_name='nsdm_subscription_fk_filter')
    notificationTypes = models.TextField(null=True, blank=True)
    nsdInfoId = models.TextField(null=True, blank=True)
    nsdId = models.TextField(null=True, blank=True)
    nsdName = models.TextField(null=True, blank=True)
    nsdVersion = models.TextField(null=True, blank=True)
    nsdDesigner = models.TextField(null=True, blank=True)
    nsdInvariantId = models.TextField(null=True, blank=True)
    vnfPkgIds = models.TextField(null=True, blank=True)
    pnfdInfoIds = models.TextField(null=True, blank=True)
    nestedNsdInfoIds = models.TextField(null=True, blank=True)
    nsdOnboardingState = models.TextField(null=True, blank=True)
    nsdOperationalState = models.TextField(null=True, blank=True)
    nsdUsageState = models.TextField(null=True, blank=True)
    pnfdId = models.TextField(null=True, blank=True)
    pnfdName = models.TextField(null=True, blank=True)
    pnfdVersion = models.TextField(null=True, blank=True)
    pnfdProvider = models.TextField(null=True, blank=True)
    pnfdInvariantId = models.TextField(null=True, blank=True)
    pnfdOnboardingState = models.TextField(null=True, blank=True)
    pnfdUsageState = models.TextField(null=True, blank=True)
