import argparse
import asyncio
import json
import logging
import signal

from autobahn.asyncio.websocket import WebSocketClientFactory

import functools
import os
from stf_utils.common.stfapi import SmartphoneTestingFarmAPI
from stf_utils.config.config import initialize_config_file
from stf_utils.stf_record.protocol import STFRecordProtocol

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("stf-record")
config = initialize_config_file()


def gracefully_exit(loop):
    log.info("Stopping loop...")
    loop.stop()


def wsfactory(address, directory, resolution, keep_old_data):
    loop = asyncio.get_event_loop()
    gracefully_exit_handler = functools.partial(gracefully_exit, loop)
    loop.add_signal_handler(signal.SIGTERM, gracefully_exit_handler)
    loop.add_signal_handler(signal.SIGINT, gracefully_exit_handler)

    directory = create_directory_if_not_exists(directory)
    if not keep_old_data:
        remove_all_data(directory)

    factory = WebSocketClientFactory("ws://{0}".format(address))
    factory.protocol = STFRecordProtocol
    factory.protocol.img_directory = directory
    factory.protocol.address = address
    factory.protocol.resolution = resolution

    coro = loop.create_connection(
        factory, address.split(":")[0], address.split(":")[1]
    )
    log.info("Connecting to {0} ...".format(address))
    loop.run_until_complete(coro)
    try:
        loop.run_forever()
    finally:
        loop.close()


def create_directory_if_not_exists(directory):
    directory = os.path.abspath(directory)
    log.debug("Using directory \"{0}\" for storing images".format(directory))
    if not os.path.exists(directory):
        os.makedirs(directory)
    return directory


def remove_all_data(directory):
    if directory and os.path.exists(directory):
        for file in os.listdir(directory):
            if file.endswith(".txt") or file.endswith(".jpg"):
                try:
                    os.remove("{0}/{1}".format(directory, file))
                    log.debug("File {0}/{1} was deleted".format(directory, file))
                except Exception as e:
                    log.debug("Error during deleting file {0}/{1}: {2}".format(directory, file, str(e)))


def _get_device_serial(adb_connect_url, connected_devices_file_path):
        device_serial = None
        with open(connected_devices_file_path, "r") as devices_file:
            for line in devices_file.readlines():
                line = json.loads(line)
                log.debug("Finding device serial of device connected as {0} in {1}".format(
                    adb_connect_url,
                    connected_devices_file_path
                ))
                if line.get("adb_url") == adb_connect_url:
                    log.debug("Found device serial {0} for device connected as {1}".format(
                        line.get("serial"),
                        adb_connect_url)
                    )
                    device_serial = line.get("serial")
                    break
            else:
                log.warn("No matching device serial found for device name {0}".format(adb_connect_url))
        return device_serial


def get_ws_url(api, args):
    if args.get("adb_connect_url"):
        connected_devices_file_path = config.main.get("devices_file_path")
        args["serial"] = _get_device_serial(
            args["adb_connect_url"], connected_devices_file_path)

    if args.get("serial"):
        device_props = api.get_device(args["serial"])
        props_json = device_props.json()
        args["ws"] = props_json.get("device").get("display").get("url")
        log.debug("Got websocket url {0} by device serial {1} from stf API".format(args["ws"], args["serial"]))
    else:
        raise(Exception("Neither device serial nor websocket url provided. Unable to determine device to screencast"))

    address = args["ws"].split("ws://")[-1]
    return address


def parse_args():
    parser = argparse.ArgumentParser(
        description="Utility for saving screenshots "
                    "from devices with openstf minicap"
    )
    generic_display_id_group = parser.add_mutually_exclusive_group(required=True)
    generic_display_id_group.add_argument(
        "-s", "--serial", help="Device serial"
    )
    generic_display_id_group.add_argument(
        "-w", "--ws", help="WebSocket URL"
    )
    generic_display_id_group.add_argument(
        "-a", "--adb-connect-url", help="URL used to remote debug with adb connect, e.g. <host>:<port>"
    )
    parser.add_argument(
        "-d", "--dir", help="Directory for images", default="images"
    )
    parser.add_argument(
        "-r", "--resolution", help="Resolution of images"
    )
    parser.add_argument(
        "-l", "--log-level", help="Log level"
    )
    parser.add_argument(
        "-k", "--keep-old-data", help="Do not clean old data from directory", action="store_true", default=False
    )
    parser.add_argument(
        "-c", "--config", help="Path to config file"
    )

    args = vars(parser.parse_args())
    return args


def start_recorder(args, oauth_token=None, host=None):
    if args.get("config"):
        config.add_config_file(args.get("config"))
    else:
        config.add_config_file("stf-utils.ini")

    if oauth_token is None:
        oauth_token = config.main.get("oauth_token")
    if host is None:
        host = config.main.get("host")

    if args.get("log_level"):
        log.info("Changed log level to {0}".format(args["log_level"].upper()))
        log.setLevel(args["log_level"].upper())

    api = SmartphoneTestingFarmAPI(
        host=host,
        common_api_path="/api/v1",
        oauth_token=oauth_token
    )

    ws_url = get_ws_url(api, args)
    wsfactory(
        directory=args.get("dir", "images"),
        resolution=args.get("resolution", None),
        address=ws_url,
        keep_old_data=args.get("keep_old_data", False)
    )


def run():
    args = parse_args()
    start_recorder(args)

if __name__ == "__main__":
    run()
