import sys
import time
import signal
import client
import json
import logging
from six.moves import configparser

config = configparser.ConfigParser()
config.read("config.ini")
HOST = config.get("main", "host")
OAUTH_TOKEN = config.get("main", "oauth_token")
DEVICE_SPEC = config.get("main", "device_spec")

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s %(levelname)s %(message)s"
)


def exit_gracefully(signum, frame):
    stf.close_all()
    sys.exit(0)


if __name__ == '__main__':
    signal.signal(signal.SIGINT, exit_gracefully)
    signal.signal(signal.SIGTERM, exit_gracefully)
    stf = client.SmartphoneTestingFarmClient(
        host=HOST,
        common_api_path="/api/v1",
        oauth_token=OAUTH_TOKEN,
    )
    with open(DEVICE_SPEC) as f:
        device_spec = json.load(f)
    stf.add_devices(device_spec=device_spec)
    try:
        stf.connect_to_mine()
    except Exception as e:
        stf.close_all()
        raise e
    while True:
        time.sleep(100)
