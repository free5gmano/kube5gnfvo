from functools import partial
from NSDManagement.models import NsdInfo
from NSLCMOperationOccurrences.models import NsLcmOpOcc
from NSLifecycleManagement.models import NsInstance
from VIMManagement.utils.monitor_deployment import MonitorDeployment
from VnfPackageManagement.models import VnfPkgInfo


class MonitorVnf(object):
    lcm_operation = (instantiate, scale, heal, update, terminate) = (
        'INSTANTIATE', 'Scale', 'Heal', 'Update', 'TERMINATE')

    def __init__(self):
        self.monitor_deployment = MonitorDeployment()

    def monitoring_vnf(self, ns_instance_id, lcm_operation_type, usage_state, **kwargs):
        completed_events = [partial(self.set_state, ns_id=ns_instance_id, lcm_operation_type=lcm_operation_type,
                                    usage_state=usage_state)]

        container_list = list()
        for vnf_instance in kwargs['vnf_instances']:
            vnf_package = VnfPkgInfo.objects.filter(id=vnf_instance.vnfPkgId).last()
            if vnf_package.vnf_package_info_fk_software_image_info.last().diskFormat != 'qcow2':
                container_list.append(vnf_instance.vnfInstanceName.lower())
        self.monitor_deployment.watch_specific_deployment(
            container_list, kwargs['container_phase'], completed_events)

    def set_state(self, ns_id, lcm_operation_type, usage_state):
        ns_instance = NsInstance.objects.filter(id=ns_id).last()
        for vnf_instance in ns_instance.NsInstance_VnfInstance.all():
            vnf_package = VnfPkgInfo.objects.filter(id=vnf_instance.vnfPkgId).last()
            vnf_package.usageState = usage_state
            vnf_package.save()

        nsd_info = NsdInfo.objects.filter(id=ns_instance.nsdInfoId).last()
        nsd_info.nsdUsageState = usage_state
        nsd_info.save()

        ns_lcm_op_occ = NsLcmOpOcc.objects.filter(nsInstanceId=ns_id, lcmOperationType=lcm_operation_type).last()
        ns_lcm_op_occ.operationState = 'COMPLETED'
        ns_lcm_op_occ.save()
