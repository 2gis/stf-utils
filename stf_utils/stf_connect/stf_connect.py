# -*- coding: utf-8 -*-

import os
import argparse
import json
import logging
import signal
import sys
import time

from stf_utils.config.config import initialize_config_file
from stf_utils.stf_connect.client import SmartphoneTestingFarmClient, STFDevicesConnector, STFConnectedDevicesWatcher

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
logging.basicConfig(level=getattr(logging, LOG_LEVEL))
log = logging.getLogger(__name__)


def set_log_level(_log_level):
    if _log_level:
        log.debug("Changed log level to {0}".format(_log_level.upper()))
        log.setLevel(_log_level.upper())


class STFConnect:
    def __init__(self, config, device_spec):
        self.client = SmartphoneTestingFarmClient(
            host=config.main.get("host"),
            common_api_path="/api/v1",
            oauth_token=config.main.get("oauth_token"),
            device_spec=device_spec,
            devices_file_path=config.main.get("devices_file_path"),
            shutdown_emulator_on_disconnect=config.main.get("shutdown_emulator_on_disconnect")
        )
        self.connector = STFDevicesConnector(self.client)
        self.watcher = STFConnectedDevicesWatcher(self.client)

    def run_forever(self):
        self._start_workers()
        while True:
            time.sleep(1)

    def connect_devices(self, timeout):
        start = time.time()
        while time.time() < start + timeout:
            if not self.client.all_devices_are_connected:
                self.client.connect_devices()
            else:
                break
            time.sleep(0.2)
        else:
            log.info("Timeout connecting devices {}".format(timeout))
            self.client.close_all()

    def _start_workers(self):
        self.watcher.start()
        self.connector.start()

    def _stop_workers(self):
        if self.connector and self.connector.running:
            self.connector.stop()
        if self.watcher and self.watcher.running:
            self.watcher.stop()

    def stop(self):
        log.info("Stopping connect service...")
        self._stop_workers()

        log.debug("Stopping main thread...")
        self.client.close_all()


def get_spec(device_spec_path, groups=None):
    with open(device_spec_path) as f:
        device_spec = json.load(f)

    if groups:
        log.info("Working only with specified groups: {0}".format(groups))
        specified_groups = groups.split(",")
        return [group for group in device_spec if group.get("group_name") in specified_groups]

    return device_spec


def parse_args():
    parser = argparse.ArgumentParser(
        description="Utility for connecting "
                    "devices from STF"
    )
    parser.add_argument(
        "-g", "--groups", help="Device groups defined in spec file to connect"
    )
    parser.add_argument(
        "-l", "--log-level", help="Log level"
    )
    parser.add_argument(
        "-c", "--config", help="Path to config file", default="stf-utils.ini"
    )
    parser.add_argument(
        "--connect-and-quit", help="Connect devices and exit", action='store_true', default=False
    )
    parser.add_argument(
        "--timeout", help="Devices connect timeout", default=600
    )
    return parser.parse_args()


def register_signal_handler(handler):
    def exit_gracefully(signum, frame):
        handler()
        sys.exit(0)

    signal.signal(signal.SIGINT, exit_gracefully)
    signal.signal(signal.SIGTERM, exit_gracefully)


def run():
    args = parse_args()
    set_log_level(args.log_level)
    config = initialize_config_file(args.config)

    device_spec = get_spec(config.main.get("device_spec"), args.groups)

    stf_connect = STFConnect(config, device_spec)

    register_signal_handler(stf_connect.stop)

    log.info("Starting device connect service...")
    if args.connect_and_quit:
        stf_connect.connect_devices(args.timeout)
    else:
        stf_connect.run_forever()

if __name__ == "__main__":
    run()
