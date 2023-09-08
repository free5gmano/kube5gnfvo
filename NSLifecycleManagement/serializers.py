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
import json

from rest_framework import serializers

from utils.format_tools import transform_representation
from .models import *


class NsCpHandleSerializer(serializers.ModelSerializer):
    class Meta:
        model = NsCpHandle
        fields = ('vnfInstanceId', 'vnfExtCpInstanceId')


class VnffgInfoSerializer(serializers.ModelSerializer):
    nsCpHandle = NsCpHandleSerializer(many=True, required=False,
                                      source='VnffgInfo_NsCpHandle')

    class Meta:
        model = VnffgInfo
        fields = ('id', 'vnffgdId', 'vnfInstanceId', 'nsVirtualLinkInfoId', 'nsCpHandle')

    def to_representation(self, instance):
        return transform_representation(super().to_representation(instance))


class ExtLinkPortInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExtLinkPortInfo
        fields = ('id', 'cpInstanceId')
        ref_name = 'NsInstanceSerializer_ExtLinkPortInfoSerializer'


class ExtVirtualLinkInfoSerializer(serializers.ModelSerializer):
    extLinkPorts = ExtLinkPortInfoSerializer(many=True, required=False,
                                             source='ExtVirtualLinkInfo_ExtLinkPortInfo')

    class Meta:
        model = ExtVirtualLinkInfo
        fields = ('id', 'extLinkPorts')
        ref_name = 'NsInstanceSerializer_ExtVirtualLinkInfoSerializer'


class IpAddressesSerializer(serializers.ModelSerializer):
    class Meta:
        model = IpAddresses
        fields = ('type', 'addresses', 'isDynamic')


class IpOverEthernetAddressInfoSerializer(serializers.ModelSerializer):
    ipAddresses = IpAddressesSerializer(
        many=True, required=False, source='IpOverEthernetAddressInfo_IpAddresses')

    class Meta:
        model = IpOverEthernetAddressInfo
        fields = ('ipAddresses',)


class CpProtocolInfoSerializer(serializers.ModelSerializer):
    ipOverEthernet = IpOverEthernetAddressInfoSerializer(
        required=False, source='CpProtocolInfo_IpOverEthernetAddressInfo')

    class Meta:
        model = CpProtocolInfo
        fields = ('layerProtocol', 'ipOverEthernet')


class VnfExtCpInfoSerializer(serializers.ModelSerializer):
    cpProtocolInfo = CpProtocolInfoSerializer(many=True, required=False,
                                              source='VnfExtCpInfo_CpProtocolInfo')

    class Meta:
        model = VnfExtCpInfo
        fields = ('id', 'cpdId', 'cpProtocolInfo')


class NsInstanceLinksSerializer(serializers.ModelSerializer):
    self = serializers.CharField(source='link_self')

    class Meta:
        model = NsInstanceLinks
        fields = ('self', 'nestedNsInstances', 'instantiate', 'terminate', 'update', 'scale', 'heal')


class InstantiatedVnfInfoSerializer(serializers.ModelSerializer):
    extCpInfo = VnfExtCpInfoSerializer(many=True, required=False,
                                       source='InstantiatedVnfInfo_VnfExtCpInfo')
    extVirtualLinkInfo = ExtVirtualLinkInfoSerializer(many=True, required=False,
                                                      source='InstantiatedVnfInfo_ExtVirtualLinkInfo')

    class Meta:
        model = InstantiatedVnfInfo
        fields = ('vnfState', 'extCpInfo', 'extVirtualLinkInfo')


class VnfInstanceSerializer(serializers.ModelSerializer):
    instantiatedVnfInfo = InstantiatedVnfInfoSerializer(required=False,
                                                        source='VnfInstance_instantiatedVnfInfo')

    class Meta:
        model = VnfInstance
        fields = ('id', 'vnfInstanceName', 'vnfdId', 'vnfProvider', 'vnfProductName', 'vnfdVersion',
                  'vnfPkgId', 'instantiationState', 'instantiatedVnfInfo')


