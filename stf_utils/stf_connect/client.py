# -*- coding: utf-8 -*-

import six
import threading
import json
import os
import time
import collections
import logging

from stf_utils.common.stfapi import SmartphoneTestingFarmAPI
from stf_utils.common import adb

log = logging.getLogger(__name__)


class Device:
    serial = None
    ready = None
    present = None
    owner = None
    remote_connect_url = None

    def __init__(self, **entries):
        self.dict = entries
        self.__dict__.update(entries)

    def __str__(self):
        return "Device %s(%s)" % (self.serial, self.remote_connect_url)

    def __repr__(self):
        return "Device %s(%s)" % (self.serial, self.remote_connect_url)


class SmartphoneTestingFarmClient(SmartphoneTestingFarmAPI):
    def __init__(self, host, common_api_path, oauth_token, device_spec, shutdown_emulator_on_disconnect, devices_file_path):
        super(SmartphoneTestingFarmClient, self).__init__(host, common_api_path, oauth_token)
        self.device_groups = []
        self.device_spec = device_spec
        self.devices_file_path = devices_file_path
        self.shutdown_emulator_on_disconnect = shutdown_emulator_on_disconnect
        self._set_up_device_groups()
        self.all_devices_are_connected = False

    def get_wanted_amount(self, group):
        amount = group.get("wanted_amount")
        if amount == 0:
            devices = self.useful_devices
            return len(self._filter_devices(devices, group))
        return amount

    def _set_up_device_groups(self):
        for wanted_device_group in self.device_spec:
            self.device_groups.append(
                {
                    "group_name": wanted_device_group.get("group_name"),
                    "wanted_amount": int(wanted_device_group.get("amount", 0)),
                    "specs": wanted_device_group.get("specs", {}),
                    "min_sdk": int(wanted_device_group.get("min_sdk", 1)),
                    "max_sdk": int(wanted_device_group.get("max_sdk", 99)),
                    "added_devices": [],
                    "connected_devices": []
                }
            )
        log.debug("Wanted device groups: {}".format(self.device_groups))

    def connect_devices(self):
        self.all_devices_are_connected = True
        for device_group in self.device_groups:
            wanted_amount, actual_amount = self.get_amounts(device_group)
            if actual_amount < wanted_amount:
                self.all_devices_are_connected = False
                appropriate_devices = self._filter_devices(self.available_devices, device_group)
                devices_to_connect = appropriate_devices[:wanted_amount - actual_amount]
                self._connect_added_devices(devices_to_connect, device_group)

    def get_amounts(self, device_group):
        wanted_amount = self.get_wanted_amount(device_group)
        connected_devices = device_group.get("connected_devices")
        actual_amount = len(connected_devices)
        log.info("Group: %s. Wanted Amount: %s. Actual Amount (%s): %s"
                 % (device_group.get("group_name"),
                    wanted_amount, actual_amount,
                    connected_devices))
        return wanted_amount, actual_amount

    def connected_devices_check(self):
        for device_group in self.device_groups:
            for device in device_group.get("connected_devices"):
                if not adb.device_is_ready(device.remote_connect_url):
                    log.warning("ADB connection with device {} was lost. "
                                "We'll try to connect a new one.".format(device))
                    self._delete_device_from_group(device, device_group)
                    self._disconnect_device(device)
                    log.warning("Still connected {} in group '{}'".format(
                        device_group.get("connected_devices"), device_group.get("group_name")))
                else:
                    adb.echo_ping(device.remote_connect_url)

    def _connect_added_devices(self, devices_to_add, device_group):
        for device in devices_to_add:
            try:
                log.info("Trying to connect %s from group %s..." % (device, device_group.get("group_name")))
                if self.is_device_available(device.serial):
                    self._add_device_to_group(device, device_group)
                    self._connect_device_to_group(device, device_group)
                    self._add_device_to_file(device)
                    log.info("%s was connected and ready for use" % device)
            except Exception:
                log.exception("Error connecting for %s" % device)
                self._delete_device_from_group(device, device_group)
                self._disconnect_device(device)

    def _add_device_to_group(self, device, device_group):
        self.add_device(serial=device.serial)
        device_group.get("added_devices").append(device)

    def _connect_device_to_group(self, device, device_group):
        resp = self.remote_connect(serial=device.serial)
        content = resp.json()
        device.remote_connect_url = content.get("remoteConnectUrl")
        log.info("Got remote connect url %s for connect by adb for %s" % (device.remote_connect_url, device.serial))

        try:
            adb.connect(device.remote_connect_url)
            device_group.get("connected_devices").append(device)
            log.debug("%s was added to connected devices list" % device)
        except TypeError:
            raise Exception("Error during connecting device by ADB connect for %s" % device)
        except OSError:
            raise Exception("ADB Connection Error during connection for %s" % device)

    def close_all(self):
        log.info("Disconnecting all devices...")
        self._disconnect_all()
        self._delete_all()

    def _add_device_to_file(self, device):
        try:
            with open(self.devices_file_path, 'a+') as mapping_file:
                json_mapping = json.dumps({
                    "adb_url": device.remote_connect_url,
                    "serial": device.serial
                })
                mapping_file.write("{0}\n".format(json_mapping))
        except OSError:
            log.exception("Can't open file {} for {}".format(self.devices_file_path, device))

    def _delete_device_from_group(self, device_for_delete, device_group):
        lists = ["connected_devices", "added_devices"]
        try:
            self.all_devices_are_connected = False
            for _list in lists:
                self._delete_device_from_devices_list(device_for_delete, device_group, _list)

            log.debug("Deleted %s from lists %s" % (device_for_delete, lists))
        except Exception:
            log.exception("Error deleting %s" % device_for_delete)

    def _delete_device_from_devices_list(self, device_for_delete, device_group, device_list):
        try:
            for device in device_group.get(device_list):
                if device_for_delete.serial == device.serial:
                    index = device_group.get(device_list).index(device)
                    device_group.get(device_list).pop(index)
        except Exception:
            log.exception("Deleting %s from list %s was failed" % (device_for_delete, device_list))

    def _delete_all(self):
        if os.path.exists(self.devices_file_path):
            try:
                os.remove(self.devices_file_path)
            except OSError:
                log.exception("Can't remove file {0}".format(self.devices_file_path))

        for device_group in self.device_groups:
            log.debug("Deleting devices from group %s" % device_group.get("added_devices"))
            for device in device_group.get("added_devices"):
                self._delete_device_from_group(device, device_group)

    def _disconnect_all(self):
        for device_group in self.device_groups:
            while device_group.get("connected_devices"):
                device = device_group.get("connected_devices").pop()
                self._disconnect_device(device)

    def remote_disconnect(self, device):
        try:
            super(SmartphoneTestingFarmClient, self).remote_disconnect(device.serial)
        except Exception:
            log.exception("Error during disconnect %s from stf" % device)

    def delete_device(self, device):
        try:
            super(SmartphoneTestingFarmClient, self).delete_device(serial=device.serial)
        except Exception:
            log.exception("Error during deleting %s from stf" % device)

    def _disconnect_device(self, device):
        try:
            if adb.device_is_ready(device.remote_connect_url):
                if self.shutdown_emulator_on_disconnect and device.serial.startswith('emulator'):
                    adb.shutdown_emulator(device.remote_connect_url)
                    log.info("%s has been released" % device)
                    return
                else:
                    adb.disconnect(device.remote_connect_url)
        except Exception:
            log.exception("Error during disconnect by ADB for %s" % device)

        self.remote_disconnect(device)
        self.delete_device(device)
        log.info("%s has been released" % device)

    def get_all_devices(self):
        try:
            resp = super(SmartphoneTestingFarmClient, self).get_all_devices()
            content = resp.json()
            return [Device(**device) for device in content.get("devices")]
        except Exception:
            log.exception("Getting devices list was failed")
            return []

    def _get_device_state(self, serial):
        time.sleep(0.1)  # don't ddos api =)
        try:
            response = self.get_device(serial=serial)
            return response.json().get("device", {})
        except Exception:
            log.exception("Device {} get state failed".format(self))

    def is_device_available(self, serial):
        state = self._get_device_state(serial)
        if state.get("present") and state.get("ready") and not state.get("owner"):
            log.debug("{} is available".format(serial))
            return True
        return False

    def is_device_useful(self, serial):
        state = self._get_device_state(serial)
        if state.get("present") and state.get("ready"):
            log.debug("{} is useful".format(serial))
            return True
        return False

    @property
    def available_devices(self):
        res = [device for device in self.get_all_devices() if self.is_device_available(device.serial)]
        log.info("Available devices for connect: {}".format(res))
        return res

    @property
    def useful_devices(self):
        res = [device for device in self.get_all_devices() if self.is_device_useful(device.serial)]
        log.info("Useful devices: {}".format(res))
        return res

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
            flatten_device = self._flatten_spec(device.dict)
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


