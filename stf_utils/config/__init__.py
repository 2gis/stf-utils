from six import moves
import os

config = moves.configparser.ConfigParser()
config_dir = os.path.dirname(os.path.abspath(__file__))
config.read("{0}/config.ini".format(config_dir))

