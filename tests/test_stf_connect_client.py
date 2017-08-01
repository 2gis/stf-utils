# -*- coding: utf-8 -*-

from lode_runner import dataprovider
from unittest import TestCase

try:
    from mock import patch, Mock
except ImportError:
    from unittest.mock import patch, Mock

from tests.helpers import get_response_from_file, wait_for
from stf_utils.stf_connect.client import SmartphoneTestingFarmClient, STFConnectedDevicesWatcher


class TestSmartphoneTestingFarmClient(TestCase):
    def setUp(self):
        super(TestSmartphoneTestingFarmClient, self).setUp()
        self.watcher = None
        get_all_devices = get_response_from_file('get_all_devices.json')
        get_device = get_response_from_file('get_device_x86.json')
        remote_connect = get_response_from_file('remote_connect.json')

        self.all_devices_mock = Mock(return_value=Mock(json=Mock(return_value=get_all_devices)))
        self.get_device_mock = Mock(return_value=Mock(json=Mock(return_value=get_device)))
        self.remote_connect_mock = Mock(return_value=Mock(json=Mock(return_value=remote_connect)))

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
        """
        - set config with 1 device
        - try to connect devices

        Expected: 1 device connected and 1 device in connected_devices list

        - stop stf-connect

        Expected: 0 devices connected and lists of devices was empty
        """
        with patch(
            'stf_utils.common.stfapi.SmartphoneTestingFarmAPI.get_all_devices', self.all_devices_mock,
        ), patch(
            'stf_utils.stf_connect.client.SmartphoneTestingFarmClient.get_device', self.get_device_mock,
        ), patch(
            'stf_utils.stf_connect.client.SmartphoneTestingFarmClient.add_device', Mock(),
        ), patch(
            'stf_utils.stf_connect.client.SmartphoneTestingFarmClient.remote_connect', self.remote_connect_mock,
        ), patch(
            'stf_utils.stf_connect.client.SmartphoneTestingFarmClient.delete_device', Mock(),
        ), patch(
            'stf_utils.stf_connect.client.SmartphoneTestingFarmClient.remote_disconnect', Mock(),
        ), patch(
            'stf_utils.common.adb.device_is_ready', Mock(return_value=True)
        ), patch(
            'stf_utils.common.adb.connect', Mock(return_value=True)
        ), patch(
            'stf_utils.common.adb.disconnect', Mock(return_value=True)
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

    @dataprovider([
        [
            {
                "group_name": "alfa",
                "amount": "1",
                "specs": {"abi": "x86"}
            }
        ]
    ])
    def test_connect_new_device_after_device_lost(self, device_spec):
        """
        - set config with 1 device
        - try to connect devices

        Expected: 1 device connected and 1 device in connected_devices list

        - start devices watcher
        - got 'False' in device_is_ready method (connected device is not available)

        Expected: 0 devices connected and lists of devices was empty
        (device was removed from stf-connect and device by adb was disconnected)

        - try to connect available devices

        Expected: 1 device connected and 1 device in connected_devices list
        """
        def raise_exception():
            raise Exception('something ugly happened in adb connect')

        with patch(
            'stf_utils.common.stfapi.SmartphoneTestingFarmAPI.get_all_devices', self.all_devices_mock,
        ), patch(
            'stf_utils.stf_connect.client.SmartphoneTestingFarmClient.get_device', self.get_device_mock,
        ), patch(
            'stf_utils.stf_connect.client.SmartphoneTestingFarmClient.add_device', Mock(),
        ), patch(
            'stf_utils.stf_connect.client.SmartphoneTestingFarmClient.remote_connect', self.remote_connect_mock,
        ), patch(
            'stf_utils.common.adb.device_is_ready', Mock(side_effect=[False, True, True])
        ), patch(
            'stf_utils.common.adb.connect', Mock(side_effect=[True, raise_exception, True])
        ), patch(
            'stf_utils.common.adb.disconnect', Mock(return_value=True)
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

            self.assertTrue(wait_for(lambda: len(stf.device_groups[0].get("added_devices")) == int(device_spec[0].get("amount"))))
            self.assertTrue(wait_for(lambda: len(stf.device_groups[0].get("connected_devices")) == int(device_spec[0].get("amount"))))

            self.watcher = STFConnectedDevicesWatcher(stf)
            self.watcher.start()

            self.assertTrue(wait_for(lambda: len(stf.device_groups[0].get("added_devices")) == 0))
            self.assertTrue(wait_for(lambda: len(stf.device_groups[0].get("connected_devices")) == 0))

            stf.connect_devices()

            self.assertTrue(wait_for(lambda: stf.shutdown_emulator_on_disconnect))
            self.assertTrue(wait_for(lambda: len(stf.device_groups[0].get("added_devices")) == int(device_spec[0].get("amount"))))
            self.assertTrue(wait_for(lambda: len(stf.device_groups[0].get("connected_devices")) == int(device_spec[0].get("amount"))))
