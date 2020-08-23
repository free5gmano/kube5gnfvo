import json

from NSLifecycleManagement.models import VnfInstance, NsInstance
from NSFaultManagement.models import Alarm, AlarmLinks, FaultyComponentInfo, FaultyResourceInfo
from datetime import datetime

from utils.notification_management.kafka_notification import KafkaNotification


class AlarmEvent(object):
    error_record = dict()
    kafka_notification = KafkaNotification('fault_alarm')

    def managed_object(self, vnf_instance):
        ns_instance_set = NsInstance.objects.filter(
            NsInstance_VnfInstance__vnfInstanceName=vnf_instance.vnfInstanceName)
        ns_instance_id = list()
        ns_instance_link = list()
        for ns_instance in ns_instance_set:
            ns_instance_id.append(str(ns_instance.id))
            ns_instance_link.append(str(ns_instance.NsInstance_links.link_self))

        return json.dumps(ns_instance_id), json.dumps(ns_instance_link)

    def create_alarm(self, name: str, reason: str, message: str):
        pod_name_list = name.split('-')
        [pod_name_list.pop(-1) for _ in range(0, 2)]
        vnf_name = '-'.join(pod_name_list)

        vnf_instance = VnfInstance.objects.filter(vnfInstanceName=vnf_name).last()
        if vnf_instance:
            ns_instance_id, ns_instance_link = self.managed_object(vnf_instance)
            check = self._time_check(ns_instance_id, str(vnf_instance.id))
            if check:
                self.kafka_notification.notify(ns_instance_id, 'NS Instance({}) crashed'.format(ns_instance_id))
                alarm = Alarm.objects.create(
                    **{'managedObjectId': ns_instance_id,
                       'probableCause': reason,
                       'faultDetails': message})

                AlarmLinks.objects.create(
                    _links=alarm,
                    **{'link_self': 'nsfm/v1/alarms/{}'.format(alarm.id),
                       'objectInstance': ns_instance_link})

                FaultyComponentInfo.objects.create(
                    rootCauseFaultyComponent=alarm,
                    **{'faultyVnfInstanceId': str(vnf_instance.id)}
                )

                FaultyResourceInfo.objects.create(rootCauseFaultyResource=alarm)

    def _time_check(self, ns_id, vnf_id):
        if ns_id + vnf_id in list(self.error_record):
            time = str(datetime.now() - self.error_record[ns_id + vnf_id]).split('.')[0].split(':')
            if int(time[0]) >= 1 or int(time[1]) >= 1 or int(time[2]) >= 10:
                self.error_record[ns_id + vnf_id] = datetime.now()
                return True
            return False
        else:
            self.error_record[ns_id + vnf_id] = datetime.now()
            return True
