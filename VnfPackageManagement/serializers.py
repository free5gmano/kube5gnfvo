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

import os

from rest_framework import serializers
from VnfPackageManagement.models import *
from utils.file_manipulation import create_dir
from utils.format_tools import transform_representation

vnf_package_base_path = os.getcwd() + "/VnfPackage/"
create_dir(vnf_package_base_path)


class VnfPkgInfoLinksSerializer(serializers.ModelSerializer):
    self = serializers.CharField(source='link_self')

    class Meta:
        model = VnfPkgInfoLinks
        fields = ('self', 'vnfd', 'packageContent')


class ChecksumSerializer(serializers.ModelSerializer):
    class Meta:
        model = Checksum
        fields = ('algorithm', 'hash')


class VnfPackageArtifactInfoSerializer(serializers.ModelSerializer):
    checksum = ChecksumSerializer(source='vnf_package_artifact_info_fk_checksum')

    class Meta:
        model = VnfPackageArtifactInfo
        fields = ('artifactPath', 'checksum')


class VnfPackageSoftwareImageInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = VnfPackageSoftwareImageInfo
        fields = ('id', 'name', 'provider', 'version', 'containerFormat', 'diskFormat', 'createdAt',
                  'minDisk', 'minRam', 'size', 'userMetadata', 'imagePath')

    def to_representation(self, instance):
        return transform_representation(super().to_representation(instance))


class VnfPkgInfoSerializer(serializers.ModelSerializer):
    checksum = ChecksumSerializer(required=False, source='vnf_package_info_fk_checksum')
    _links = VnfPkgInfoLinksSerializer(required=False, source='vnf_package_info_fk_link')
    additionalArtifacts = VnfPackageArtifactInfoSerializer(many=True, required=False,
                                                           source='vnf_package_info_fk_artifactInfo')
    softwareImages = VnfPackageSoftwareImageInfoSerializer(many=True, required=False,
                                                           source='vnf_package_info_fk_software_image_info')

    class Meta:
        model = VnfPkgInfo
        fields = '__all__'

    def to_representation(self, instance):
        return transform_representation(super().to_representation(instance))

    def create(self, validated_data):
        link_value = validated_data.pop('vnf_package_info_fk_link')
        vnf_package_info = VnfPkgInfo.objects.create(**validated_data)
        path_content = ['vnfd', 'package_content']

        for dir_name in path_content:
            create_dir('{}{}/{}'.format(vnf_package_base_path, vnf_package_info.id, dir_name))

        VnfPkgInfoLinks.objects.create(
            _links=vnf_package_info,
            **{'link_self': '{}{}'.format(link_value['link_self'], vnf_package_info.id),
               'vnfd': '{}{}/{}'.format(link_value[path_content[0]], vnf_package_info.id, path_content[0]),
               'packageContent': '{}{}/{}'.format(link_value['packageContent'], vnf_package_info.id, path_content[1])})
        return vnf_package_info

    def update(self, instance, validated_data):
        if 'operationalState' in validated_data and 'userDefinedData' in validated_data:
            instance.operationalState = validated_data['operationalState']
            instance.userDefinedData = validated_data['userDefinedData']
            instance.save()
        else:
            instance.vnfdId = validated_data['vnfdId']
            instance.vnfProvider = validated_data['vnfProvider']
            instance.vnfProductName = validated_data['vnfProductName']
            instance.vnfdVersion = validated_data['vnfdVersion']
            instance.vnfSoftwareVersion = validated_data['vnfSoftwareVersion']
            Checksum.objects.create(vnf_package_info_fk_checksum=instance,
                                    **validated_data['vnf_package_info_fk_checksum'])

            if 'vnf_package_info_fk_artifactInfo' in validated_data:
                for vnf_pacakge_artifact in validated_data['vnf_package_info_fk_artifactInfo']:
                    checksum = vnf_pacakge_artifact.pop('vnf_package_artifact_info_fk_checksum')
                    additional_artifacts = VnfPackageArtifactInfo.objects.create(**vnf_pacakge_artifact)
                    Checksum.objects.create(vnf_package_artifact_info_fk_checksum=additional_artifacts,
                                            **checksum),
                    instance.vnf_package_info_fk_artifactInfo.add(additional_artifacts)

            for software_image_info_value in validated_data['vnf_package_info_fk_software_image_info']:
                software_image_info = VnfPackageSoftwareImageInfo.objects.create(
                    **software_image_info_value)
                instance.vnf_package_info_fk_software_image_info.add(software_image_info)

            instance.onboardingState = 'ONBOARDED'
            instance.operationalState = 'ENABLED'
            instance.usageState = 'NOT_IN_USE'
            instance.save()

        return instance
