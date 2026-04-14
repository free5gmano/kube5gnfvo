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

# gNB / UE 是另一套 model，alarm 也要支援查它們
try:
    from GnbManagement.models import GnbInstance, UeInstance
except ImportError:
    GnbInstance = None
    UeInstance = None


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

    def _find_instance_by_pod_name(self, name: str, is_container: bool):
        """
        Try to find a matching instance for a given pod name.
        Returns (instance, instance_type) where instance_type is 'vnf', 'gnb', or 'ue'.
        """
        candidates = []
        if is_container:
            # 容器 Pod name 格式: {deployment-name}-{rs-hash}-{pod-hash}
            # 嘗試逐步縮短前綴
            pod_name_list = name.split('-')
            for i in range(1, min(len(pod_name_list), 5)):
                candidate = '-'.join(pod_name_list[:-i])
                if candidate:
                    candidates.append(candidate)
        else:
            candidates.append(name[:-5])

        for candidate in candidates:
            # 1. 先找 VnfInstance (5GC)
            vnf = VnfInstance.objects.filter(vnfInstanceName=candidate).last()
            if vnf:
                return vnf, 'vnf'
            # 2. 找 GnbInstance
            if GnbInstance is not None:
                gnb = GnbInstance.objects.filter(gnbInstanceName=candidate).last()
                if gnb:
                    return gnb, 'gnb'
            # 3. 找 UeInstance
            if UeInstance is not None:
                ue = UeInstance.objects.filter(ueInstanceName=candidate).last()
                if ue:
                    return ue, 'ue'
        return None, None

    def create_alarm(self, name: str, reason: str, message: str, is_container: bool):
        instance, instance_type = self._find_instance_by_pod_name(name, is_container)
        if instance is None:
            return

        if instance_type == 'vnf':
            ns_instance_id, ns_instance_link = self.managed_object(instance)
            faulty_id = str(instance.id)
        else:
            # gNB / UE 沒有 NsInstance 關聯，直接用 instance 自己當 managedObject
            ns_instance_id = json.dumps([str(instance.id)])
            ns_instance_link = json.dumps([f'/{instance_type}/v1/instances/{instance.id}'])
            faulty_id = str(instance.id)

        check = self._time_check(ns_instance_id, faulty_id)
        if not check:
            return

        self.kafka_notification.notify(
            ns_instance_id,
            '{} Instance({}) crashed'.format(instance_type.upper(), ns_instance_id),
        )
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
            **{'faultyVnfInstanceId': faulty_id}
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
