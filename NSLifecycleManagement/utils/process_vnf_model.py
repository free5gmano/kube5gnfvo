from NSLifecycleManagement.models import VnfInstance, InstantiatedVnfInfo, VnfExtCpInfo, CpProtocolInfo, \
    IpOverEthernetAddressInfo, IpAddresses, ExtVirtualLinkInfo, ExtLinkPortInfo
from VnfPackageManagement.models import VnfPkgInfo
from utils.format_tools import random_string
from utils.process_package.process_vnf_instance import ProcessVNFInstance


def get_vnf_instance(vnf_pkg_ids) -> list:
    vnf_instances = list()
    for vnf_pkg_id in vnf_pkg_ids:
        vnf_package_info = VnfPkgInfo.objects.filter(id=vnf_pkg_id).last()
        vnfd_id = vnf_package_info.vnfdId.lower()
        vnf_instance_name = '{}-{}'.format(vnfd_id, random_string())
        process_vnf_instance = ProcessVNFInstance(vnf_pkg_id, vnf_instance_name=vnf_instance_name)
        ext_cp_info = process_vnf_instance.process_template()
        vnf_instances.append({'vnfdId': vnf_package_info.vnfdId,
                              'vnfInstanceName': vnf_instance_name,
                              'vnfProvider': vnf_package_info.vnfProvider,
                              'vnfProductName': vnf_package_info.vnfProductName,
                              'vnfSoftwareVersion': vnf_package_info.vnfSoftwareVersion,
                              'vnfdVersion': vnf_package_info.vnfdVersion,
                              'vnfPkgId': vnf_pkg_id,
                              'metadata': vnf_package_info.userDefinedData,
                              'instantiatedVnfInfo': {'vnfState': 'STARTED',
                                                      'extCpInfo': ext_cp_info}})
    return vnf_instances


def create_vnf_instance(vnf_instance_value):
    instantiated_vnf_info = vnf_instance_value.pop('instantiatedVnfInfo')
    vnf_instance = VnfInstance.objects.create(**vnf_instance_value)
    ext_cp_info_dict = instantiated_vnf_info.pop('extCpInfo')
    instantiated_vnf_info = InstantiatedVnfInfo.objects.create(
        instantiatedVnfInfo=vnf_instance, **instantiated_vnf_info)
    for ext_cp_info in ext_cp_info_dict:
        cp_protocol_info_dict = ext_cp_info.pop('cpProtocolInfo')
        vnf_ext_cp_info = VnfExtCpInfo.objects.create(
            **{'extCpInfo': instantiated_vnf_info, **ext_cp_info})
        for cp_protocol_info in cp_protocol_info_dict:
            ip_over_ethernet_address_info_dict = cp_protocol_info.pop(
                'ipOverEthernet')
            cp_protocol = CpProtocolInfo.objects.create(**cp_protocol_info)
            ip_over_ethernet_address_info = IpOverEthernetAddressInfo.objects.create(
                ipOverEthernet=cp_protocol)
            for ip_over_ethernet_address in \
                    ip_over_ethernet_address_info_dict['ipAddresses']:
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
    return vnf_instance
