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


class LccnSubscription(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    callbackUri = models.TextField()


class LccnSubscriptionLink(models.Model):
    _links = models.OneToOneField(
        LccnSubscription, on_delete=models.CASCADE, primary_key=True, related_name='lccn_subscription_fk_links')

    link_self = models.URLField()


class LifecycleChangeNotificationsFilter(models.Model):
    filter = models.OneToOneField(
        LccnSubscription, on_delete=models.CASCADE, primary_key=True, related_name='lccn_subscription_fk_filter')
    notificationTypes = models.TextField(null=True, blank=True)
    operationTypes = models.TextField(null=True, blank=True)
    operationStates = models.TextField(null=True, blank=True)
    nsComponentTypes = models.TextField(null=True, blank=True)
    lcmOpNameImpactingNsComponent = models.TextField(null=True, blank=True)
    lcmOpOccStatusImpactingNsComponent = models.TextField(null=True, blank=True)


class NsInstanceSubscriptionFilter(models.Model):
    nsInstanceSubscriptionFilter = models.OneToOneField(
        LifecycleChangeNotificationsFilter, on_delete=models.CASCADE, primary_key=True,
        related_name='lccn_subscription_filter_fk_filter')
    nsdIds = models.TextField(null=True, blank=True)
    vnfdIds = models.TextField(null=True, blank=True)
    pnfdIds = models.TextField(null=True, blank=True)
    nsInstanceIds = models.TextField(null=True, blank=True)
    nsInstanceNames = models.TextField(null=True, blank=True)
