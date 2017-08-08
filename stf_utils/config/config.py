# -*- coding: utf-8 -*-

import os
import ast

try:
    import ConfigParser
except ImportError:
    import configparser as ConfigParser


class Config(object):
    main = {
        "host": "",
        "oauth_token": "",
        "device_spec": "",
        "devices_file_path": "",
        "shutdown_emulator_on_disconnect": "",
    }

    def __init__(self, config_path):
        """
        :type path: str
        """
        if not os.path.exists(config_path):
            raise FileNotFoundError(config_path)

        self.add_config_file(config_path)

    def add_config_file(self, path_to_file):
        """
        :type path_to_file: str
        """
        parser = ConfigParser.ConfigParser()
        parser.optionxform = str
        parser.read(path_to_file)
        sections = parser.sections()
        for section in sections:
            params = parser.items(section)
            section = section.lower()
            d = {}
            for param in params:
                key, value = param
                try:
                    value = ast.literal_eval(value)
                except (ValueError, SyntaxError):
                    pass
                d[key] = value
            if hasattr(self, section):
                getattr(self, section).update(d)
            else:
                setattr(self, section, d)

