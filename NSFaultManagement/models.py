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
from enum import Enum, EnumMeta
from django.db import models
import uuid


class ChoiceEnumMeta(EnumMeta):

    def __getattribute__(cls, name):
        value = super().__getattribute__(name)
        if isinstance(value, Enum):
            return value.value
        return value

    def __iter__(self):
        return ((tag.name, tag.value) for tag in super().__iter__())


class FaultyResourceType(Enum, metaclass=ChoiceEnumMeta):
    COMPUTE = 'COMPUTE'
    STORAGE = 'STORAGE'
    NETWORK = 'NETWORK'


class AckState(Enum, metaclass=ChoiceEnumMeta):
    ACKNOWLEDGED = 'ACKNOWLEDGED'
    UNACKNOWLEDGED = 'UNACKNOWLEDGED'


class PerceivedSeverityType(Enum, metaclass=ChoiceEnumMeta):
    CRITICAL = 'CRITICAL'
    MAJOR = 'MAJOR'
    MINOR = 'MINOR'
    WARNING = 'WARNING'
    INDETERMINATE = 'INDETERMINATE'
    CLEARED = 'CLEARED'


class EventType(Enum, metaclass=ChoiceEnumMeta):
    COMMUNICATIONS_ALARM = 'COMMUNICATIONS_ALARM'
    PROCESSING_ERROR_ALARM = 'PROCESSING_ERROR_ALARM'
    ENVIRONMENTAL_ALARM = 'ENVIRONMENTAL_ALARM'
    QOS_ALARM = 'QOS_ALARM'
    EQUIPMENT_ALARM = 'EQUIPMENT_ALARM'


class Alarm(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    managedObjectId = models.TextField()
    alarmRaisedTime = models.TimeField(auto_now_add=True)
    alarmChangedTime = models.TimeField(null=True, blank=True)
    alarmClearedTime = models.TimeField(null=True, blank=True)
    alarmAcknowledgedTime = models.TimeField(null=True, blank=True)
    ackState = models.CharField(max_length=20, choices=AckState, default='UNACKNOWLEDGED')
    perceivedSeverity = models.CharField(max_length=20, choices=PerceivedSeverityType, default='CRITICAL')
    eventTime = models.TimeField(auto_now_add=True)
    eventType = models.CharField(max_length=30, choices=EventType, default='PROCESSING_ERROR_ALARM')
    faultType = models.TextField(null=True, blank=True)
    probableCause = models.TextField(null=True, blank=True)
    isRootCause = models.BooleanField(default=False)
    correlatedAlarmIds = models.TextField(null=True, blank=True)
    faultDetails = models.TextField(null=True, blank=True)


class FaultyComponentInfo(models.Model):
    rootCauseFaultyComponent = models.OneToOneField(
        Alarm, null=True, blank=True, on_delete=models.CASCADE, related_name='alarm_fk_root_cause_faulty_component')
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    faultyNestedNsInstanceId = models.UUIDField(null=True, blank=True)
    faultyNsVirtualLinkInstanceId = models.TextField(null=True, blank=True)
    faultyVnfInstanceId = models.TextField(null=True, blank=True)


class FaultyResourceInfo(models.Model):
    rootCauseFaultyResource = models.OneToOneField(
        Alarm, null=True, blank=True, on_delete=models.CASCADE, related_name='alarm_fk_root_cause_faulty_resource')
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    faultyResourceType = models.CharField(
        max_length=10, choices=FaultyResourceType, null=True, blank=True, default='COMPUTE')


class ResourceHandle(models.Model):
    faultyResource = models.OneToOneField(
        FaultyResourceInfo, null=True, blank=True, on_delete=models.CASCADE,
        related_name='faulty_resource_info_fk_resource_handle')
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    vimId = models.TextField(null=True, blank=True)
    resourceProviderId = models.TextField(null=True, blank=True)
    resourceId = models.TextField()
    vimLevelResourceType = models.TextField(null=True, blank=True)


class AlarmLinks(models.Model):
    _links = models.OneToOneField(
        Alarm, on_delete=models.CASCADE, primary_key=True, related_name='alarm_fk_link')
    link_self = models.URLField()
    objectInstance = models.TextField()
