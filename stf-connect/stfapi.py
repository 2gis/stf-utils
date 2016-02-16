import json
import requests


class SmartphoneTestingFarmApi(object):
    def __init__(self, host, common_api_path, oauth_token, *args, **kwargs):
        self.host = host
        self.common_api_path = common_api_path,
        self.oauth_token = oauth_token,
        self.api_url = self.host + self.common_api_path

    def add_devices(self, device_spec):
        pass

    def connect_to_mine(self):
        pass
