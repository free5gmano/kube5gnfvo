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


class NsdInfo(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    nsdId = models.TextField(null=True, blank=True)
    nsdName = models.TextField(null=True, blank=True)
    nsdVersion = models.TextField(null=True, blank=True)
    nsdDesigner = models.TextField(null=True, blank=True)
    nsdInvariantId = models.TextField(null=True, blank=True)
    vnfPkgIds = models.TextField(null=True, blank=True)
    pnfdInfoIds = models.TextField(null=True, blank=True)
    nestedNsdInfoIds = models.TextField(null=True, blank=True)
    nsdOnboardingState = models.TextField(default="CREATED")
    nsdOperationalState = models.TextField(default="DISABLED")
    nsdUsageState = models.TextField(default="NOT_IN_USE")
    userDefinedData = models.TextField(null=True, blank=True)


class NsdInfoProblemDetails(models.Model):
    onboardingFailureDetails = models.OneToOneField(NsdInfo,
                                                    null=True,
                                                    blank=True,
                                                    on_delete=models.CASCADE,
                                                    related_name='nsd_info_fk_problem_details')
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    type = models.URLField(null=True, blank=True)
    title = models.TextField(null=True, blank=True)
    status = models.IntegerField()
    detail = models.TextField()
    instance = models.URLField(null=True, blank=True)


class NsdInfoLinks(models.Model):
    _links = models.OneToOneField(NsdInfo,
                                  on_delete=models.CASCADE,
                                  primary_key=True,
                                  related_name='nsd_info_fk_link')
    link_self = models.URLField()
    nsd_content = models.URLField()
