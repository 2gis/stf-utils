from stfapi import SmartphoneTestingFarmAPI


class SmartphoneTestingFarmClient(SmartphoneTestingFarmAPI):
    def __init__(self, *args, **kwargs):
        super(SmartphoneTestingFarmClient, self).__init__(*args, **kwargs)
        self.devices = [{"serial": "emulator-5554"}]

    def add_devices(self, device_spec):
        for device in self.devices:
            self.add_device(serial=device.get("serial"))

    def connect_to_mine(self):
        pass

    def close_all(self):
        for device in self.devices:
            self.delete_device(serial=device.get("serial"))
