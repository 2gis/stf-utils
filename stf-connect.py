from json import dumps, loads
import logging
import requests

log = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

API_URL = "http://stf.auto.ostack.test/api/v1"
OAUTH_TOKEN = "e1cb89b5108348dd9251b7848948084809dad3a2e1084d8ebc4bf6663381d56e"

devices_path = "/devices"
user_devices_path = "/user/devices"
add_device_path = "/user/"


def get_available_devices(api_url, oauth_token):
    url = "{0}{1}".format(api_url, devices_path)
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
    return device_list


def get_owned_devices(api_url, oauth_token):
    url = "{0}{1}".format(api_url, user_devices_path)
    resp = requests.get(
        url,
        headers={
            "Authorization": "Bearer {0}".format(oauth_token)
        }
    )
    return resp.json().get("devices")


def add_all_devices(api_url, oauth_token):
    device_list = get_available_devices(api_url, oauth_token)
    url = "{0}{1}".format(api_url, user_devices_path)
    for device in device_list:
        device_serial = device.get("serial")
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
        log.info(loads(resp.text).get("description"))


def delete_all_devices(api_url, oauth_token):
    device_list = get_owned_devices(api_url, oauth_token)
    for device in device_list:
        device_serial = device.get("serial")
        url = "{0}{1}/{2}".format(api_url, user_devices_path, device_serial)
        resp = requests.delete(
            url,
            headers={
                "Content-Type": "application/json",
                "Authorization": "Bearer {0}".format(oauth_token)
            }
        )
        log.info(loads(resp.text).get("description"))

add_all_devices(API_URL, OAUTH_TOKEN)
delete_all_devices(API_URL, OAUTH_TOKEN)