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


class NsLcmOpOcc(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    operationState = models.TextField(default='PROCESSING')
    statusEnteredTime = models.DateTimeField()
    nsInstanceId = models.TextField()
    lcmOperationType = models.TextField()
    startTime = models.DateField(auto_now_add=True, editable=False)
    isAutomaticInvocation = models.BooleanField()
    operationParams = models.TextField(null=True, blank=True)
    isCancelPending = models.BooleanField()
    cancelMode = models.TextField(null=True, blank=True)
    error = models.TextField(null=True, blank=True)


class ResourceChanges(models.Model):
    resourceChanges = models.OneToOneField(NsLcmOpOcc,
                                           on_delete=models.CASCADE,
                                           primary_key=True,
                                           related_name='resourceChanges')


class AffectedVnf(models.Model):
    affectedVnfs = models.ForeignKey(ResourceChanges,
                                     on_delete=models.CASCADE,
                                     related_name='affectedVnfs')
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    vnfInstanceId = models.TextField()
    vnfdId = models.TextField()
    vnfProfileId = models.TextField()
    vnfName = models.TextField()
    changeType = models.TextField()
    changeResult = models.TextField()


class AffectedVirtualLink(models.Model):
    affectedVl = models.ForeignKey(ResourceChanges,
                                   on_delete=models.CASCADE,
                                   related_name='affectedVl')
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    nsVirtualLinkInstanceId = models.TextField()
    nsVirtualLinkDescId = models.TextField()
    vlProfileId = models.TextField()
    changeType = models.TextField()
    changeResult = models.TextField()


class AffectedVnffg(models.Model):
    affectedVnffg = models.ForeignKey(ResourceChanges,
                                      on_delete=models.CASCADE,
                                      related_name='affectedVnffg')
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    vnffgInstanceId = models.TextField()
    vnffgdId = models.TextField()
    changeType = models.TextField()
    changeResult = models.TextField()


class AffectedNs(models.Model):
    affectedNss = models.ForeignKey(ResourceChanges,
                                    on_delete=models.CASCADE,
                                    related_name='affectedNss')
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    nsInstanceId = models.TextField()
    nsdId = models.TextField()
    changeType = models.TextField()
    changeResult = models.TextField()


class AffectedSap(models.Model):
    affectedSaps = models.ForeignKey(ResourceChanges,
                                     on_delete=models.CASCADE,
                                     related_name='affectedSaps')
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    sapInstanceId = models.TextField()
    sapdId = models.TextField()
    sapName = models.TextField()
    changeType = models.TextField()
    changeResult = models.TextField()


class Links(models.Model):
    _links = models.OneToOneField(NsLcmOpOcc,
                                  on_delete=models.CASCADE,
                                  primary_key=True,
                                  related_name='_links')
    link_self = models.URLField()
    nsInstance = models.URLField()
    cancel = models.URLField(null=True, blank=True)
    retry = models.URLField(null=True, blank=True)
    rollback = models.URLField(null=True, blank=True)
    _continue = models.URLField(null=True, blank=True)
    fail = models.URLField(null=True, blank=True)


class ChangedInfo(models.Model):
    changedInfo = models.OneToOneField(AffectedVnf,
                                       on_delete=models.CASCADE,
                                       primary_key=True,
                                       related_name='changedInfo')


class ModifyVnfInfoData(models.Model):
    changedVnfInfo = models.OneToOneField(ChangedInfo,
                                          on_delete=models.CASCADE,
                                          primary_key=True,
                                          related_name='changedVnfInfo')
    vnfInstanceId = models.TextField()
    vnfInstanceName = models.TextField(null=True, blank=True)
    vnfInstanceDescription = models.TextField(null=True, blank=True)
    vnfdId = models.TextField(null=True, blank=True)
    vnfConfigurableProperties = models.TextField(null=True, blank=True)
    metadata = models.TextField(null=True, blank=True)
    extensions = models.TextField(null=True, blank=True)


class ExtVirtualLinkInfo(models.Model):
    changedExtConnectivity = models.ForeignKey(ChangedInfo,
                                               on_delete=models.CASCADE,
                                               related_name='changedExtConnectivity')
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)


class ExtLinkPortInfo(models.Model):
    extLinkPorts = models.ForeignKey(ExtVirtualLinkInfo,
                                     on_delete=models.CASCADE,
                                     related_name='extLinkPorts')
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    cpInstanceId = models.TextField(null=True, blank=True)


class ResourceHandle(models.Model):
    resourceHandle = models.OneToOneField(ExtVirtualLinkInfo,
                                          on_delete=models.CASCADE,
                                          related_name='resourceHandle')
    vimId = models.TextField(null=True, blank=True)
    resourceProviderId = models.TextField(null=True, blank=True)
    resourceId = models.TextField()
    vimLevelResourceType = models.TextField(null=True, blank=True)
