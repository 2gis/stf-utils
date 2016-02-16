import re
import six
import json
import requests

re_path_template = re.compile('{\w+}')


def bind_method(**config):
    class SmartphoneTestingFarmAPIMethod(object):
        path = config['path']
        method = config.get('method', 'GET')
        response_type = config.get("response_type", "list")
        headers = config.get("headers")

        def __init__(self, api, *args, **kwargs):
            self.api = api
            self.parameters = {}
            self._build_parameters(args, kwargs)
            print("args: {0}, kwargs: {1}".format(args, kwargs))
            print("parameters: {0}".format(self.parameters))
            self._build_path()

        def _build_parameters(self, args, kwargs):
            for index, value in enumerate(args):
                if value is None:
                    continue
                try:
                    self.parameters[index] = value
                except IndexError:
                    raise Exception("Too many arguments supplied")

            for key, value in six.iteritems(kwargs):
                if value is None:
                    continue
                if key in self.parameters:
                    raise Exception("Parameter %s already supplied" % key)
                self.parameters[key] = value

        def _build_path(self):
            for variable in re_path_template.findall(self.path):
                name = variable.strip('{}')
                try:
                    value = self.parameters[name]
                except KeyError:
                    raise Exception('No parameter value found for path variable: %s' % name)
                del self.parameters[name]
                self.path = self.path.replace(variable, value)

        def _prepare_headers(self):
            auth_header = {
                "Authorization": "Bearer {0}".format(self.api.oauth_token)
            }
            if self.headers is not None:
                auth_header.update(self.headers)
            return auth_header

        def execute(self):
            # headers, data = self._prepare_request()
            print("exec. params: {0}".format(self.parameters))
            print("exec. headers: {0}".format(self._prepare_headers()))
            print("url: {0}".format(self.api.api_url + self.path))
            print("method: {0}".format(self.method))
            response = requests.request(method=self.method, url=self.api.api_url + self.path, headers=self._prepare_headers(), data=json.dumps(self.parameters).encode("utf-8"))
            print(response.status_code)

    def _call(api, *args, **kwargs):
        method = SmartphoneTestingFarmAPIMethod(api, *args, **kwargs)
        return method.execute()

    return _call


class SmartphoneTestingFarmAPI(object):
    def __init__(self, host, common_api_path, oauth_token):
        self.host = host
        self.common_api_path = common_api_path
        self.oauth_token = oauth_token
        self.api_url = "{0}{1}".format(self.host, self.common_api_path)
        self.devices = [
            {
                "serial": "emulator-5554"
            }
        ]

    def add_devices(self, device_spec):
        for device in self.devices:
            self.add_device(serial=device.get("serial"))

    def connect_to_mine(self):
        pass

    def close_all(self):
        for device in self.devices:
            self.delete_device(serial=device.get("serial"))

    delete_device = bind_method(
        method="delete",
        path="/user/devices/{serial}"
    )

    add_device = bind_method(
        method="post",
        path="/user/devices",
        headers={
            "Content-Type": "application/json"
        }
    )