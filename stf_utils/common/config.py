from six import moves


def initialize_config_file(file):
    config = moves.configparser.SafeConfigParser()
    config.read(file)
    return config
