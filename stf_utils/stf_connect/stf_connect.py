import argparse
import json
import logging
import signal
import sys
import time

from stf_utils.config.config import initialize_config_file
from stf_utils.stf_connect.client import SmartphoneTestingFarmClient, STFDevicesConnector, STFConnectedDevicesWatcher

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s"
)
log = logging.getLogger('stf-connect')


def run():
    def exit_gracefully(signum, frame):
        log.info("Stopping connect service...")
        try:
            thread_stop(devices_watcher_thread)
            thread_stop(devices_connector_thread)
        except NameError as e:
            log.warn("Poll thread is not defined, skipping... %s" % str(e))
        log.info("Stopping main thread...")
        stf.close_all()
        sys.exit(0)

    def thread_stop(thread):
        thread.stop()
        thread.join()

    def set_log_level():
        if args["log_level"]:
            log.info("Changed log level to {0}".format(args["log_level"].upper()))
            log.setLevel(args["log_level"].upper())

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
        "-c", "--config", help="Path to config file", default="default-config.ini"
    )
    args = vars(parser.parse_args())
    config_file = args["config"]
    config = initialize_config_file(config_file)
    signal.signal(signal.SIGINT, exit_gracefully)
    signal.signal(signal.SIGTERM, exit_gracefully)
    set_log_level()
    log.info("Starting connect service...")
    with open(config.main.get("device_spec")) as f:
        device_spec = json.load(f)
    if args["groups"]:
        log.info("Working only with specified groups: {0}".format(args["groups"]))
        specified_groups = args["groups"].split(",")
        device_spec = [device_group for device_group in device_spec if device_group.get("group_name") in specified_groups]
    stf = SmartphoneTestingFarmClient(
        host=config.main.get("host"),
        common_api_path="/api/v1",
        oauth_token=config.main.get("oauth_token"),
        device_spec=device_spec,
        devices_file_path=config.main.get("devices_file_path"),
        shutdown_emulator_on_disconnect=config.main.get("shutdown_emulator_on_disconnect")
    )
    devices_connector_thread = STFDevicesConnector(stf)
    devices_watcher_thread = STFConnectedDevicesWatcher(stf)
    devices_watcher_thread.start()
    devices_connector_thread.start()

    while True:
        time.sleep(100)

if __name__ == "__main__":
    run()
