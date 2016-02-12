import os
import sys
import signal
import logging
import requests
import subprocess

from json import dumps, loads
from time import sleep


log = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(message)s'
)

API_URL = "http://stf.auto.ostack.test/api/v1"
OAUTH_TOKEN = "e1cb89b5108348dd9251b7848948084809dad3a2e1084d8ebc4bf6663381d56e"


def exit_gracefully(signum, frame):
    disconnect_all(API_URL, OAUTH_TOKEN)
    delete_all(API_URL, OAUTH_TOKEN)
    sys.exit(0)


def get_available(api_url, oauth_token):
    url = "{0}/devices".format(api_url)
    resp = requests.get(
        url,
        headers={
            "Authorization": "Bearer {0}".format(oauth_token)
        }
    )
    device_list = []
    for device in resp.json().get("devices"):
        if device.get("present") and not device.get("owner"):
            device_list.append(device)
    if resp.status_code == 200:
        return device_list
    else:
        log.error(resp)
        raise requests.RequestException


def get_owned(api_url, oauth_token):
    url = "{0}/user/devices".format(api_url)
    resp = requests.get(
        url,
        headers={
            "Authorization": "Bearer {0}".format(oauth_token)
        }
    )
    if resp.status_code == 200:
        return resp.json().get("devices")
    else:
        log.error(resp)
        raise requests.RequestException


def add_all(api_url, oauth_token):
    device_list = get_available(api_url, oauth_token)
    url = "{0}/user/devices".format(api_url)
    for device in device_list:
        device_serial = device.get("serial")
        log.info("Adding device {0}".format(device_serial))
        resp = requests.post(
            url,
            data=dumps({
                "serial": "{0}".format(device_serial)
            }).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Authorization": "Bearer {0}".format(oauth_token)
            }
        )
        if resp.status_code == 200:
            log.info(loads(resp.text).get("description"))
        else:
            log.error(resp.text)
            raise requests.RequestException


def delete_all(api_url, oauth_token):
    device_list = get_owned(api_url, oauth_token)
    for device in device_list:
        device_serial = device.get("serial")
        url = "{0}/user/devices/{1}".format(api_url, device_serial)
        log.info("Deleting device {0}".format(device_serial))
        resp = requests.delete(
            url,
            headers={
                "Content-Type": "application/json",
                "Authorization": "Bearer {0}".format(oauth_token)
            }
        )
        if resp.status_code == 200:
            log.info(loads(resp.text).get("description"))
        else:
            log.error(resp.text)
            raise requests.RequestException


def connect_all(api_url, oauth_token):
    device_list = get_owned(api_url, oauth_token)
    for device in device_list:
        device_serial = device.get("serial")
        url = "{0}/user/devices/{1}/remoteConnect".format(api_url, device_serial)
        log.info("Connecting device {0}".format(device_serial))
        resp = requests.post(
            url,
            headers={
                "Content-Type": "application/json",
                "Authorization": "Bearer {0}".format(oauth_token)
            }
        )
        if resp.status_code == 200:
            adb_connect_url = resp.json().get("remoteConnectUrl")
            command = ["adb", "connect", adb_connect_url]
            subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env=os.environ.copy()
            )
        else:
            log.error(resp.text)
            raise requests.RequestException


def disconnect_all(api_url, oauth_token):
    device_list = get_owned(api_url, oauth_token)
    for device in device_list:
        device_serial = device.get("serial")
        url = "{0}/user/devices/{1}/remoteConnect".format(api_url, device_serial)
        log.info("Disconnecting device {0}".format(device_serial))
        resp = requests.delete(
            url,
            headers={
                "Content-Type": "application/json",
                "Authorization": "Bearer {0}".format(oauth_token)
            }
        )
        if resp.status_code == 200:
            log.info(loads(resp.text).get("description"))
        else:
            log.error(resp.text)
            raise requests.RequestException


if __name__ == '__main__':
    signal.signal(signal.SIGINT, exit_gracefully)
    signal.signal(signal.SIGTERM, exit_gracefully)
    add_all(API_URL, OAUTH_TOKEN)
    connect_all(API_URL, OAUTH_TOKEN)
    while True:
        sleep(100)
