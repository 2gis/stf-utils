import six
from common.stfapi import SmartphoneTestingFarmAPI
from common import adb
import threading
import json
import os
import time
import collections
import logging

log = logging.getLogger('stf-connect')


class SmartphoneTestingFarmClient(SmartphoneTestingFarmAPI):
    def __init__(self, host, common_api_path, oauth_token, device_spec, shutdown_emulator_on_disconnect, devices_file_path):
        super(SmartphoneTestingFarmClient, self).__init__(host, common_api_path, oauth_token)
        self.device_groups = []
        self.device_spec = device_spec
        self.devices_file_path = devices_file_path
        self.shutdown_emulator_on_disconnect = shutdown_emulator_on_disconnect
        for wanted_device_group in self.device_spec:
            self.device_groups.append(
            {
                "group_name": wanted_device_group.get("group_name"),
                "wanted_amount": wanted_device_group.get("amount"),
                "specs": wanted_device_group.get("specs", {}),
                "min_sdk": int(wanted_device_group.get("min_sdk", 1)),
                "max_sdk": int(wanted_device_group.get("max_sdk", 99)),
                "added_devices": [],
                "connected_devices": []
            })
        log.debug("Created list of wanted devices groups: %s" % self.device_groups)
        self.all_devices_are_connected = False

    def connect_devices(self):
        self.all_devices_are_connected = True
        for device_group in self.device_groups:
            available_devices = self._get_available_devices()
            simply_available_devices = [d.get("serial") for d in available_devices]
            log.debug("Got avaliable devices for connect:\n%s" % simply_available_devices)
            wanted_amount = int(device_group.get("wanted_amount"))
            actual_amount = len(device_group.get("connected_devices"))
            log.debug("Trying connect devices... Wanted Amount: %s. Actual Amount: %s" % (wanted_amount, actual_amount))
            if actual_amount < wanted_amount:
                self.all_devices_are_connected = False
                appropriate_devices = self._filter_devices(available_devices, device_group)
                devices_to_connect = appropriate_devices[:wanted_amount - actual_amount]
                self._connect_added_devices(devices_to_connect, device_group)

    def _connect_added_devices(self, devices_to_add, device_group):
        for device in devices_to_add:
            try:
                if self._device_is_available(device):
                    self._add_device_to_group(device, device_group)
                    self._connect_device_to_group(device, device_group)
            except Exception as e:
                self._delete_device_from_group(device, device_group)
                log.debug("%s. \nDevice %s" % (str(e), device.get("serial")))

    def _add_device_to_group(self, device, device_group):
        self.add_device(serial=device.get("serial"))
        device_group.get("added_devices").append(device)

    def _connect_device_to_group(self, device, device_group):
        device_serial = device.get("serial")
        resp = self.remote_connect(serial=device_serial)
        content = resp.json()
        remote_connect_url = content.get("remoteConnectUrl")
        log.debug("Got remote connect url %s for connect by adb for device %s" % (remote_connect_url, device_serial))

        try:
            adb.connect(remote_connect_url)
            device["remoteConnectUrl"] = remote_connect_url
            device_group.get("connected_devices").append(device)
            self._add_device_to_file(device)
        except TypeError:
            raise Exception("Error during connecting device by adb connect %s for device %s" % (remote_connect_url, device_serial))
        except ConnectionError:
            raise Exception("ADB Connection Error during connection for %s with %s" % (remote_connect_url, device_serial))

    def close_all(self):
        self._disconnect_all()
        self._delete_all()

    def _add_device_to_file(self, device):
        try:
            with open(self.devices_file_path, 'a+') as mapping_file:
                json_mapping = json.dumps({
                    "adb_url": device.get("remoteConnectUrl"),
                    "serial": device.get("serial")
                })
                mapping_file.write("{0}\n".format(json_mapping))
        except PermissionError:
            log.debug("PermissionError: Can't open file {0}".format(self.devices_file_path))

    def _delete_device_from_group(self, device_for_delete, device_group):
        for device in device_group.get("added_devices"):
            if device_for_delete.get("serial") == device.get("serial"):
                try:
                    self.delete_device(serial=device.get("serial"))
                    index = device_group.get("added_devices").index(device)
                    device_group.get("added_devices").pop(index)
                    log.debug("Deleted device %s" % device.get("serial"))
                except Exception as e:
                    log.debug("Delete device %s was failed: %s" % (device.get("serial"), str(e)))

    def _delete_all(self):
        if os.path.exists(self.devices_file_path):
            try:
                os.remove(self.devices_file_path)
            except PermissionError:
                log.debug("PermissionError: Can't remove file {0}".format(self.devices_file_path))

        for device_group in self.device_groups:
            simply_device_group = [d.get("serial") for d in device_group.get("added_devices")]
            log.debug("Deleting devices from group \n%s" % simply_device_group)
            for device in device_group.get("added_devices"):
                self._delete_device_from_group(device, device_group)

    def _disconnect_all(self):
        for device_group in self.device_groups:
            while device_group.get("connected_devices"):
                device = device_group.get("connected_devices").pop()
                self._disconnect_device(device)

    def _disconnect_device(self, device):
        serial = device.get("serial")
        if self.shutdown_emulator_on_disconnect and serial.startswith('emulator'):
            remote_connect_url = device.get("remoteConnectUrl")
            adb.shutdown_emulator(remote_connect_url)
            return

        try:
            self.remote_disconnect(serial)
            log.debug("Device %s has been disconnected" % serial)
        except Exception as e:
            log.debug("Device %s has not been disconnected. %s" % (serial, str(e)))

    def _get_all_devices(self):
        try:
            resp = self.get_all_devices()
            content = resp.json()
            return content.get("devices")
        except Exception as e:
            log.debug("Getting devices list was failed %s" % str(e))
            return []

    def _get_available_devices(self):
        available_devices = []
        for device in self._get_all_devices():
            if self._device_is_available(device):
                available_devices.append(device)
        return available_devices

    def _device_is_available(self, device):
        time.sleep(0.1)  # don't ddos api =)
        is_available = False
        try:
            response = self.get_device(serial=device.get("serial"))
            renewed_device = response.json().get("device", {})
            if renewed_device.get("present") and renewed_device.get("ready") and not renewed_device.get("owner"):
                log.debug("Device %s is available" % renewed_device.get("serial"))
                is_available = True
        except Exception as e:
            log.debug("Device %s is not available %s" % (device.get("serial"), str(e)))
        return is_available

    def _flatten_spec(self, d, parent_key='', sep='_'):
        items = []
        for k, v in d.items():
            new_key = parent_key + sep + k if parent_key else k
            if isinstance(v, collections.MutableMapping):
                items.extend(self._flatten_spec(v, new_key, sep=sep).items())
            else:
                items.append((new_key, v))
        return dict(items)

    def _filter_devices(self, devices, specification):
        filtered_devices = []
        for device in devices:
            flatten_device = self._flatten_spec(device)
            min_sdk = specification.get("min_sdk")
            max_sdk = specification.get("max_sdk")
            correct_sdk_version_list = {i for i in range(min_sdk, max_sdk + 1)}
            device_is_appropriate = True

            if int(flatten_device.get("sdk")) not in correct_sdk_version_list:
                device_is_appropriate = False
                continue

            for key, value in six.iteritems(specification.get("specs")):
                if value not in {flatten_device.get(key), "ANY"}:
                    device_is_appropriate = False
                    break

            if device_is_appropriate:
                filtered_devices.append(device)
        return filtered_devices


class SmartphoneTestingFarmPoll(threading.Thread):
    def __init__(self, stf_client, poll_period=3):
        super(SmartphoneTestingFarmPoll, self).__init__()
        self._stopper = threading.Event()
        self.stf_client = stf_client
        self.poll_period = poll_period

    def run(self):
        last_run_time = 0
        while True:
            if self.stopped():
                break
            if self.stf_client.all_devices_are_connected:
                break
            if time.time() - last_run_time >= self.poll_period:
                self.stf_client.connect_devices()
                last_run_time = time.time()
            time.sleep(0.1)

    def stop(self):
        self._stopper.set()

    def stopped(self):
        return self._stopper.isSet()
