from os_ma_nfvo.settings import ONOS_IP
from utils.base_request import BaseRequest


class ONOSClient(BaseRequest):
    onos_account = 'onos'
    onos_password = 'rocks'
    onos_base_uri = ONOS_IP

    def __init__(self):
        super().__init__(
            self.onos_base_uri, auth_account=self.onos_account, auth_password=self.onos_password)

    def register_sfc(self, body: dict):
        self.post('register', data=body)

    def notification_sf_info(self, body: dict):
        self.post('notification', data=body)

    def read_sfc(self, body: dict):
        return self.post('read', data=body)

    def remove_sfc(self, body: dict):
        self.post('delete', data=body)
