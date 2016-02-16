import re
import six
import json
import requests

re_path_template = re.compile('{\w+}')


class SmartphoneTestingFarmAPI(object):
    def __init__(self, host, common_api_path, oauth_token):
        self.host = host
        self.common_api_path = common_api_path,
        self.oauth_token = oauth_token,
        self.api_url = self.host + self.common_api_path

    def add_devices(self, device_spec):
        pass

    def connect_to_mine(self):
        pass

    def close_all(self):
        pass


def bind_method(**config):
    class SmartphoneTestingFarmAPIMethod(object):
        path = config['path']
        method = config.get('method', 'GET')
        response_type = config.get("response_type", "list")
        objectify_response = config.get("objectify_response", True)
        exclude_format = config.get('exclude_format', False)

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
                    self.parameters[index] = value
                except IndexError:
                    raise Exception("mazafaka")

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
    #
    #     def _do_api_request(self, url, method="GET", body=None, headers=None):
    #         headers = headers or {}
    #         if self.signature and self.api.client_ips != None and self.api.client_secret != None:
    #             secret = self.api.client_secret
    #             ips = self.api.client_ips
    #             signature = hmac.new(secret, ips, sha256).hexdigest()
    #             headers['X-Insta-Forwarded-For'] = '|'.join([ips, signature])
    #
    #         response, content = OAuth2Request(self.api).make_request(url, method=method, body=body, headers=headers)
    #         if response['status'] == '503' or response['status'] == '429':
    #             raise InstagramAPIError(response['status'], "Rate limited", "Your client is making too many request per second")
    #         try:
    #             content_obj = simplejson.loads(content)
    #         except ValueError:
    #             raise InstagramClientError('Unable to parse response, not valid JSON.', status_code=response['status'])
    #         # Handle OAuthRateLimitExceeded from Instagram's Nginx which uses different format to documented api responses
    #         if 'meta' not in content_obj:
    #             if content_obj.get('code') == 420 or content_obj.get('code') == 429:
    #                 error_message = content_obj.get('error_message') or "Your client is making too many request per second"
    #                 raise InstagramAPIError(content_obj.get('code'), "Rate limited", error_message)
    #             raise InstagramAPIError(content_obj.get('code'), content_obj.get('error_type'), content_obj.get('error_message'))
    #         api_responses = []
    #         status_code = content_obj['meta']['code']
    #         self.api.x_ratelimit_remaining = response.get("x-ratelimit-remaining",None)
    #         self.api.x_ratelimit = response.get("x-ratelimit-limit",None)
    #         if status_code == 200:
    #             if not self.objectify_response:
    #                 return content_obj, None
    #
    #             if self.response_type == 'list':
    #                 for entry in content_obj['data']:
    #                     if self.return_json:
    #                         api_responses.append(entry)
    #                     else:
    #                         obj = self.root_class.object_from_dictionary(entry)
    #                         api_responses.append(obj)
    #             elif self.response_type == 'entry':
    #                 data = content_obj['data']
    #                 if self.return_json:
    #                     api_responses = data
    #                 else:
    #                     api_responses = self.root_class.object_from_dictionary(data)
    #             elif self.response_type == 'empty':
    #                 pass
    #             return api_responses, self._build_pagination_info(content_obj)
    #         else:
    #             raise InstagramAPIError(status_code, content_obj['meta']['error_type'], content_obj['meta']['error_message'])
    #
    #     def execute(self):
    #         url, method, body, headers = OAuth2Request(self.api).prepare_request(self.method,
    #                                                                              self.path,
    #                                                                              self.parameters,
    #                                                                              include_secret=self.include_secret)
    #         if self.with_next_url:
    #             return self._get_with_next_url(self.with_next_url, method, body, headers)
    #         if self.as_generator:
    #             return self._paginator_with_url(url, method, body, headers)
    #         else:
    #             content, next = self._do_api_request(url, method, body, headers)
    #         if self.paginates:
    #             return content, next
    #         else:
    #             return content
    #
    # def _call(api, *args, **kwargs):
    #     method = InstagramAPIMethod(api, *args, **kwargs)
    #     return method.execute()
    #
    # return _call
