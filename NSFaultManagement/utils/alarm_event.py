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

    def create_alarm(self, name: str, reason: str, message: str, is_container: bool):
        if is_container:
            # Try progressively shorter prefixes to match VnfInstance name.
            # Pod name format varies: {vnf_name}-{rs_hash}-{pod_hash}
            # but the number of '-' segments in the suffix is unpredictable.
            pod_name_list = name.split('-')
            vnf_instance = None
            for i in range(1, min(len(pod_name_list), 4)):
                candidate = '-'.join(pod_name_list[:-i])
                if not candidate:
                    break
                vnf_instance = VnfInstance.objects.filter(vnfInstanceName=candidate).last()
                if vnf_instance:
                    break
        else:
            vnf_name = name[:-5]
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

    # 同一個 (ns_id, vnf_id) 在此秒數內重複告警會被擋掉
    COOLDOWN_SECONDS = 60

    def _time_check(self, ns_id, vnf_id):
        key = ns_id + vnf_id
        now = datetime.now()
        if key in self.error_record:
            elapsed = (now - self.error_record[key]).total_seconds()
            if elapsed >= self.COOLDOWN_SECONDS:
                self.error_record[key] = now
                return True
            return False
        else:
            self.error_record[key] = now
            return True
