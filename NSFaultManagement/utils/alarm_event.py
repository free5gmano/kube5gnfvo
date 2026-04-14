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

        Pod name patterns:
        - VNF (5GC):  {vnf_name}-{rs_hash}-{pod_hash}
                      → vnf_name 直接對應 VnfInstance.vnfInstanceName
        - gNB/UE:     gnb-{uuid_short}-{rs_hash}-{pod_hash}
                       → uuid_short 是 GnbInstance.id 的前 8 字元
                       → 需要用 UUID 前綴比對，不是直接 name 比對
        """
        candidates = []
        if is_container:
            pod_name_list = name.split('-')
            for i in range(1, min(len(pod_name_list), 5)):
                candidate = '-'.join(pod_name_list[:-i])
                if candidate:
                    candidates.append(candidate)
        else:
            candidates.append(name[:-5])

        # 1. 先用 name 找 VnfInstance (5GC)
        for candidate in candidates:
            vnf = VnfInstance.objects.filter(vnfInstanceName=candidate).last()
            if vnf:
                return vnf, 'vnf'

        # 2. gNB / UE: 用 UUID 前綴比對
        # Pod name pattern: gnb-{first8chars}-{rs}-{pod} or ue-{first8chars}-{rs}-{pod}
        if is_container and name:
            parts = name.split('-')
            if len(parts) >= 2:
                # e.g., "gnb-128f9281-574d479467-4p9bp" → prefix="gnb", uuid_short="128f9281"
                prefix = parts[0]
                uuid_short = parts[1]

                if prefix == 'gnb' and GnbInstance is not None:
                    for gnb in GnbInstance.objects.all():
                        if str(gnb.id).startswith(uuid_short):
                            return gnb, 'gnb'

                if prefix == 'ue' and UeInstance is not None:
                    for ue in UeInstance.objects.all():
                        if str(ue.id).startswith(uuid_short):
                            return ue, 'ue'

        # 3. Fallback: 直接用 name 比對 gnb/ue (如果使用者部署時給了特殊名字)
        for candidate in candidates:
            if GnbInstance is not None:
                gnb = GnbInstance.objects.filter(gnbInstanceName=candidate).last()
                if gnb:
                    return gnb, 'gnb'
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

        # 在 faultDetails 開頭加上 type= 標記讓 Agent 能區分 vnf/gnb/ue
        # 不能用 [gnb] 這種格式因為 format_tools.py 會把開頭有 [ 的字串當 JSON parse
        tagged_message = f'type={instance_type}; {message}' if message else f'type={instance_type}'

        # Kafka notification 帶完整 alarm 詳情 (JSON 格式)，webhook 端就不用再打 API
        notification_payload = json.dumps({
            'instance_type': instance_type,
            'ns_instance_id': faulty_id,
            'probableCause': reason,
            'faultDetails': tagged_message,
            'faultyVnfInstanceId': faulty_id,
            'perceivedSeverity': 'CRITICAL',
        })
        self.kafka_notification.notify(ns_instance_id, notification_payload)

        alarm = Alarm.objects.create(
            **{'managedObjectId': ns_instance_id,
               'probableCause': reason,
               'faultDetails': tagged_message})

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
