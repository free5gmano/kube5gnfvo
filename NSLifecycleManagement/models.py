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


class NsInstance(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    nsInstanceName = models.TextField()
    nsInstanceDescription = models.TextField()
    nsdId = models.TextField()
    nsdInfoId = models.TextField()
    flavourId = models.TextField(null=True, blank=True)
    nestedNsInstanceId = models.TextField(null=True, blank=True)
    nsState = models.TextField(default='NOT_INSTANTIATED')


class VnfInstance(models.Model):
    vnfInstance = models.ForeignKey(NsInstance,
                                    null=True,
                                    blank=True,
                                    on_delete=models.CASCADE,
                                    related_name='NsInstance_VnfInstance')
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    vnfInstanceName = models.TextField(null=True, blank=True)
    vnfInstanceDescription = models.TextField(null=True, blank=True)
    vnfdId = models.TextField()
    vnfProvider = models.TextField()
    vnfProductName = models.TextField()
    vnfSoftwareVersion = models.TextField()
    vnfdVersion = models.TextField()
    vnfPkgId = models.TextField()
    vnfConfigurableProperties = models.TextField(null=True, blank=True)
    vimId = models.TextField(null=True, blank=True)
    instantiationState = models.TextField(default='NOT_INSTANTIATED')
    metadata = models.TextField(null=True, blank=True)
    extensions = models.TextField(null=True, blank=True)


class SapInfo(models.Model):
    vnfInstance = models.ForeignKey(NsInstance, null=True, blank=True, on_delete=models.CASCADE,
                                    related_name='NsInstance_SapInfo')
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    sapdId = models.TextField()
    sapName = models.TextField()
    description = models.TextField()


class NsMonitoringParame(models.Model):
    monitoringParameter = models.ForeignKey(NsInstance, null=True, blank=True, on_delete=models.CASCADE,
                                            related_name='NsInstance_NsMonitoringParame')
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.TextField(null=True, blank=True)
    performanceMetric = models.TextField()


class NsScaleInfo(models.Model):
    nsScaleStatus = models.ForeignKey(NsInstance,
                                      null=True,
                                      blank=True,
                                      on_delete=models.CASCADE,
                                      related_name='NsInstance_NsScaleInfo')
    nsScalingAspectId = models.TextField()
    nsScaleLevelId = models.TextField()


class NsInstanceLinks(models.Model):
    _links = models.OneToOneField(NsInstance,
                                  on_delete=models.CASCADE,
                                  primary_key=True,
                                  related_name='NsInstance_links')
    link_self = models.URLField()
    nestedNsInstances = models.TextField(null=True, blank=True)
    instantiate = models.URLField(null=True, blank=True)
    terminate = models.URLField(null=True, blank=True)
    update = models.URLField(null=True, blank=True)
    scale = models.URLField(null=True, blank=True)
    heal = models.URLField(null=True, blank=True)


class AffinityOrAntiAffinityRule(models.Model):
    additionalAffinityOrAntiAffinityRule = models.ForeignKey(NsInstance,
                                                             null=True,
                                                             blank=True,
                                                             on_delete=models.CASCADE,
                                                             related_name='NsInstance_AffinityOrAntiAffinityRule')
    vnfdId = models.TextField(null=True, blank=True)
    vnfProfiledld = models.TextField()
    vnfInstancedId = models.TextField(null=True, blank=True)
    affinityOrAntiAffinity = models.TextField()
    scope = models.TextField()


class InstantiatedVnfInfo(models.Model):
    instantiatedVnfInfo = models.OneToOneField(VnfInstance,
                                               on_delete=models.CASCADE,
                                               primary_key=True,
                                               related_name='VnfInstance_instantiatedVnfInfo')
    flavourId = models.TextField(null=True, blank=True)
    vnfState = models.TextField(default='STOPPED')
    localizationLanguage = models.TextField(null=True, blank=True)


class VnfScaleInfo(models.Model):
    scaleStatus = models.ForeignKey(InstantiatedVnfInfo,
                                    null=True,
                                    blank=True,
                                    on_delete=models.CASCADE,
                                    related_name='InstantiatedVnfInfo_VnfScaleInfo')

    aspectlId = models.TextField()
    scaleLevel = models.TextField()


class VnfExtCpInfo(models.Model):
    extCpInfo = models.ForeignKey(InstantiatedVnfInfo, on_delete=models.CASCADE,
                                  related_name='InstantiatedVnfInfo_VnfExtCpInfo')
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    cpdId = models.TextField()
    extLinkPortId = models.TextField()
    metadata = models.TextField()
    associatedVnfcCpId = models.TextField()
    associatedVnfVirtualLinkId = models.TextField()


class ExtVirtualLinkInfo(models.Model):
    extVirtualLinkInfo = models.ForeignKey(InstantiatedVnfInfo, null=True, blank=True, on_delete=models.CASCADE,
                                           related_name='InstantiatedVnfInfo_ExtVirtualLinkInfo')
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)


