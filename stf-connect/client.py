import six
import stfapi
import adb
import threading
import time


class SmartphoneTestingFarmClient(stfapi.SmartphoneTestingFarmAPI):
    def __init__(self, host, common_api_path, oauth_token, device_spec):
        super(SmartphoneTestingFarmClient, self).__init__(host, common_api_path, oauth_token)
        self.device_groups = []
        self.device_spec = device_spec
        for wanted_device_group in self.device_spec:
            self.device_groups.append(
                {
                    "group_name": wanted_device_group.get("group_name"),
                    "wanted_amount": wanted_device_group.get("amount"),
                    "specs": wanted_device_group.get("specs"),
                    "added_devices": [],
                    "connected_devices": []
                }
            )

    def connect_devices(self):
        available_devices = self._get_available_devices()
        for device_group in self.device_groups:
            wanted_amount = device_group.get("wanted_amount")
            actual_amount = len(device_group.get("connected_devices"))
            if actual_amount < wanted_amount:
                appropriate_devices = self._filter_devices(available_devices, device_group.get("specs"))
                devices_to_connect = appropriate_devices[:wanted_amount - actual_amount]
                self._add_devices_to_group(devices_to_connect, device_group)
                self._connect_devices_to_group(devices_to_connect, device_group)

    def _add_devices_to_group(self, devices_to_add, device_group):
        for device in devices_to_add:
            self.add_device(serial=device.get("serial"))
            device_group.get("added_devices").append(device)

    def _connect_devices_to_group(self, devices_to_connect, device_group):
        for device in devices_to_connect:
            resp = self.remote_connect(serial=device.get("serial"))
            content = resp.json()
            remote_connect_url = content.get("remoteConnectUrl")
            adb.connect(remote_connect_url)
            device_group.get("connected_devices").append(device)

    def close_all(self):
        self._disconnect_all()
        self._delete_all()

    def _delete_all(self):
        for device_group in self.device_groups:
            while device_group.get("added_devices"):
                device = device_group.get("added_devices").pop()
                self.delete_device(serial=device.get("serial"))

    def _disconnect_all(self):
        for device_group in self.device_groups:
            while device_group.get("connected_devices"):
                device = device_group.get("connected_devices").pop()
                self.remote_disconnect(serial=device.get("serial"))

    def _get_all_devices(self):
        resp = self.get_all_devices()
        content = resp.json()
        return content.get("devices")

    def _get_available_devices(self):
        available_devices = []
        for device in self._get_all_devices():
            if device.get("present") and not device.get("owner"):
                available_devices.append(device)
        return available_devices

    @staticmethod
    def _filter_devices(devices, specification):
        filtered_devices = []
        for device in devices:
            device_is_appropriate = True
            for key, value in six.iteritems(specification):
                        if value not in {device.get(key), "ANY"}:
                            device_is_appropriate = False
                            break
            if device_is_appropriate:
                filtered_devices.append(device)
        return filtered_devices


# class SmartphoneTestingFarmPoll(threading.Thread):
#     def __init__(self, stf_client, device_spec, poll_period=3):
#         self.stf_client = stf_client
#         self.device_spec = device_spec
#         self.poll_period = poll_period
#         super(SmartphoneTestingFarmPoll, self).__init__()
#
#     def run(self):
#         while True:
#
#             time.sleep(self.poll_period)
#
#
# myThread = SmartphoneTestingFarmPoll(stf, device_spec)
# myThread.start()
#
# [
#     {
#         "group_name": "alfa",
#         "amount": "7",
#         "serials": ["emulator-5554"]
#     }
# ]