class CommonPollThread(threading.Thread):
    def __init__(self, stf_client, poll_period=3):
        super(CommonPollThread, self).__init__()
        self._running = threading.Event()
        self.stf_client = stf_client
        self.poll_period = poll_period
        self.func = None

    def run(self):
        log.debug("Starting %s..." % str(self))
        last_run_time = 0
        while self.running:
            if time.time() - last_run_time >= self.poll_period:
                if self.func:
                    self.func()
                last_run_time = time.time()
            time.sleep(0.1)

    def start(self):
        log.debug("Starting {}...".format(self))
        self._running.set()
        super(CommonPollThread, self).start()

    def stop(self):
        log.debug("Stopping {}...".format(self))
        self._running.clear()
        self.join()

    @property
    def running(self):
        return self._running.isSet()


class STFDevicesConnector(CommonPollThread):
    def __init__(self, stf_client, poll_period=3):
        super(STFDevicesConnector, self).__init__(stf_client, poll_period)
        self.func = self.try_connect_required_devices

    def try_connect_required_devices(self):
        if not self.stf_client.all_devices_are_connected:
            self.stf_client.connect_devices()


class STFConnectedDevicesWatcher(CommonPollThread):
    def __init__(self, stf_client, poll_period=5):
        super(STFConnectedDevicesWatcher, self).__init__(stf_client, poll_period)
        self.func = self.stf_client.connected_devices_check
