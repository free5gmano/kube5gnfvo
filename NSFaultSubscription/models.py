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
from enum import Enum

from django.db import models
import uuid

from NSFaultManagement.models import FaultyResourceType, EventType, PerceivedSeverityType, ChoiceEnumMeta


class FmSubscription(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    callbackUri = models.TextField()


class FmSubscriptionLink(models.Model):
    _links = models.OneToOneField(
        FmSubscription, on_delete=models.CASCADE, primary_key=True,
        related_name='fm_subscription_fk_fm_subscription_link')
    link_self = models.URLField()


class NotificationTypes(Enum, metaclass=ChoiceEnumMeta):
    AlarmNotification = 'AlarmNotification'
    AlarmClearedNotification = 'AlarmClearedNotification'
    AlarmListRebuiltNotification = 'AlarmListRebuiltNotification'


class FmSubscriptionsFilter(models.Model):
    filter = models.OneToOneField(
        FmSubscription, on_delete=models.CASCADE, primary_key=True,
        related_name='fm_subscription_fk_fm_subscriptions_filter')
    notificationTypes = models.CharField(max_length=30, choices=NotificationTypes, null=True, blank=True)
    faultyResourceTypes = models.CharField(max_length=30, choices=FaultyResourceType, null=True, blank=True)
    perceivedSeverities = models.CharField(max_length=30, choices=PerceivedSeverityType, null=True, blank=True)
    eventTypes = models.CharField(max_length=30, choices=EventType, null=True, blank=True)
    probableCauses = models.TextField(null=True, blank=True)


class NsInstanceSubscriptionFilter(models.Model):
    nsInstanceSubscriptionFilter = models.OneToOneField(
        FmSubscriptionsFilter, on_delete=models.CASCADE, primary_key=True,
        related_name='fm_subscription_filter_fk_ns_instance_subscription_filter')
    nsdIds = models.TextField(null=True, blank=True)
    vnfdIds = models.TextField(null=True, blank=True)
    pnfdIds = models.TextField(null=True, blank=True)
    nsInstanceIds = models.TextField(null=True, blank=True)
    nsInstanceNames = models.TextField(null=True, blank=True)
