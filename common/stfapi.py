import re
import six
import json
import requests

re_path_template = re.compile('{\w+}')


def bind_method(**config):
    class SmartphoneTestingFarmAPIMethod(object):
        path = config['path']
        method = config.get('method', 'GET')
        accepts_parameters = config.get("accepts_parameters", [])
        headers = config.get("headers")

        def __init__(self, api, *args, **kwargs):
            self.api = api
            self.parameters = {}
            self._build_parameters(args, kwargs)
            self._build_path()

        def _build_parameters(self, args, kwargs):
            for index, value in enumerate(args):
                if value is None:
                    continue
                try:
                    self.parameters[self.accepts_parameters[index]] = value
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

        def _prepare_request(self):
            method = self.method
            url = "{0}{1}".format(self.api.api_url, self.path)
            headers = {
                "Authorization": "Bearer {0}".format(self.api.oauth_token)
            }
            if self.headers is not None:
                headers.update(self.headers)
            data = json.dumps(self.parameters)
            return method, url, headers, data

        def execute(self):
            method, url, headers, data = self._prepare_request()
            response = requests.request(
                method=method,
                url=url,
                headers=headers,
                data=data
            )
            return response

    def _call(api, *args, **kwargs):
        method = SmartphoneTestingFarmAPIMethod(api, *args, **kwargs)
        return method.execute()

    return _call


class SmartphoneTestingFarmAPI(object):
    """
    Bindings for OpenSTF API:
    https://github.com/openstf/stf/blob/2.0.0/doc/API.md
    """
    def __init__(self, host, common_api_path, oauth_token):
        self.host = host
        self.common_api_path = common_api_path
        self.oauth_token = oauth_token
        self.api_url = "{0}{1}".format(self.host, self.common_api_path)

    get_all_devices = bind_method(
        path="/devices"
    )

    get_device = bind_method(
        path="/devices/{serial}"
    )

    get_user_info = bind_method(
        path="/user"
    )

    get_my_devices = bind_method(
        path="/user/devices"
    )

    add_device = bind_method(
        method="post",
        path="/user/devices",
        headers={
            "Content-Type": "application/json"
        },
        accepts_parameters=["serial"]
    )

    delete_device = bind_method(
        method="delete",
        path="/user/devices/{serial}"
    )

    remote_connect = bind_method(
        method="post",
        path="/user/devices/{serial}/remoteConnect",
        headers={
            "Content-Type": "application/json"
        }
    )

    remote_disconnect = bind_method(
        method="delete",
        path="/user/devices/{serial}/remoteConnect",
        accepts_parameters=["serial"]
    )
