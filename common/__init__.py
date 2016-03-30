from six import moves
import os

config = moves.configparser.ConfigParser()
root_dir = os.path.dirname(os.path.abspath(__file__).replace("/common", ""))
config.read("{0}/config.ini".format(root_dir))