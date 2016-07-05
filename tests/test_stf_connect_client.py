from lode_runner import dataprovider
from mock import patch, Mock
from unittest import TestCase

from tests.helpers import get_response_from_file, wait_for
from stf_connect.client import SmartphoneTestingFarmClient


class TestSmartphoneTestingFarmClient(TestCase):
    def setUp(self):
        super(TestSmartphoneTestingFarmClient, self).setUp()
        self.watcher = None
        self.get_all_devices = get_response_from_file('get_all_devices.json')
        self.get_device = get_response_from_file('get_device_x86.json')
        self.remote_connect = get_response_from_file('remote_connect.json')

    def tearDown(self):
        if self.watcher:
            self.watcher.stop()

    @dataprovider([
        [
            {
                "group_name": "alfa",
                "amount": "1",
                "min_sdk": "16",
                "max_sdk": "23",
                "specs": {"abi": "x86", "platform": "Android"}
            }
        ]
    ])
    def test_connect_devices(self, device_spec):
        all_devices_mock = Mock(return_value=Mock(json=Mock(return_value=self.get_all_devices)))
        get_device_mock = Mock(return_value=Mock(json=Mock(return_value=self.get_device)))
        remote_connect_mock = Mock(return_value=Mock(json=Mock(return_value=self.remote_connect)))

        with patch(
            'stf_connect.client.SmartphoneTestingFarmClient.get_all_devices', all_devices_mock,
        ), patch(
            'stf_connect.client.SmartphoneTestingFarmClient.get_device', get_device_mock,
        ), patch(
            'stf_connect.client.SmartphoneTestingFarmClient.add_device', Mock(),
        ), patch(
            'stf_connect.client.SmartphoneTestingFarmClient.remote_connect', remote_connect_mock,
        ), patch(
            'stf_connect.client.SmartphoneTestingFarmClient.delete_device', Mock(),
        ), patch(
            'stf_connect.client.SmartphoneTestingFarmClient.remote_disconnect', Mock(),
        ), patch(
            'common.adb.device_is_ready', Mock(return_value=True)
        ), patch(
            'common.adb.connect', Mock(return_value=True)
        ):
            stf = SmartphoneTestingFarmClient(
                host="http://host.domain",
                common_api_path="/api/v1",
                oauth_token="test token",
                device_spec=device_spec,
                devices_file_path="./devices",
                shutdown_emulator_on_disconnect=True
            )
            stf.connect_devices()

            wait_for(lambda: self.assertTrue(stf.shutdown_emulator_on_disconnect))
            wait_for(lambda: self.assertEqual(len(stf.device_groups[0].get("added_devices")), int(device_spec[0].get("amount"))))
            wait_for(lambda: self.assertEqual(len(stf.device_groups[0].get("connected_devices")), int(device_spec[0].get("amount"))))

            stf.close_all()

            wait_for(lambda: self.assertEqual(len(stf.device_groups[0].get("added_devices")), 0))
            wait_for(lambda: self.assertEqual(len(stf.device_groups[0].get("connected_devices")), 0))
