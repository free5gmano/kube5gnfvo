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
from abc import abstractmethod

from NSDSubscription.models import NsdmSubscription
from NSFaultSubscription.models import FmSubscription
from NSLifecycleSubscriptions.models import LccnSubscription
from VnfPackageSubscription.models import PkgmSubscription
from utils.base_request import BaseRequest


class NotificationManagement(object):
    Subscription_Type = (VNFPackage, NSDescriptor, NSInstance, FaultAlarm) = (
        'vnf_pkg', 'ns_descriptor', 'ns_instance', 'fault_alarm')

    def __init__(self, subscription_type):
        self.subscription_type = subscription_type
        self.header = None
        self.response = None

    def _set_header(self, header: dict):
        self.header = header

    def _initialization_response(self, response: dict):
        self.response = response

    def notify(self, subscription_id, notify_massage: str):
        subscription = self._check_subscription_exist(subscription_id)
        if subscription:
            self._process_data(notify_massage)
            BaseRequest(subscription.callbackUri).post(uri='', data=self.response, headers=self.header)

    def _check_subscription_exist(self, subscription_id):
        return {
            self.VNFPackage: PkgmSubscription.objects.filter(
                pkgm_subscription_fk_filter__vnfPkgId__contains=subscription_id).last(),
            self.NSDescriptor: NsdmSubscription.objects.filter(
                nsdm_subscription_fk_filter__nsdInfoId__contains=subscription_id).last(),
            self.NSInstance: LccnSubscription.objects.filter(
                lccn_subscription_fk_filter__lccn_subscription_filter_fk_filter__nsInstanceIds__contains=subscription_id).last(),
            self.FaultAlarm: FmSubscription.objects.filter(
                fm_subscription_fk_fm_subscriptions_filter__fm_subscription_filter_fk_ns_instance_subscription_filter__nsInstanceIds=subscription_id).last()
        }.get(self.subscription_type, None)

    @abstractmethod
    def _process_data(self, data):
        pass
