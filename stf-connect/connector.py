import sys
import time
import signal
import client
import json
import logging

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s %(levelname)s %(message)s'
)


def exit_gracefully(signum, frame):
    stf.close_all()
    sys.exit(0)


if __name__ == '__main__':
    signal.signal(signal.SIGINT, exit_gracefully)
    signal.signal(signal.SIGTERM, exit_gracefully)
    stf = client.SmartphoneTestingFarmClient(
        host="http://stf.auto.ostack.test",
        common_api_path="/api/v1",
        oauth_token="e1cb89b5108348dd9251b7848948084809dad3a2e1084d8ebc4bf6663381d56e",
    )
    with open("spec.json") as f:
        device_spec = json.load(f)
    stf.add_devices(device_spec=device_spec)
    stf.connect_to_mine()
    while True:
        time.sleep(100)