class ExtLinkPortInfo(models.Model):
    extLinkPorts = models.ForeignKey(ExtVirtualLinkInfo, null=True, blank=True, on_delete=models.CASCADE,
                                     related_name='ExtVirtualLinkInfo_ExtLinkPortInfo')
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    cpInstanceId = models.TextField(null=True, blank=True)


class ExtManagedVirtualLinkInfo(models.Model):
    extManagedVirtualLinkInfo = models.ForeignKey(
        InstantiatedVnfInfo, null=True, blank=True, on_delete=models.CASCADE,
        related_name='InstantiatedVnfInfo_ExtManagedVirtualLinkInfo')
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    vnfVirtualLinkDescId = models.TextField()


class VnfMonitoringParamet(models.Model):
    monitoringParameters = models.ForeignKey(InstantiatedVnfInfo, null=True, blank=True, on_delete=models.CASCADE,
                                             related_name='InstantiatedVnfInfo_VnfMonitoringParamet')
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.TextField(null=True, blank=True)
    performanceMetric = models.TextField()


class VnfcResourceInfo(models.Model):
    vnfcResourceInfo = models.ForeignKey(InstantiatedVnfInfo, null=True, blank=True, on_delete=models.CASCADE,
                                         related_name='InstantiatedVnfInfo_VnfcResourceInfo')
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    vduId = models.TextField()
    storageResourceIds = models.TextField()
    reservationId = models.TextField()
    metadata = models.TextField()


class VnfcCpInfo(models.Model):
    vnfcCpInfo = models.ForeignKey(VnfcResourceInfo, null=True, blank=True, on_delete=models.CASCADE,
                                   related_name='VnfcResourceInfo_vnfcResourceInfo')
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    cpdId = models.TextField()
    vnfExtCpId = models.TextField(null=True, blank=True)
    vnfLinkPortId = models.TextField(null=True, blank=True)
    metadata = models.TextField(null=True, blank=True)


class CpProtocolInfo(models.Model):
    sapInfo_cpProtocolInfo = models.ForeignKey(SapInfo, on_delete=models.CASCADE, null=True, blank=True,
                                               related_name='SapInfo_CpProtocolInfo')
    vnfExtCpInfo_cpProtocolInfo = models.ForeignKey(VnfExtCpInfo, on_delete=models.CASCADE, null=True, blank=True,
                                                    related_name='VnfExtCpInfo_CpProtocolInfo')
    vnfcCpInfo_cpProtocolInfo = models.ForeignKey(VnfcCpInfo, on_delete=models.CASCADE, null=True, blank=True,
                                                  related_name='VnfcCpInfo_CpProtocolInfo')
    layerProtocol = models.TextField()


class IpOverEthernetAddressInfo(models.Model):
    ipOverEthernet = models.OneToOneField(CpProtocolInfo, primary_key=True, on_delete=models.CASCADE,
                                          related_name='CpProtocolInfo_IpOverEthernetAddressInfo')
    macAddress = models.TextField(null=True, blank=True)


class IpAddresses(models.Model):
    ipAddresses = models.ForeignKey(IpOverEthernetAddressInfo, null=True, blank=True, on_delete=models.CASCADE,
                                    related_name='IpOverEthernetAddressInfo_IpAddresses')
    type = models.TextField()
    addresses = models.TextField(null=True, blank=True)
    isDynamic = models.BooleanField(null=True, blank=True)
    subnetId = models.TextField(null=True, blank=True)


class AddressRange(models.Model):
    addressRange = models.OneToOneField(IpAddresses, on_delete=models.CASCADE, primary_key=True,
                                        related_name='IpAddresses_AddressRange')
    minAddress = models.TextField()
    maxAddress = models.TextField()


