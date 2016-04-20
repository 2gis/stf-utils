import signal
import logging
import json
import time
import sys
import argparse
from stf_connect.client import SmartphoneTestingFarmClient, SmartphoneTestingFarmPoll
from common import config

HOST = config.get("main", "host")
OAUTH_TOKEN = config.get("main", "oauth_token")
DEVICE_SPEC = config.get("main", "device_spec")
DEVICES_FILE_DIR = config.get("main", "devices_file_dir")
DEVICES_FILE_NAME = config.get("main", "devices_file_name")
DEVICES_FILE_PATH = "{0}/{1}".format(DEVICES_FILE_DIR, DEVICES_FILE_NAME)
SHUTDOWN_EMULATOR_ON_DISCONNECT = config.get("main", "shutdown_emulator_on_disconnect")

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s %(levelname)s %(message)s"
)
log = logging.getLogger('stf-connect')


def exit_gracefully(signum, frame):
    log.info("Stopping connect service...")
    try:
        log.info("Stopping poll thread...")
        poll_thread.stop()
        poll_thread.join()
    except NameError:
        log.warn("Poll thread is not defined, skipping...")
    log.info("Stopping main thread...")
    stf.close_all()
    sys.exit(0)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Utility for connecting '
                    'devices from STF'
    )
    parser.add_argument(
        '-groups', help='Device groups defined in spec file to connect'
    )
    args = vars(parser.parse_args())
    signal.signal(signal.SIGINT, exit_gracefully)
    signal.signal(signal.SIGTERM, exit_gracefully)
    log.info("Starting connect service...")
    with open(DEVICE_SPEC) as f:
        device_spec = json.load(f)
    if args['groups']:
        log.info('Working only with specified groups: {0}'.format(args['groups']))
        specified_groups = args["groups"].split(",")
        device_spec = [device_group for device_group in device_spec if device_group.get("group_name") in specified_groups]
    stf = SmartphoneTestingFarmClient(
        host=HOST,
        common_api_path="/api/v1",
        oauth_token=OAUTH_TOKEN,
        device_spec=device_spec,
        devices_file_path=DEVICES_FILE_PATH,
        shutdown_emulator_on_disconnect=SHUTDOWN_EMULATOR_ON_DISCONNECT
    )
    try:
        stf.connect_devices()
    except Exception as e:
        stf.close_all()
        raise e
    poll_thread = SmartphoneTestingFarmPoll(stf)
    poll_thread.start()
    while True:
        time.sleep(100)
