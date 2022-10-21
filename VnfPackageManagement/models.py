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


class VnfPkgInfo(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    vnfdId = models.TextField(null=True, blank=True)
    vnfProvider = models.TextField(null=True, blank=True)
    vnfProductName = models.TextField(null=True, blank=True)
    vnfSoftwareVersion = models.TextField(null=True, blank=True)
    vnfdVersion = models.TextField(null=True, blank=True)
    onboardingState = models.TextField(default="CREATED")
    operationalState = models.TextField(default="DISABLED")
    usageState = models.TextField(default="NOT_IN_USE")
    userDefinedData = models.TextField(null=True, blank=True)


class VnfPackageArtifactInfo(models.Model):
    additionalArtifacts = models.ForeignKey(
        VnfPkgInfo,
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name='vnf_package_info_fk_artifactInfo')
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    artifactPath = models.TextField()
    metadata = models.TextField(null=True, blank=True)


class VnfPackageSoftwareImageInfo(models.Model):
    softwareImages = models.ForeignKey(
        VnfPkgInfo,
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name='vnf_package_info_fk_software_image_info')
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.TextField()
    provider = models.TextField()
    version = models.TextField()
    containerFormat = models.TextField(default="DOCKER")
    diskFormat = models.TextField(default="RAW")
    createdAt = models.DateTimeField(auto_now_add=True)
    minDisk = models.TextField(null=True, blank=True)
    minRam = models.TextField(null=True, blank=True)
    size = models.TextField(null=True, blank=True)
    userMetadata = models.TextField(null=True, blank=True)
    imagePath = models.TextField(null=True, blank=True)


class VnfPkgInfoLinks(models.Model):
    _links = models.OneToOneField(
        VnfPkgInfo,
        primary_key=True,
        on_delete=models.CASCADE,
        related_name='vnf_package_info_fk_link')
    link_self = models.URLField()
    vnfd = models.URLField()
    packageContent = models.URLField()


class Checksum(models.Model):
    vnf_package_info_fk_checksum = models.OneToOneField(
        VnfPkgInfo,
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name='vnf_package_info_fk_checksum')
    vnf_package_artifact_info_fk_checksum = models.OneToOneField(
        VnfPackageArtifactInfo,
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name='vnf_package_artifact_info_fk_checksum')
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    algorithm = models.TextField()
    hash = models.TextField()