class VnfVirtualLinkResourceInfo(models.Model):
    vnfVirtualLinkResourceInfo = models.ForeignKey(InstantiatedVnfInfo, null=True, blank=True, on_delete=models.CASCADE,
                                                   related_name='InstantiatedVnfInfo_VnfVirtualLinkResourceInfo')
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    vnfVirtualLinkDescId = models.TextField()
    reservationId = models.TextField()
    metadata = models.TextField()


class VnfLinkPortInfo(models.Model):
    vnfVirtualLinkResourceInfo_vnfLinkPorts = models.ForeignKey(
        VnfVirtualLinkResourceInfo, null=True, blank=True,
        on_delete=models.CASCADE,
        related_name='VnfVirtualLinkResourceInfo_VnfLinkPortInfo')
    extManagedVirtualLinkInfo_vnfLinkPorts = models.ForeignKey(
        ExtManagedVirtualLinkInfo, null=True, blank=True,
        on_delete=models.CASCADE,
        related_name='ExtManagedVirtualLinkInfo_VnfLinkPortInfo')
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    cpInstanceId = models.TextField(null=True, blank=True)
    cpInstanceType = models.TextField(null=True, blank=True)


class VirtualStorageResourceInfo(models.Model):
    virtualStorageResourceInfo = models.ForeignKey(InstantiatedVnfInfo, null=True, blank=True, on_delete=models.CASCADE,
                                                   related_name='InstantiatedVnfInfo_VirtualStorageResourceInfo')
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    virtualStorageDescId = models.TextField()
    reservationId = models.TextField(null=True, blank=True)
    metadata = models.TextField(null=True, blank=True)


class NsVirtualLinkInfo(models.Model):
    virtualLinkInfo = models.ForeignKey(NsInstance, null=True, blank=True, on_delete=models.CASCADE,
                                        related_name='NsInstance_virtualLinkInfo')
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    nsVirtualLinkDescId = models.TextField()
    nsVirtualLinkProfileld = models.TextField()


class NsLinkPortInfo(models.Model):
    linkPort = models.ForeignKey(NsVirtualLinkInfo, null=True, blank=True, on_delete=models.CASCADE,
                                 related_name='NsVirtualLinkInfo_NsLinkPortInfo')
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)


class VnffgInfo(models.Model):
    vnffgInfo = models.ForeignKey(NsInstance, null=True, blank=True, on_delete=models.CASCADE,
                                  related_name='NsInstance_VnffgInfo')
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    vnffgdId = models.TextField()
    vnfInstanceId = models.TextField(null=True, blank=True)
    nsVirtualLinkInfoId = models.TextField(null=True, blank=True)


