from VnfPackageManagement.models import VnfPkgInfo
from utils.format_tools import randomString
from utils.process_package.process_vnf_instance import ProcessVNFInstance


def get_vnf_Instance(vnf_pkg_ids) -> list:
    vnf_instances = list()
    for vnf_pkg_id in vnf_pkg_ids:
        vnf_package_info = VnfPkgInfo.objects.filter(id=vnf_pkg_id).last()
        vnfd_id = vnf_package_info.vnfdId.lower()
        vnf_instance_name = '{}-{}'.format(vnfd_id, randomString())
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
