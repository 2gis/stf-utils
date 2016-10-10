import argparse
import asyncio
import json
import logging
import signal

import functools
import os
from autobahn.asyncio.websocket import WebSocketClientFactory
from stf_utils.common.stfapi import api
from stf_utils.config import config
from stf_utils.stf_record.protocol import STFRecordProtocol

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("stf-record")


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


def get_ws_url(args):
    if args["adb_connect_url"]:
        connected_devices_file_path = "{0}/{1}".format(
            config.get("main", "devices_file_dir"),
            config.get("main", "devices_file_name")
        )
        args["serial"] = _get_device_serial(args["adb_connect_url"], connected_devices_file_path)

    if args["serial"]:
        device_props = api.get_device(args["serial"])
        props_json = device_props.json()
        args["ws"] = props_json.get("device").get("display").get("url")
        log.debug("Got websocket url {0} by device serial {1} from stf API".format(args["ws"], args["serial"]))

    address = args["ws"].split("ws://")[-1]
    return address


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


def run():
    parser = argparse.ArgumentParser(
        description="Utility for saving screenshots "
                    "from devices with openstf minicap"
    )
    generic_display_id_group = parser.add_mutually_exclusive_group(required=True)
    generic_display_id_group.add_argument(
        "-serial", help="Device serial"
    )
    generic_display_id_group.add_argument(
        "-ws", help="WebSocket URL"
    )
    generic_display_id_group.add_argument(
        "-adb-connect-url", help="URL used to remote debug with adb connect, e.g. <host>:<port>"
    )
    parser.add_argument(
        "-dir", help="Directory for images", default="images"
    )
    parser.add_argument(
        "-resolution", help="Resolution of images"
    )
    parser.add_argument(
        "-log-level", help="Log level"
    )
    parser.add_argument(
        "-no-clean-old-data", help="Do not clean old data from directory", action="store_true", default=False
    )

    args = vars(parser.parse_args())

    if args["log_level"]:
        log.info("Changed log level to {0}".format(args["log_level"].upper()))
        log.setLevel(args["log_level"].upper())

    wsfactory(
        directory=args["dir"],
        resolution=args["resolution"],
        address=get_ws_url(args),
        keep_old_data=args["no_clean_old_data"]
    )

if __name__ == "__main__":
    run()
