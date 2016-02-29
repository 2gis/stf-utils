import six
import stfapi
import adb


class SmartphoneTestingFarmClient(stfapi.SmartphoneTestingFarmAPI):
    def __init__(self, *args, **kwargs):
        super(SmartphoneTestingFarmClient, self).__init__(*args, **kwargs)
        self.session_devices = []

    def connect_devices(self, device_spec):
        self.add_devices(device_spec)
        self.connect_mine()

    def add_devices(self, device_spec):
        devices_to_add = self._get_appropriate_devices(device_spec)
        for device in devices_to_add:
            self.add_device(serial=device.get("serial"))
            self.session_devices.append(device)

    def connect_mine(self):
        for device in self.session_devices:
            resp = self.remote_connect(serial=device.get("serial"))
            content = resp.json()
            remote_connect_url = content.get("remoteConnectUrl")
            adb.connect(remote_connect_url)

    def close_all(self):
        self.disconnect_mine()
        self.delete_mine()

    def delete_mine(self):
        while self.session_devices:
            device = self.session_devices.pop()
            self.delete_device(serial=device.get("serial"))

    def disconnect_mine(self):
        for device in self.session_devices:
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

    def _get_appropriate_devices(self, device_spec):
        appropriate_devices = []
        all_devices = self._get_available_devices()
        for wanted_device_group in device_spec:
            number_of_devices_to_add = int(wanted_device_group.get("amount"))
            wanted_device_specs = wanted_device_group.get("specs")
            for device in all_devices:
                if number_of_devices_to_add == 0:
                    break
                device_is_appropriate = True
                for key, value in six.iteritems(wanted_device_specs):
                    if value not in {device.get(key), "ANY"}:
                        device_is_appropriate = False
                        break
                if device_is_appropriate:
                    number_of_devices_to_add -= 1
                    appropriate_devices.append(device)
        return appropriate_devices
