from stfapi import SmartphoneTestingFarmAPI
import six


class SmartphoneTestingFarmClient(SmartphoneTestingFarmAPI):
    def __init__(self, *args, **kwargs):
        super(SmartphoneTestingFarmClient, self).__init__(*args, **kwargs)

    def connect_devices(self, device_spec):
        self.add_devices(device_spec)
        self.connect_to_mine()

    def add_devices(self, device_spec):
        devices_to_add = self._get_appropriate_devices(device_spec)
        for device in devices_to_add:
            self.add_device(serial=device.get("serial"))

    def connect_to_mine(self):
        pass

    def close_all(self):
        self.delete_all()
        self.disconnect_all()

    def delete_all(self):
        my_devices = self._get_my_devices()
        for device in my_devices:
            self.delete_device(serial=device.get("serial"))

    def disconnect_all(self):
        my_devices = self._get_my_devices()
        for device in my_devices:
            self.remote_disconnect(serial=device.get("serial"))

    def _get_all_devices(self):
        resp = self.get_all_devices()
        content = resp.json()
        return content.get("devices")

    def _get_my_devices(self):
        resp = self.get_my_devices()
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
        for actual_device in all_devices:
            for wanted_device_group in device_spec:
                actual_device_is_approriate = True
                wanted_device_specs = wanted_device_group.get("specs")
                for key, value in six.iteritems(wanted_device_specs):
                    if value not in {actual_device.get(key), "ANY"}:
                        actual_device_is_approriate = False
                        break
                if actual_device_is_approriate:
                    appropriate_devices.append(actual_device)
                    break
        return appropriate_devices
