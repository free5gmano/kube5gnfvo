from functools import partial
from NSDManagement.models import NsdInfo
from NSLCMOperationOccurrences.models import NsLcmOpOcc
from NSLifecycleManagement.models import NsInstance
from VIMManagement.utils.monitor_deployment import MonitorDeployment
from VnfPackageManagement.models import VnfPkgInfo
from utils.notification_management.kafka_notification import KafkaNotification


class MonitorVnf(object):
    lcm_operation = (instantiate, scale, heal, update, terminate) = (
        'INSTANTIATE', 'Scale', 'Heal', 'Update', 'TERMINATE')

    def __init__(self):
        self.monitor_deployment = MonitorDeployment()
        self.kafka_notification = KafkaNotification('ns_instance')

    def monitoring_vnf(self, ns_instance_id, lcm_operation_type, ns_state, usage_state, **kwargs):
        completed_events = [
            partial(self.set_state, ns_instance_id=ns_instance_id, lcm_operation_type=lcm_operation_type,
                    ns_state=ns_state, usage_state=usage_state)]
        container_list = list()
        for vnf_instance in kwargs['vnf_instances']:
            container_list.append(vnf_instance.vnfInstanceName.lower())

        self.monitor_deployment.watch_specific_deployment(
            container_list, kwargs['container_phase'], completed_events)

    def set_state(self, ns_instance_id, lcm_operation_type, ns_state, usage_state):
        ns_instance = NsInstance.objects.filter(id=ns_instance_id).last()
        for vnf_instance in ns_instance.NsInstance_VnfInstance.all():
            if self.terminate == lcm_operation_type:
                vnf_instance.instantiationState = 'NOT_INSTANTIATED'
            else:
                vnf_instance.instantiationState = 'INSTANTIATED'
            vnf_instance.save()
            vnf_package = VnfPkgInfo.objects.filter(id=vnf_instance.vnfPkgId).last()
            vnf_package.usageState = usage_state
            vnf_package.save()

        nsd_info = NsdInfo.objects.filter(id=ns_instance.nsdInfoId).last()
        nsd_info.nsdUsageState = usage_state
        nsd_info.save()

        ns_instance.nsState = ns_state
        ns_instance.save()

        ns_lcm_op_occ = NsLcmOpOcc.objects.filter(
            nsInstanceId=ns_instance_id, lcmOperationType=lcm_operation_type).last()
        ns_lcm_op_occ.operationState = 'COMPLETED'
        ns_lcm_op_occ.save()

        self.kafka_notification.notify(ns_instance_id, 'NS Instance({}) had been {}'.format(ns_instance_id, ns_state))