class NsInstanceSerializer(serializers.ModelSerializer):
    vnffgInfo = VnffgInfoSerializer(many=True, required=False, source='NsInstance_VnffgInfo')
    vnfInstance = VnfInstanceSerializer(many=True, required=False, source='NsInstance_VnfInstance')
    _links = NsInstanceLinksSerializer(required=False, source='NsInstance_links')

    class Meta:
        model = NsInstance
        fields = '__all__'

    def create(self, validated_data):
        link_value = validated_data.pop('NsInstance_links')
        vnf_instance_dict = validated_data.pop('NsInstance_VnfInstance', dict())
        vnffg_info_list = validated_data.pop('NsInstance_VnffgInfo', list())
        ns = NsInstance.objects.create(**validated_data)
        NsInstanceLinks.objects.create(
            _links=ns, **{'link_self': link_value['link_self'] + str(ns.id)})
        vnffg_vl_id = list()
        for vnf_Instance_value in vnf_instance_dict:
            instantiated_vnf_info = vnf_Instance_value.pop('VnfInstance_instantiatedVnfInfo')
            vnf_instance = VnfInstance.objects.create(**vnf_Instance_value)
            ext_cp_info_dict = instantiated_vnf_info.pop('InstantiatedVnfInfo_VnfExtCpInfo')
            instantiated_vnf_info = InstantiatedVnfInfo.objects.create(
                instantiatedVnfInfo=vnf_instance, **instantiated_vnf_info)
            for ext_cp_info in ext_cp_info_dict:
                cp_protocol_info_dict = ext_cp_info.pop('VnfExtCpInfo_CpProtocolInfo')
                vnf_ext_cp_info = VnfExtCpInfo.objects.create(
                    **{'extCpInfo': instantiated_vnf_info, **ext_cp_info})
                for cp_protocol_info in cp_protocol_info_dict:
                    ip_over_ethernet_address_info_dict = cp_protocol_info.pop(
                        'CpProtocolInfo_IpOverEthernetAddressInfo')
                    cp_protocol = CpProtocolInfo.objects.create(**cp_protocol_info)
                    ip_over_ethernet_address_info = IpOverEthernetAddressInfo.objects.create(
                        ipOverEthernet=cp_protocol)
                    for ip_over_ethernet_address in \
                            ip_over_ethernet_address_info_dict['IpOverEthernetAddressInfo_IpAddresses']:
                        ip_address_dict = {'type': ip_over_ethernet_address['type'],
                                           'isDynamic': ip_over_ethernet_address['isDynamic']}
                        if 'addresses' in ip_over_ethernet_address:
                            ip_address_dict['addresses'] = ip_over_ethernet_address['addresses']
                        ip_address = IpAddresses.objects.create(**ip_address_dict)
                        ip_over_ethernet_address_info.IpOverEthernetAddressInfo_IpAddresses.add(ip_address)
                    vnf_ext_cp_info.VnfExtCpInfo_CpProtocolInfo.add(cp_protocol)
                ext_virtual_link_info = ExtVirtualLinkInfo.objects.create()
                ext_link_port_info = ExtLinkPortInfo.objects.create(**{"cpInstanceId": vnf_ext_cp_info.id})
                ext_virtual_link_info.ExtVirtualLinkInfo_ExtLinkPortInfo.add(ext_link_port_info)
                instantiated_vnf_info.InstantiatedVnfInfo_ExtVirtualLinkInfo.add(ext_virtual_link_info)
            ns.NsInstance_VnfInstance.add(vnf_instance)

            for vnffg in vnffg_info_list:
                if isinstance(vnffg['vnfInstanceId'], str):
                    vnffg['vnfInstanceId'] = json.loads(vnffg['vnfInstanceId'])

                if vnf_Instance_value['vnfdId'] in vnffg['vnfInstanceId']:
                    vnffg['vnfInstanceId'].append(str(vnf_instance.id))
                    vnffg['vnfInstanceId'].remove(vnf_Instance_value['vnfdId'])
                    cp = instantiated_vnf_info.InstantiatedVnfInfo_VnfExtCpInfo.all()
                    for cp_info in cp:
                        for ns_cp_handle in vnffg['VnffgInfo_NsCpHandle']:
                            if ns_cp_handle['vnfExtCpInstanceId'] == cp_info.cpdId:
                                ns_cp_handle['vnfExtCpInstanceId'] = cp_info.id
                                for vnf_vl in instantiated_vnf_info.InstantiatedVnfInfo_ExtVirtualLinkInfo.all():
                                    for vl_port in vnf_vl.ExtVirtualLinkInfo_ExtLinkPortInfo.all():
                                        if vl_port.cpInstanceId == str(cp_info.id):
                                            vnffg_vl_id.append(str(vnf_vl.id))
                                            break
                                ns_cp_handle['vnfInstanceId'] = vnf_instance.id
                                break

        for vnffg in vnffg_info_list:
            ns_cp_handle_list = vnffg.pop('VnffgInfo_NsCpHandle')
            vnffg['vnfInstanceId'] = json.dumps(vnffg['vnfInstanceId'])
            vnffg['nsVirtualLinkInfoId'] = json.dumps(vnffg_vl_id)
            vnffgd_info = VnffgInfo.objects.create(**vnffg)
            for ns_cp_handle in ns_cp_handle_list:
                NsCpHandle.objects.create(vnffgInfo_nsCpHandle=vnffgd_info, **ns_cp_handle)
            ns.NsInstance_VnffgInfo.add(vnffgd_info)

        return ns

    def update(self, instance, validated_data):
        return super().update(instance, validated_data)
