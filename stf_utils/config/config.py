try:
    import ConfigParser
except ImportError:
    import configparser as ConfigParser
import os
import ast


class Config(object):
    main = {
        "host": "",
        "oauth_token": "",
        "device_spec": "",
        "devices_file_path": "",
        "shutdown_emulator_on_disconnect": "",
    }

    def __init__(self, *args):
        """
        :type args: tuple of str
        """
        for ini_path in args:
            self.add_config_file(ini_path)

    def add_config_file(self, path_to_file):
        """
        :type path_to_file: str
        """
        parser = ConfigParser.SafeConfigParser()
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


def initialize_config_file(file=""):
    config = Config(
        os.path.abspath(os.path.dirname(__file__)) + "/stf-utils.ini",
    )
    config.add_config_file(file)
    return config
