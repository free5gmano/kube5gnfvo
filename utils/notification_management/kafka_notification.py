import base64

from utils.notification_management.base_notification_management import NotificationManagement


class KafkaNotification(NotificationManagement):
    def __init__(self, subscription_type):
        super().__init__(subscription_type)
        self._set_header({"Content-Type": "application/vnd.kafka.v1+json"})
        self._initialization_response({"records": list()})

    def _process_data(self, data):
        b64_data = base64.b64encode(data.encode())
        self.response['records'].clear()
        self.response['records'].append({"value": b64_data.decode()})