class NfpInfo(models.Model):
    nfpInfo = models.ForeignKey(VnffgInfo, null=True, blank=True, on_delete=models.CASCADE,
                                related_name='VnffgInfo_NfpInfo')
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    nfpdId = models.TextField(null=True, blank=True)
    nfpName = models.TextField(null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    totalCp = models.TextField(null=True, blank=True)
    nfpState = models.TextField()


class CpGroupInfo(models.Model):
    cpGroup = models.ForeignKey(NfpInfo, on_delete=models.CASCADE,
                                related_name='NfpInfo_CpGroupInfo')
    forwardingBehaviour = models.TextField(null=True, blank=True)


class NfpRule(models.Model):
    nfpRule = models.OneToOneField(NfpInfo, on_delete=models.CASCADE,
                                   related_name='NfpInfo_nfpRule')
    etherDestinationAddress = models.TextField(null=True, blank=True)
    etherSourceAddress = models.TextField(null=True, blank=True)
    etherType = models.TextField(null=True, blank=True)
    vlanTag = models.TextField(null=True, blank=True)
    protocol = models.TextField(null=True, blank=True)
    dscp = models.TextField(null=True, blank=True)
    sourceIpAddressPrefix = models.TextField(null=True, blank=True)
    destinationIpAddressPrefix = models.TextField(null=True, blank=True)


class PortRange(models.Model):
    sourcePortRange = models.OneToOneField(
        NfpRule, on_delete=models.CASCADE, null=True,
        related_name='NfpRule_SourcePortRange')
    destinationPortRange = models.OneToOneField(
        NfpRule, on_delete=models.CASCADE, null=True,
        related_name='NfpRule_DestinationPortRange')
    lowerPort = models.IntegerField()
    upperPort = models.IntegerField()


class Mask(models.Model):
    extendedCriteria = models.ForeignKey(NfpRule, on_delete=models.CASCADE,
                                         related_name='NfpInfo_Mask')
    startingPoint = models.IntegerField()
    length = models.IntegerField()
    value = models.TextField()


class CpPairInfo(models.Model):
    cpGroup = models.ForeignKey(CpGroupInfo, on_delete=models.CASCADE,
                                related_name='CpGroupInfo_CpPairInfo')
    vnfExtCpIds = models.TextField(null=True, blank=True)
    sapIds = models.TextField(null=True, blank=True)


class ForwardingBehaviourInputParameters(models.Model):
    nsLinkPortInfo_nsCpHandle = models.OneToOneField(
        CpGroupInfo, on_delete=models.CASCADE, primary_key=True,
        related_name='CpGroupInfo_ForwardingBehaviourInputParameters')
    algortihmName = models.TextField(null=True, blank=True)
    algorithmWeights = models.IntegerField(null=True, blank=True)


class NsCpHandle(models.Model):
    vnffgInfo_nsCpHandle = models.ForeignKey(VnffgInfo, on_delete=models.CASCADE,
                                             related_name='VnffgInfo_NsCpHandle')
    nsLinkPortInfo_nsCpHandle = models.OneToOneField(
        NsLinkPortInfo, null=True, blank=True, unique=True, on_delete=models.CASCADE,
        related_name='NsLinkPortInfo_NsCpHandle')
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    vnfInstanceId = models.TextField(null=True, blank=True)
    vnfExtCpInstanceId = models.TextField(null=True, blank=True)
    nsInstanceId = models.TextField(null=True, blank=True)
    nsSapInstanceId = models.TextField(null=True, blank=True)


class ResourceHandle(models.Model):
    nsLinkPortInfo_resourceHandle = models.OneToOneField(
        NsLinkPortInfo, on_delete=models.CASCADE, null=True, blank=True, unique=True,
        related_name='NsLinkPortInfo_ResourceHandle')
    nsVirtualLinkInfo_resourceHandle = models.ForeignKey(
        NsVirtualLinkInfo, on_delete=models.CASCADE, null=True, blank=True,
        related_name='NsVirtualLinkInfo_ResourceHandle')
    virtualStorageResourceInfo_storageResource = models.OneToOneField(
        VnfLinkPortInfo, on_delete=models.CASCADE, null=True, blank=True, unique=True,
        related_name='VirtualStorageResourceInfo_ResourceHandle')
    vnfVirtualLinkResourceInfo_networkResource = models.OneToOneField(
        VnfLinkPortInfo, on_delete=models.CASCADE, null=True, blank=True, unique=True,
        related_name='VnfVirtualLinkResourceInfo_ResourceHandle')
    vnfcResourceInfo_computeResource = models.OneToOneField(VnfLinkPortInfo, on_delete=models.CASCADE, null=True,
                                                            blank=True, unique=True,
                                                            related_name='VnfcResourceInfo_ResourceHandle')
    vnfLinkPortInfo_resourceHandle = models.OneToOneField(VnfLinkPortInfo, on_delete=models.CASCADE, null=True,
                                                          blank=True, unique=True,
                                                          related_name='VnfLinkPortInfo_ResourceHandle')
    extVirtualLinkInfo_resourceHandle = models.OneToOneField(ExtVirtualLinkInfo, on_delete=models.CASCADE, null=True,
                                                             blank=True,
                                                             unique=True,
                                                             related_name='ExtVirtualLinkInfo_ResourceHandle')
    extLinkPortInfo_resourceHandle = models.OneToOneField(ExtLinkPortInfo, null=True, blank=True, unique=True,
                                                          on_delete=models.CASCADE,
                                                          related_name='ExtLinkPortInfo_ResourceHandle')
    extManagedVirtualLinkInfo_networkResource = models.OneToOneField(
        ExtManagedVirtualLinkInfo,
        on_delete=models.CASCADE, null=True, blank=True,
        unique=True,
        related_name='ExtManagedVirtualLinkInfo_ResourceHandle')
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    vimId = models.TextField(null=True, blank=True)
    resourceProviderId = models.TextField(null=True, blank=True)
    resourceId = models.TextField()
    vimLevelResourceType = models.TextField(null=True, blank=True)
